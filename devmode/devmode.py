#!/usr/bin/env python3
import ctypes
import importlib.util
import inspect
import json
import os
import fcntl
import re
import select
import signal
import struct
import sys
import time

PTRACE_PEEKTEXT = 1
PTRACE_POKETEXT = 4
PTRACE_PEEKUSR = 3
PTRACE_POKEUSR = 6
PTRACE_ATTACH = 16
PTRACE_DETACH = 17
PTRACE_CONT = 7
PTRACE_SINGLESTEP = 9
PTRACE_GETREGS = 12
PTRACE_SETREGS = 13
PTRACE_GETREGSET = 0x4204
PTRACE_SETREGSET = 0x4205
NT_PRFPREG = 0x400
PTRACE_SETOPTIONS = 0x4200
PTRACE_GETEVENTMSG = 0x4201
PTRACE_EVENT_CLONE = 3
PTRACE_O_TRACESYSGOOD = 0x00000001
PTRACE_O_TRACECLONE = 0x00000008

ARM_BKPT = 0xE1200070
THUMB_BKPT = 0xBE00
T_BIT = 0x20
WAIT_ALL = 0x40000000
REG_PC_OFFSET = 15 * ctypes.sizeof(ctypes.c_long)
DEBUG = True
STDIN_NONBLOCK = False
WATCH_LOG = False

libc = ctypes.CDLL(None, use_errno=True)
ptrace = libc.ptrace
ptrace.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
ptrace.restype = ctypes.c_long

libc.waitpid.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_int]
libc.waitpid.restype = ctypes.c_int
libc.process_vm_readv.argtypes = [
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_ulong,
    ctypes.c_void_p,
    ctypes.c_ulong,
    ctypes.c_ulong,
]
libc.process_vm_readv.restype = ctypes.c_long


class ArmRegs(ctypes.Structure):
    _fields_ = [("uregs", ctypes.c_ulong * 18)]


class IOVec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]


class VFPRegs(ctypes.Structure):
    _fields_ = [
        ("fpregs", ctypes.c_ulonglong * 32),
        ("fpscr", ctypes.c_uint),
        ("fpexc", ctypes.c_uint),
    ]


class Breakpoint:
    def __init__(self, name, addr, meta, event, kind):
        self.name = name
        self.addr = addr
        self.meta = meta
        self.event = event
        self.kind = kind
        self.is_thumb = False
        self.orig_word = None
        self.orig_halfword = None

    def label(self):
        return f"{self.name}@0x{self.addr:x}"


class Watch:
    def __init__(self, name, base, index, offset, kind, size, abs_addr, event):
        self.name = name
        self.base = base
        self.index = index
        self.offset = offset
        self.kind = kind
        self.size = size
        self.abs_addr = abs_addr
        self.event = event
        self.last = None
        self.seen = False
        self.base_seen = False
        self.fail_count = 0
        self.last_fail = 0.0

    def label(self):
        return f"{self.name}[{self.index}]"


class WatchBlock:
    def __init__(self, name, base, index, size, event, kind):
        self.name = name
        self.base = base
        self.index = index
        self.size = size
        self.event = event
        self.kind = kind
        self.last = None
        self.base_seen = False
        self.fail_count = 0
        self.last_fail = 0.0

    def label(self):
        return f"{self.name}[{self.index}]"


def ts():
    return f"{time.monotonic():.6f}"


def out(msg):
    line = f"{ts()} {msg}"
    try:
        print(line, flush=True)
        return
    except Exception:
        pass
    try:
        sys.stderr.write(line + "\n")
        sys.stderr.flush()
    except Exception:
        pass


def dbg(msg):
    if DEBUG:
        out(msg)


def watch_log(msg):
    if WATCH_LOG:
        out(msg)


def color(text, code):
    return f"\033[{code}m{text}\033[0m"


def parse_address(val):
    if val is None:
        return None
    if isinstance(val, int):
        return int(val)
    sval = str(val).strip()
    if not sval:
        return None
    try:
        if sval.lower().startswith("0x"):
            return int(sval, 16)
        return int(sval, 0)
    except ValueError:
        return None


def parse_float(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    sval = str(val).strip()
    if not sval:
        return None
    try:
        return float(sval)
    except ValueError:
        return None


class ValueCache:
    def __init__(self):
        self.values = {}
        self.kinds = {}

    def set(self, key, value, kind=None):
        self.values[key] = value
        if kind is not None:
            self.kinds[key] = kind

    def get(self, key):
        return self.values.get(key)


class EventBus:
    def __init__(self):
        self._callbacks = {}

    def on(self, event_name, fn):
        callbacks = self._callbacks.get(event_name)
        if callbacks is None:
            callbacks = []
            self._callbacks[event_name] = callbacks
        callbacks.append(fn)
        return (event_name, len(callbacks) - 1)

    def off(self, handle):
        if not handle or len(handle) != 2:
            return False
        event_name, idx = handle
        callbacks = self._callbacks.get(event_name)
        if not callbacks or idx >= len(callbacks):
            return False
        callbacks[idx] = None
        return True

    def emit(self, event_name, payload):
        callbacks = self._callbacks.get(event_name)
        if not callbacks:
            return
        for fn in callbacks:
            if fn is not None:
                fn(payload)


def call_plugin(fn, ctx, payload):
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        fn(ctx)
        return
    params = list(sig.parameters.values())
    for param in params:
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            fn(ctx, payload)
            return
    if len(params) >= 2:
        fn(ctx, payload)
    else:
        fn(ctx)


class PluginContext:
    def __init__(self, bus, name, cache, events, event_keys, keys, cmd_queue):
        self._bus = bus
        self.name = name
        self._cache = cache
        self._events = events
        self._event_keys = event_keys
        self._keys = keys
        self._cmd_queue = cmd_queue
        self._event_name = None
        self._event_payload = None

    def on(self, event_name, fn):
        def handler(payload):
            self._event_name = event_name
            self._event_payload = payload
            call_plugin(fn, self, payload)

        return self._bus.on(event_name, handler)

    def off(self, handle):
        return self._bus.off(handle)

    def log(self, msg):
        out(f"{self.name} {msg}")

    def __getitem__(self, key):
        return self._cache.get(key)

    def keys(self):
        return list(self._keys)

    def events(self):
        return list(self._events)

    def event_keys(self, event_name):
        return list(self._event_keys.get(event_name, []))

    def queue_cmd(self, cmd):
        if not cmd:
            return False
        text = str(cmd).strip()
        if not text or not text.startswith("/") or len(text) == 1:
            return False
        self._cmd_queue.append(text)
        return True

    @property
    def event(self):
        return self._event_name

    @property
    def payload(self):
        return self._event_payload


class PluginManager:
    def __init__(self, bus, base_dir, cache, events, event_keys, keys, cmd_queue):
        self.bus = bus
        self.base_dir = base_dir
        self.cache = cache
        self.events = events
        self.event_keys = event_keys
        self.keys = keys
        self.cmd_queue = cmd_queue
        self.plugins = {}
        self.contexts = {}

    def load_all(self):
        pattern = re.compile(r"plugin-.*\.py$")
        try:
            filenames = sorted(os.listdir(self.base_dir))
        except OSError as exc:
            out(f"plugin scan failed: {exc}")
            return
        for filename in filenames:
            if not pattern.match(filename):
                continue
            path = os.path.join(self.base_dir, filename)
            module_name = os.path.splitext(filename)[0].replace("-", "_")
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                out(f"plugin load failed: {filename}")
                continue
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as exc:
                out(f"plugin import failed: {filename} err={exc}")
                continue
            self.plugins[filename] = mod
            ctx = PluginContext(
                self.bus,
                filename,
                self.cache,
                self.events,
                self.event_keys,
                self.keys,
                self.cmd_queue,
            )
            self.contexts[filename] = ctx
            load_fn = getattr(mod, "plugin_load", None)
            if callable(load_fn):
                try:
                    load_fn(ctx)
                except Exception as exc:
                    out(f"plugin_load failed: {filename} err={exc}")

    def unload_all(self):
        for filename, mod in self.plugins.items():
            unload_fn = getattr(mod, "plugin_unload", None)
            if not callable(unload_fn):
                continue
            ctx = self.contexts.get(filename)
            try:
                unload_fn(ctx)
            except Exception as exc:
                out(f"plugin_unload failed: {filename} err={exc}")


def ptrace_checked(request, pid, addr, data):
    addr_p = ctypes.c_void_p(addr if addr is not None else 0)
    data_p = ctypes.c_void_p(data if data is not None else 0)
    ctypes.set_errno(0)
    res = ptrace(request, pid, addr_p, data_p)
    err = ctypes.get_errno()
    return int(res), int(err)


def wait_for(pid, flags=0):
    status = ctypes.c_int()
    ctypes.set_errno(0)
    r = libc.waitpid(pid, ctypes.byref(status), flags)
    err = ctypes.get_errno()
    if err:
        out(f"waitpid error pid={pid} errno={err}")
    return int(r), int(status.value)


def read_regs(tid):
    regs = ArmRegs()
    res = ptrace(PTRACE_GETREGS, tid, None, ctypes.byref(regs))
    err = ctypes.get_errno()
    if err or res != 0:
        return None
    return regs


def write_regs(tid, regs):
    res = ptrace(PTRACE_SETREGS, tid, None, ctypes.byref(regs))
    err = ctypes.get_errno()
    return err == 0 and res == 0


def read_pc(tid):
    regs = read_regs(tid)
    if regs is not None:
        return int(regs.uregs[15]) & 0xFFFFFFFF
    res, err = ptrace_checked(PTRACE_PEEKUSR, tid, REG_PC_OFFSET, 0)
    if err:
        return None
    return res & 0xFFFFFFFF


def read_word(tid, addr):
    res, err = ptrace_checked(PTRACE_PEEKTEXT, tid, addr, None)
    if err and res == -1:
        return None
    return res & 0xFFFFFFFF


def write_word(tid, addr, value):
    res, err = ptrace_checked(PTRACE_POKETEXT, tid, addr, value)
    return err == 0 and res == 0


def read_halfword(tid, addr):
    word_addr = addr & ~3
    word = read_word(tid, word_addr)
    if word is None:
        return None
    shift = 16 if (addr & 2) else 0
    return (word >> shift) & 0xFFFF


def write_halfword(tid, addr, value):
    word_addr = addr & ~3
    word = read_word(tid, word_addr)
    if word is None:
        return False
    shift = 16 if (addr & 2) else 0
    masked = word & ~(0xFFFF << shift)
    patched = masked | ((value & 0xFFFF) << shift)
    return write_word(tid, word_addr, patched)


def read_mem(pid, addr, size):
    buf = (ctypes.c_char * size)()
    local = IOVec(ctypes.cast(buf, ctypes.c_void_p), size)
    remote = IOVec(ctypes.c_void_p(addr), size)
    ctypes.set_errno(0)
    res = libc.process_vm_readv(
        pid,
        ctypes.byref(local),
        1,
        ctypes.byref(remote),
        1,
        0,
    )
    if res != size:
        return None, ctypes.get_errno()
    return bytes(buf), 0


def read_mem_any(pid, mem_fd, addr, size):
    data, err = read_mem(pid, addr, size)
    if data is not None and len(data) == size:
        return data, 0
    if mem_fd is None:
        return None, err
    try:
        data = os.pread(mem_fd, size, addr)
    except OSError as exc:
        return None, exc.errno or err
    if len(data) != size:
        return None, err
    return data, 0


def read_f64_mem(pid, addr):
    data, err = read_mem(pid, addr, 8)
    if data is None or len(data) != 8:
        return None, err
    return struct.unpack("<d", data)[0], 0


def read_f64_any(pid, mem_fd, addr):
    data, err = read_mem_any(pid, mem_fd, addr, 8)
    if data is None or len(data) != 8:
        return None, err
    return struct.unpack("<d", data)[0], 0


def read_f32_any(pid, mem_fd, addr):
    data, err = read_mem_any(pid, mem_fd, addr, 4)
    if data is None or len(data) != 4:
        return None, err
    return struct.unpack("<f", data)[0], 0


def read_u32_mem(pid, addr):
    data, err = read_mem(pid, addr, 4)
    if data is None or len(data) != 4:
        return None, err
    return int.from_bytes(data, byteorder="little", signed=False), 0


def read_u32_any(pid, mem_fd, addr):
    data, err = read_mem_any(pid, mem_fd, addr, 4)
    if data is None or len(data) != 4:
        return None, err
    return int.from_bytes(data, byteorder="little", signed=False), 0


def read_u16_mem(pid, addr):
    data, err = read_mem(pid, addr, 2)
    if data is None or len(data) != 2:
        return None, err
    return int.from_bytes(data, byteorder="little", signed=False), 0


def read_u8_mem(pid, addr):
    data, err = read_mem(pid, addr, 1)
    if data is None or len(data) != 1:
        return None, err
    return data[0], 0


def to_s32(val):
    if val & 0x80000000:
        return val - 0x100000000
    return val


def mode_is_thumb(meta, addr):
    mode = meta.get("mode")
    if isinstance(mode, str):
        if mode.lower() == "thumb":
            return True
        if mode.lower() == "arm":
            return False
    if meta.get("thumb") is True:
        return True
    return bool(addr & 1)


def load_breakpoints(path):
    with open(path, "r") as f:
        data = json.load(f)
    bps = []
    watches = []
    blocks = []
    for entry in data:
        if entry.get("watch_block") is True:
            name = entry.get("name", "watch_block")
            event = entry.get("event") or name
            kind = entry.get("kind") or "block"
            base = parse_address(entry.get("base"))
            index = entry.get("index", 0)
            size = int(entry.get("size") or 0)
            if base is None or size <= 0:
                continue
            blocks.append(WatchBlock(name, base, int(index), size, event, kind))
            continue
        if entry.get("watch") is True:
            name = entry.get("name", "watch")
            event = entry.get("event") or name
            base = parse_address(entry.get("base"))
            index = entry.get("index", 0)
            offset = parse_address(entry.get("offset"))
            kind = (entry.get("kind") or "s32").lower()
            size = int(entry.get("size") or 4)
            abs_addr = entry.get("abs") is True
            if base is None or offset is None:
                continue
            watches.append(Watch(name, base, int(index), offset, kind, size, abs_addr, event))
            continue
        name = entry.get("name", "unnamed")
        event = entry.get("event") or name
        kind = entry.get("kind") or "breakpoint"
        addr_val = parse_address(entry.get("address"))
        if not addr_val:
            continue
        meta = dict(entry)
        bps.append(Breakpoint(name, addr_val, meta, event, kind))
    return bps, watches, blocks


def pick_update_breakpoints(bps):
    picked = []
    for bp in bps:
        if bp.meta.get("disabled") is True:
            continue
        if bp.meta.get("cmd_hook") is True:
            picked.append(bp)
            continue
        name = (bp.name or "").lower()
        anchor = (bp.meta.get("anchor_string") or "").lower()
        desc = (bp.meta.get("description") or "").lower()
        if name.startswith("ota_") or name.startswith("axis_") or name.startswith("stepper_"):
            picked.append(bp)
            continue
        if "do7" in anchor or "do7" in desc:
            picked.append(bp)
    return picked if picked else bps


def list_tids(pid):
    tids = []
    tasks_dir = f"/proc/{pid}/task"
    try:
        for entry in os.scandir(tasks_dir):
            if entry.name.isdigit():
                tids.append(int(entry.name))
    except FileNotFoundError:
        return []
    return sorted(tids)


def set_ptrace_options(tid):
    opts = PTRACE_O_TRACESYSGOOD | PTRACE_O_TRACECLONE
    res, err = ptrace_checked(PTRACE_SETOPTIONS, tid, None, opts)
    return err == 0 and res == 0


def get_event_msg(tid):
    data = ctypes.c_ulong()
    res = ptrace(PTRACE_GETEVENTMSG, tid, None, ctypes.byref(data))
    err = ctypes.get_errno()
    if err or res != 0:
        return None
    return int(data.value)


def install_breakpoint(tid, bp):
    if bp.addr & 1:
        bp.addr -= 1
    bp.is_thumb = mode_is_thumb(bp.meta, bp.addr)
    if bp.is_thumb:
        orig = read_halfword(tid, bp.addr)
        if orig is None:
            return False
        bp.orig_halfword = orig
        ok = write_halfword(tid, bp.addr, THUMB_BKPT)
        readback = read_halfword(tid, bp.addr)
        dbg(
            "INSTALL thumb addr=0x%x orig=0x%04x write=0x%04x read=0x%04x ok=%s"
            % (
                bp.addr,
                orig,
                THUMB_BKPT,
                0 if readback is None else readback,
                "True" if ok else "False",
            )
        )
        return ok
    orig = read_word(tid, bp.addr)
    if orig is None:
        return False
    bp.orig_word = orig
    ok = write_word(tid, bp.addr, ARM_BKPT)
    readback = read_word(tid, bp.addr)
    dbg(
        "INSTALL arm addr=0x%x orig=0x%08x write=0x%08x read=0x%08x ok=%s"
        % (
            bp.addr,
            orig,
            ARM_BKPT,
            0 if readback is None else readback,
            "True" if ok else "False",
        )
    )
    return ok


def restore_breakpoint(tid, bp):
    if bp.is_thumb:
        if bp.orig_halfword is None:
            return False
        return write_halfword(tid, bp.addr, bp.orig_halfword)
    if bp.orig_word is None:
        return False
    return write_word(tid, bp.addr, bp.orig_word)


def rearm_breakpoint(tid, bp):
    if bp.is_thumb:
        return write_halfword(tid, bp.addr, THUMB_BKPT)
    return write_word(tid, bp.addr, ARM_BKPT)


def set_pc(tid, bp):
    return set_pc_mode(tid, bp.addr, bp.is_thumb)


def set_pc_mode(tid, addr, is_thumb):
    regs = read_regs(tid)
    if regs is None:
        return False
    if is_thumb:
        regs.uregs[15] = addr | 1
        regs.uregs[16] = regs.uregs[16] | T_BIT
    else:
        regs.uregs[15] = addr
        regs.uregs[16] = regs.uregs[16] & (~T_BIT)
    return write_regs(tid, regs)


def read_vfp_regs(tid):
    regs = VFPRegs()
    iov = IOVec(ctypes.cast(ctypes.byref(regs), ctypes.c_void_p), ctypes.sizeof(regs))
    ctypes.set_errno(0)
    res = ptrace(PTRACE_GETREGSET, tid, NT_PRFPREG, ctypes.byref(iov))
    err = ctypes.get_errno()
    if err or res != 0:
        return None
    return regs


def write_vfp_regs(tid, regs):
    iov = IOVec(ctypes.cast(ctypes.byref(regs), ctypes.c_void_p), ctypes.sizeof(regs))
    ctypes.set_errno(0)
    res = ptrace(PTRACE_SETREGSET, tid, NT_PRFPREG, ctypes.byref(iov))
    err = ctypes.get_errno()
    return err == 0 and res == 0


def set_vfp_s0_s1(tid, s0, s1):
    regs = read_vfp_regs(tid)
    if regs is None:
        return None
    packed = struct.unpack("<Q", struct.pack("<ff", float(s0), float(s1)))[0]
    regs.fpregs[0] = packed
    if not write_vfp_regs(tid, regs):
        return None
    return regs


def thumb_insn_size(tid, addr):
    hw = read_halfword(tid, addr)
    if hw is None:
        return 2
    top = hw & 0xF800
    if top in (0xE800, 0xF000, 0xF800):
        return 4
    return 2


def step_over(tid, bp, is_thumb=None):
    ok_restore = restore_breakpoint(tid, bp)
    mode = bp.is_thumb if is_thumb is None else is_thumb
    ok_pc = set_pc_mode(tid, bp.addr, mode) if ok_restore else False
    return ok_restore, ok_pc


def step_over_exec(tid, bp, is_thumb=None):
    ok_restore = restore_breakpoint(tid, bp)
    ok_pc = False
    ok_step = False
    if ok_restore:
        mode = bp.is_thumb if is_thumb is None else is_thumb
        ok_pc = set_pc_mode(tid, bp.addr, mode)
    if ok_restore and ok_pc:
        ptrace_checked(PTRACE_SINGLESTEP, tid, None, None)
        r, status = wait_for(tid)
        ok_step = r == tid and os.WIFSTOPPED(status)
    ok_rearm = rearm_breakpoint(tid, bp) if ok_step else False
    return ok_restore, ok_pc, ok_step, ok_rearm


def dump_regs(tid, regs):
    if regs is None:
        out(f"REGS tid={tid} unavailable")
        return
    out(
        "REGS tid=%d pc=0x%x lr=0x%x sp=0x%x cpsr=0x%x r0=0x%x r1=0x%x r2=0x%x r3=0x%x"
        % (
            tid,
            regs.uregs[15] & 0xFFFFFFFF,
            regs.uregs[14] & 0xFFFFFFFF,
            regs.uregs[13] & 0xFFFFFFFF,
            regs.uregs[16] & 0xFFFFFFFF,
            regs.uregs[0] & 0xFFFFFFFF,
            regs.uregs[1] & 0xFFFFFFFF,
            regs.uregs[2] & 0xFFFFFFFF,
            regs.uregs[3] & 0xFFFFFFFF,
        )
    )


def match_breakpoint(pc, bp):
    base = pc & ~1
    if base == bp.addr:
        return True
    if base == bp.addr + 2:
        return True
    if base == bp.addr + 4:
        return True
    return False


class Tracer:
    def __init__(self, pid, bps, watches, blocks, cache, event_bus=None, plugin_mgr=None, cmd_queue=None):
        self.pid = pid
        self.bps = bps
        self.cmd_hooks = [bp for bp in bps if bp.meta.get("cmd_hook") is True]
        self.watches = watches
        self.blocks = blocks
        self.cache = cache
        self.event_bus = event_bus
        self.plugin_mgr = plugin_mgr
        self.cmd_queue = cmd_queue or []
        self.attached = set()
        self.mem_tid = None
        self.mem_fd = None
        self.watch_tid = None
        self.watch_last_stop = 0.0
        self.watch_last_warn = 0.0
        self.watch_warn_interval = 2.0
        self.skip_pc = {}
        self.watch_interval = 0.05
        self.watch_next = 0.0
        self.pending_cmd = None
        self.pending_cmd_since = 0.0
        self.pending_cmd_last_log = 0.0
        self.stdin_ready = False
        self.trap_last_log = {}
        self.trap_log_interval = 1.0
        self.cmd_hooks_armed = False
        self.cmd_hook_last_attempt = 0.0
        self.cmd_hook_retry = 0.5
        self.suppress_stop = set()
        self.stop_requested = False
        self.stop_reason = None

    def attach_all(self):
        for tid in list_tids(self.pid):
            res, err = ptrace_checked(PTRACE_ATTACH, tid, None, None)
            if err or res != 0:
                out(f"attach failed tid={tid} res={res} errno={err}")
                continue
            r, status = wait_for(tid)
            if r != tid:
                out(f"attach wait mismatch tid={tid} got={r}")
                continue
            if not os.WIFSTOPPED(status):
                out(f"attach wait not stopped tid={tid} status={status}")
            set_ptrace_options(tid)
            self.attached.add(tid)
        if self.attached:
            self.mem_tid = next(iter(self.attached))
            try:
                self.mem_fd = os.open(f"/proc/{self.pid}/mem", os.O_RDONLY)
                out("mem_reader=/proc/pid/mem")
            except OSError:
                self.mem_fd = None
                out("mem_reader=/proc/pid/mem failed")
        return bool(self.attached)

    def install_all(self):
        ok_all = True
        for bp in self.bps:
            if bp.meta.get("cmd_hook") is True:
                continue
            ok = install_breakpoint(self.mem_tid, bp)
            ok_all = ok_all and ok
            if ok:
                out(f"armed {bp.label()} mode={'thumb' if bp.is_thumb else 'arm'}")
            else:
                out(f"install failed {bp.label()}")
        return ok_all

    def stop_tid(self, tid):
        try:
            os.kill(tid, signal.SIGSTOP)
        except Exception:
            return False
        r, status = wait_for(tid, 0)
        ok = r == tid and os.WIFSTOPPED(status)
        if ok:
            self.suppress_stop.add(tid)
        return ok

    def set_cmd_hooks(self, enable):
        if enable and self.cmd_hooks_armed:
            return
        if not enable and not self.cmd_hooks_armed:
            return
        if self.mem_tid is None:
            return
        if enable:
            now = time.monotonic()
            if (now - self.cmd_hook_last_attempt) < self.cmd_hook_retry:
                return
            self.cmd_hook_last_attempt = now
        stopped = self.stop_tid(self.mem_tid)
        if enable:
            if not stopped:
                out("cmd_hook stop failed")
                self.cmd_hooks_armed = False
                return
            ok_all = True
            for bp in self.cmd_hooks:
                bp.meta.pop("disabled_runtime", None)
                ok = install_breakpoint(self.mem_tid, bp)
                ok_all = ok_all and ok
                if ok:
                    out(f"armed {bp.label()} mode={'thumb' if bp.is_thumb else 'arm'}")
                else:
                    out(f"install failed {bp.label()}")
            if ok_all:
                self.cmd_hooks_armed = True
            else:
                for bp in self.cmd_hooks:
                    bp.meta["disabled_runtime"] = True
                    restore_breakpoint(self.mem_tid, bp)
                self.cmd_hooks_armed = False
                out("cmd_hook arm failed; will retry")
        else:
            for bp in self.cmd_hooks:
                bp.meta["disabled_runtime"] = True
                restore_breakpoint(self.mem_tid, bp)
            self.cmd_hooks_armed = False
        if stopped:
            self.continue_tid(self.mem_tid)

    def continue_tid(self, tid, sig=0):
        ptrace_checked(PTRACE_CONT, tid, None, sig)

    def request_stop(self, reason=None):
        if not self.stop_requested:
            self.stop_requested = True
            self.stop_reason = reason or "requested"

    def handle_clone(self, tid):
        child = get_event_msg(tid)
        if child is None:
            self.continue_tid(tid)
            return
        self.attached.add(child)
        set_ptrace_options(child)
        self.continue_tid(child)
        self.continue_tid(tid)

    def handle_watch(self, tid):
        now = time.monotonic()
        if self.watch_tid is None:
            return
        if tid == self.watch_tid:
            regs = read_regs(tid)
            dump_regs(tid, regs)
            self.watch_last_stop = now
            return
        if (now - self.watch_last_warn) >= self.watch_warn_interval:
            self.watch_last_warn = now

    def poll_watches(self):
        if (not self.watches and not self.blocks) or self.mem_tid is None:
            return
        now = time.monotonic()
        for w in self.watches:
            if w.abs_addr:
                addr = w.base + w.offset
            else:
                base_ptr, err = read_u32_mem(self.pid, w.base + (w.index * 4))
                if base_ptr is None:
                    if self.mem_fd is not None:
                        try:
                            data = os.pread(self.mem_fd, 4, w.base + (w.index * 4))
                            if len(data) == 4:
                                base_ptr = int.from_bytes(data, "little", signed=False)
                                err = 0
                        except OSError as exc:
                            err = exc.errno or err
                    if base_ptr is None:
                        if w.fail_count == 0 or (now - w.last_fail) > 5.0:
                            # out(f"WATCH_FAIL {w.label()} base=0x{w.base:x} err={err}")
                            w.last_fail = now
                        w.fail_count += 1
                        continue
                if base_ptr == 0:
                    if not w.base_seen:
                        w.base_seen = True
                        # out(f"WATCH_BASE {w.label()} base_ptr=0x0")
                    continue
                if not w.base_seen:
                    w.base_seen = True
                    # out(f"WATCH_BASE {w.label()} base_ptr=0x{base_ptr:x}")
                addr = base_ptr + w.offset
            raw = None
            if w.size == 1:
                raw, err = read_u8_mem(self.pid, addr)
            elif w.size == 2:
                raw, err = read_u16_mem(self.pid, addr)
            else:
                raw, err = read_u32_mem(self.pid, addr)
            if raw is None:
                if self.mem_fd is not None:
                    try:
                        data = os.pread(self.mem_fd, w.size, addr)
                        if len(data) == w.size:
                            raw = int.from_bytes(data, "little", signed=False)
                            err = 0
                    except OSError as exc:
                        err = exc.errno or err
            if raw is None:
                if w.fail_count == 0 or (now - w.last_fail) > 5.0:
                    # out(f"WATCH_FAIL {w.label()} addr=0x{addr:x} err={err}")
                    w.last_fail = now
                w.fail_count += 1
                continue
            val = raw
            if w.kind == "s32":
                val = to_s32(val)
            elif w.kind == "u32":
                val = val & 0xFFFFFFFF
            elif w.kind == "s8":
                if val & 0x80:
                    val = val - 0x100
            elif w.kind == "u8":
                val = val & 0xFF
            elif w.kind == "f32":
                val = ctypes.c_float.from_buffer_copy(ctypes.c_uint32(val)).value
            if not w.seen:
                w.seen = True
                w.last = val
                # out(f"WATCH {w.label()} addr=0x{addr:x} value={val}")
                self.cache.set(w.name, val, w.kind)
                self.emit_event(w.event, {"key": w.name, "value": val})
                continue
            if w.last != val:
                w.last = val
                # out(f"WATCH {w.label()} addr=0x{addr:x} value={val}")
                self.cache.set(w.name, val, w.kind)
                self.emit_event(w.event, {"key": w.name, "value": val})
        for b in self.blocks:
            base_ptr, err = read_u32_mem(self.pid, b.base + (b.index * 4))
            if base_ptr is None:
                if self.mem_fd is not None:
                    try:
                        data = os.pread(self.mem_fd, 4, b.base + (b.index * 4))
                        if len(data) == 4:
                            base_ptr = int.from_bytes(data, "little", signed=False)
                            err = 0
                    except OSError as exc:
                        err = exc.errno or err
                if base_ptr is None:
                    if b.fail_count == 0 or (now - b.last_fail) > 5.0:
                        # out(f"WATCH_FAIL {b.label()} base=0x{b.base:x} err={err}")
                        b.last_fail = now
                    b.fail_count += 1
                    continue
            if base_ptr == 0:
                if not b.base_seen:
                    b.base_seen = True
                    # out(f"WATCH_BASE {b.label()} base_ptr=0x0")
                continue
            if not b.base_seen:
                b.base_seen = True
                # out(f"WATCH_BASE {b.label()} base_ptr=0x{base_ptr:x}")
            data, err = read_mem(self.pid, base_ptr, b.size)
            if data is None:
                if self.mem_fd is not None:
                    try:
                        data = os.pread(self.mem_fd, b.size, base_ptr)
                        if len(data) != b.size:
                            data = None
                    except OSError as exc:
                        err = exc.errno or err
                        data = None
            if data is None:
                if b.fail_count == 0 or (now - b.last_fail) > 5.0:
                    # out(f"WATCH_FAIL {b.label()} addr=0x{base_ptr:x} err={err}")
                    b.last_fail = now
                b.fail_count += 1
                continue
            if b.last is None:
                b.last = data
                # out(f"WATCH_BLOCK {b.label()} addr=0x{base_ptr:x} size=0x{b.size:x}")
                continue
            if b.last != data:
                changed = []
                size = b.size
                i = 0
                while i + 4 <= size and len(changed) < 8:
                    if b.last[i : i + 4] != data[i : i + 4]:
                        old = int.from_bytes(b.last[i : i + 4], "little", signed=False)
                        new = int.from_bytes(data[i : i + 4], "little", signed=False)
                        changed.append((i, old, new))
                    i += 4
                b.last = data
                if changed:
                    self.emit_event(b.event, {"key": b.name, "changed": changed})
                continue

    def emit_event(self, event_name, payload):
        if self.event_bus is not None:
            self.event_bus.emit(event_name, payload)

    def handle_hit(self, tid, bp, pc, auto_continue=True, rearm=True):
        proto = bp.meta.get("prototype") or ""
        addr_txt = color(f"BREAKPOINT_ADDR=0x{bp.addr:x}", "33")
        proto_txt = color(f"prototype=\"{proto}\"", "32")
        out(f"{addr_txt} {proto_txt}")
        self.emit_event(
            bp.event,
            {
                "name": bp.name,
                "addr": bp.addr,
                "pc": pc,
            },
        )
        regs = read_regs(tid)
        dump_regs(tid, regs)
        hit_is_thumb = bp.is_thumb
        if regs is not None:
            hit_is_thumb = bool(regs.uregs[16] & T_BIT)
        ok_restore = restore_breakpoint(tid, bp)
        ok_pc = set_pc_mode(tid, bp.addr, hit_is_thumb) if ok_restore else False
        out("resume -> restore=%s setpc=%s" % ("True" if ok_restore else "False", "True" if ok_pc else "False"))
        ok_step = False
        ok_rearm = False
        last_r = 0
        last_status = 0
        temp_bp = None
        if ok_restore and ok_pc:
            step_size = 4
            if hit_is_thumb:
                step_size = thumb_insn_size(tid, bp.addr)
            temp_addr = (bp.addr + step_size) & 0xFFFFFFFF
            temp_bp = Breakpoint(
                f"{bp.name}_step",
                temp_addr,
                {"mode": "thumb" if hit_is_thumb else "arm"},
                f"{bp.name}_step",
                "breakpoint",
            )
            ok_temp = install_breakpoint(tid, temp_bp)
            if ok_temp:
                ptrace_checked(PTRACE_CONT, tid, None, None)
                deadline = time.monotonic() + 1.0
                while time.monotonic() < deadline:
                    r, status = wait_for(tid, os.WNOHANG)
                    last_r = r
                    last_status = status
                    if r == 0:
                        time.sleep(0.002)
                        continue
                    if r == tid and os.WIFSTOPPED(status):
                        ok_step = True
                    break
            if ok_step and temp_bp:
                restore_breakpoint(tid, temp_bp)
                if rearm:
                    ok_rearm = rearm_breakpoint(tid, bp)
                else:
                    ok_rearm = True
                set_pc_mode(tid, temp_bp.addr, hit_is_thumb)
            out(
                "temp_step -> step=%s rearm=%s wait_r=%d wait_status=%d"
                % (
                    "True" if ok_step else "False",
                    "skip" if not rearm else ("True" if ok_rearm else "False"),
                    last_r,
                    last_status,
                )
            )
        if not ok_step:
            if temp_bp:
                restore_breakpoint(tid, temp_bp)
            out("breakpoint step failed (leaving disarmed)")
        self.watch_tid = tid
        self.watch_last_stop = time.monotonic()
        self.watch_last_warn = 0.0
        hit_txt = (
            "HIT_CONFIRMED restore=%d setpc=%d step=%d rearm=%d tid=%d pc=0x%x"
            % (
                1 if ok_restore else 0,
                1 if ok_pc else 0,
                1 if ok_step else 0,
                0 if not rearm else (1 if ok_rearm else 0),
                tid,
                pc,
            )
        )
        out(color(hit_txt, "35"))
        if auto_continue:
            self.continue_tid(tid)

    def loop(self):
        for tid in list(self.attached):
            self.continue_tid(tid)
        while self.attached:
            if self.stop_requested:
                out(f"stop requested: {self.stop_reason}")
                break
            now = time.monotonic()
            self.poll_cmd_queue()
            self.poll_stdin_cmd()
            if self.pending_cmd and not self.cmd_hooks_armed:
                self.set_cmd_hooks(True)
            if not self.pending_cmd and self.cmd_hooks_armed:
                self.set_cmd_hooks(False)
            if self.pending_cmd and (now - self.pending_cmd_last_log) > 1.0:
                self.pending_cmd_last_log = now
                out(f"CMD waiting for breakpoint: {self.pending_cmd}")
            if self.watches and now >= self.watch_next:
                self.poll_watches()
                self.watch_next = now + self.watch_interval
            tid, status = wait_for(-1, WAIT_ALL | os.WNOHANG)
            if tid == 0:
                time.sleep(0.01)
                continue
            if tid == -1:
                out("waitpid returned -1, exiting")
                break
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                self.attached.discard(tid)
                continue
            if not os.WIFSTOPPED(status):
                self.continue_tid(tid)
                continue
            event = (status >> 16) & 0xFFFF
            if event == PTRACE_EVENT_CLONE:
                self.handle_clone(tid)
                continue
            if tid not in self.attached:
                self.attached.add(tid)
                set_ptrace_options(tid)
            sig = os.WSTOPSIG(status)
            if sig == signal.SIGSTOP and tid in self.suppress_stop:
                self.suppress_stop.discard(tid)
                self.continue_tid(tid, 0)
                continue
            self.handle_watch(tid)
            if sig == signal.SIGTRAP or sig == signal.SIGILL:
                pc_val = read_pc(tid)
                bp_hit = None
                if pc_val is not None:
                    if tid in self.skip_pc and self.skip_pc[tid] == pc_val:
                        self.skip_pc.pop(tid, None)
                        self.continue_tid(tid)
                        continue
                    for bp in self.bps:
                        if bp.meta.get("disabled_runtime") is True:
                            if bp.meta.get("cmd_hook") is not True:
                                continue
                            if bp.orig_word is None and bp.orig_halfword is None:
                                continue
                        if match_breakpoint(pc_val, bp):
                            bp_hit = bp
                            break
                if bp_hit:
                    auto_cont = self.pending_cmd is None
                    rearm = not (bp_hit.meta.get("cmd_hook") and not self.cmd_hooks_armed)
                    self.handle_hit(tid, bp_hit, pc_val, auto_continue=auto_cont, rearm=rearm)
                    if self.pending_cmd and bp_hit.meta.get("cmd_hook") and self.cmd_hooks_armed:
                        spec = self.parse_call_cmd(self.pending_cmd)
                        if spec is None:
                            out(f"CMD parse failed: {self.pending_cmd}")
                            self.pending_cmd = None
                            self.continue_tid(tid)
                            continue
                        self.inject_call(tid, spec)
                        self.pending_cmd = None
                        self.continue_tid(tid)
                else:
                    now = time.monotonic()
                    last = self.trap_last_log.get(tid, 0.0)
                    if (now - last) >= self.trap_log_interval:
                        self.trap_last_log[tid] = now
                        out(
                            "TRAP_NO_BP tid=%d pc=%s sig=%d"
                            % (
                                tid,
                                "None" if pc_val is None else f"0x{pc_val:x}",
                                sig,
                            )
                        )
                    self.continue_tid(tid)
                continue
            self.continue_tid(tid, sig)

    def cleanup(self):
        if self.attached and self.bps:
            restore_tid = self.mem_tid
            if restore_tid is None or not self.stop_tid(restore_tid):
                restore_tid = None
                for tid in self.attached:
                    if self.stop_tid(tid):
                        restore_tid = tid
                        break
            if restore_tid is not None:
                for bp in self.bps:
                    ok = restore_breakpoint(restore_tid, bp)
                    if not ok:
                        out(f"restore failed {bp.label()}")
        detach_all(self.attached)
        if self.plugin_mgr is not None:
            self.plugin_mgr.unload_all()
        if self.mem_fd is not None:
            try:
                os.close(self.mem_fd)
            except OSError:
                pass

    def poll_stdin_cmd(self):
        if not STDIN_NONBLOCK and not set_stdin_nonblock():
            return
        try:
            rlist, _, _ = select.select([sys.stdin], [], [], 0)
        except Exception:
            return
        if not rlist:
            return
        try:
            line = sys.stdin.readline()
        except Exception:
            return
        if not line:
            return
        cmd = line.strip()
        self.enqueue_cmd(cmd)

    def enqueue_cmd(self, cmd):
        if cmd is None:
            return False
        text = str(cmd).strip()
        if not text:
            return False
        if not text.startswith("/") or len(text) == 1:
            out(f"CMD ignored (missing /): {text}")
            return False
        self.cmd_queue.append(text)
        out(f"CMD queued: {text}")
        return True

    def queue_cmd(self, cmd):
        if self.pending_cmd is not None:
            return False
        if not cmd:
            return False
        if cmd.startswith("/"):
            cmd = cmd[1:]
        if not cmd:
            return False
        self.pending_cmd = cmd
        self.pending_cmd_since = time.monotonic()
        self.pending_cmd_last_log = 0.0
        out(f"CMD pending: {cmd}")
        return True

    def poll_cmd_queue(self):
        if self.pending_cmd is not None:
            return
        if not self.cmd_queue:
            return
        cmd = self.cmd_queue.pop(0)
        if cmd is None:
            return
        self.queue_cmd(str(cmd))

    def parse_call_cmd(self, cmd):
        parts = cmd.split()
        if not parts:
            return None
        if parts[0].lower() == "home":
            axis = 0
            if len(parts) >= 2:
                axis_token = parts[1].strip().lower()
                if axis_token in ("z", "0"):
                    axis = 0
                elif axis_token in ("x", "1"):
                    axis = 1
                else:
                    axis = parse_address(axis_token) or 0
            return {"kind": "home", "axis": axis}
        if parts[0].lower() == "movez":
            dist_mm = parse_float(parts[1]) if len(parts) >= 2 else 1.0
            speed = parse_float(parts[2]) if len(parts) >= 3 else None
            wait = parse_address(parts[3]) if len(parts) >= 4 else 0
            return {
                "kind": "movez",
                "axis": 0,
                "dist_mm": dist_mm,
                "speed": speed,
                "wait": wait or 0,
            }
        if parts[0].lower() == "call" and len(parts) >= 2:
            try:
                addr = parse_address(parts[1])
            except Exception:
                addr = None
            if not addr:
                return None
            args = [0, 0, 0, 0]
            for i in range(4):
                if 2 + i < len(parts):
                    args[i] = parse_address(parts[2 + i]) or 0
            thumb = False
            if "thumb" in parts or "t" in parts:
                thumb = True
            return {"addr": addr, "thumb": thumb, "args": args}
        return None

    def inject_call(self, tid, spec):
        if spec is None:
            out("CMD spec invalid")
            return
        vfp_saved = None

        def do_inject(addr, thumb, args, vfp_saved):
            regs = read_regs(tid)
            if regs is None:
                out("CMD inject failed: could not read regs")
                return False
            out(f"CMD injecting addr=0x{addr:x} thumb={'True' if thumb else 'False'} args={args}")
            saved = ArmRegs()
            for i in range(18):
                saved.uregs[i] = regs.uregs[i]
            return_pc = regs.uregs[15] & 0xFFFFFFFF
            return_thumb = bool(regs.uregs[16] & T_BIT)
            ret_bp = Breakpoint(
                "cmd_return",
                return_pc & ~1,
                {"mode": "thumb" if return_thumb else "arm"},
                "cmd_return",
                "breakpoint",
            )
            if not install_breakpoint(tid, ret_bp):
                out("CMD inject failed: return breakpoint")
                return False
            if thumb:
                target_pc = addr | 1
                regs.uregs[16] = regs.uregs[16] | T_BIT
            else:
                target_pc = addr & ~1
                regs.uregs[16] = regs.uregs[16] & (~T_BIT)
            regs.uregs[15] = target_pc
            if return_thumb:
                regs.uregs[14] = return_pc | 1
            else:
                regs.uregs[14] = return_pc & ~1
            regs.uregs[0] = args[0] & 0xFFFFFFFF
            regs.uregs[1] = args[1] & 0xFFFFFFFF
            regs.uregs[2] = args[2] & 0xFFFFFFFF
            regs.uregs[3] = args[3] & 0xFFFFFFFF
            ok_wr = write_regs(tid, regs)
            if not ok_wr:
                restore_breakpoint(tid, ret_bp)
                out("CMD inject failed: write_regs")
                return False
            ptrace_checked(PTRACE_CONT, tid, None, None)
            deadline = time.monotonic() + 2.0
            got_ret = False
            last_r = 0
            last_status = 0
            while time.monotonic() < deadline:
                r, status = wait_for(tid, os.WNOHANG)
                last_r = r
                last_status = status
                if r == 0:
                    time.sleep(0.002)
                    continue
                if r != tid or not os.WIFSTOPPED(status):
                    break
                pc_val = read_pc(tid)
                if pc_val is not None and match_breakpoint(pc_val, ret_bp):
                    got_ret = True
                    break
                self.continue_tid(tid)
            if not got_ret:
                try:
                    os.kill(tid, signal.SIGSTOP)
                except Exception:
                    pass
                wait_for(tid, 0)
            restore_breakpoint(tid, ret_bp)
            regs_after = read_regs(tid)
            retval = regs_after.uregs[0] & 0xFFFFFFFF if regs_after else None
            ok_restore = write_regs(tid, saved)
            out(
                "CMD inject call addr=0x%x thumb=%s r0=%d r1=%d r2=%d r3=%d retval=%s restore=%s wait_r=%d wait_status=%d"
                % (
                    addr,
                    "True" if thumb else "False",
                    args[0],
                    args[1],
                    args[2],
                    args[3],
                    "None" if retval is None else f"{retval} ({to_s32(retval)})",
                    "ok" if ok_restore else "fail",
                    last_r,
                    last_status,
                )
            )
            if not ok_restore:
                out("CMD inject warning: registers not restored")
            if vfp_saved is not None:
                write_vfp_regs(tid, vfp_saved)
            return ok_restore

        if spec.get("kind") == "home":
            axis = int(spec.get("axis") or 0)
            out(f"CMD home axis={axis}")
            if not do_inject(0x53548, False, [axis, 0, 0, 0], None):
                return
            do_inject(0x53704, False, [axis, 0, 0, 0], None)
            return
        addr = spec.get("addr")
        thumb = spec.get("thumb") is True
        args = spec.get("args") or [0, 0, 0, 0]
        if spec.get("kind") == "movez":
            axis = int(spec.get("axis") or 0)
            dist_mm = spec.get("dist_mm")
            if dist_mm is None:
                dist_mm = spec.get("step")
            try:
                dist_mm = float(dist_mm)
            except (TypeError, ValueError):
                dist_mm = 0.0
            speed = spec.get("speed")
            if speed is not None:
                try:
                    speed = float(speed)
                except (TypeError, ValueError):
                    speed = None
            flags = int(spec.get("wait") or 0)
            base_ptr, err = read_u32_any(self.pid, self.mem_fd, 0x2FA124 + axis * 4)
            if not base_ptr:
                out(f"CMD inject failed: axis base ptr err={err}")
                return
            mm_per_step, err = read_f64_any(self.pid, self.mem_fd, base_ptr + 24)
            if mm_per_step is None:
                out(f"CMD inject failed: axis scale err={err}")
                return
            cur_steps_u, err = read_u32_any(self.pid, self.mem_fd, base_ptr + 0x4C)
            if cur_steps_u is None:
                out(f"CMD inject failed: axis current err={err}")
                return
            cur_steps = to_s32(cur_steps_u)
            min_steps = None
            max_steps = None
            min_u, err = read_u32_any(self.pid, self.mem_fd, base_ptr + 0x40)
            if min_u is not None:
                min_steps = to_s32(min_u)
            max_u, err = read_u32_any(self.pid, self.mem_fd, base_ptr + 0x3C)
            if max_u is not None:
                max_steps = to_s32(max_u)
            step_delta = int(round(dist_mm / mm_per_step)) if mm_per_step else 0
            if step_delta == 0 and dist_mm != 0.0:
                step_delta = 1 if dist_mm > 0 else -1
            target_steps = cur_steps - step_delta
            if min_steps is not None and target_steps < min_steps:
                target_steps = min_steps
            if max_steps is not None and target_steps > max_steps:
                target_steps = max_steps
            pos_mm = float(target_steps) * mm_per_step
            if speed is None or speed <= 0:
                speed_mm, err = read_f32_any(self.pid, self.mem_fd, 0x39FAF4)
                if speed_mm is None or speed_mm <= 0:
                    speed_mm = 1.0
            else:
                speed_mm = float(speed)
            addr = 0x535AC
            thumb = False
            args = [axis, flags, 0, 0]
            dbg(
                "CMD movez axis=%d cur=%d target=%d dist_mm=%.6f pos_mm=%.6f speed_mm=%.6f flags=0x%x"
                % (axis, cur_steps, target_steps, dist_mm, pos_mm, speed_mm, flags)
            )
            vfp_saved = set_vfp_s0_s1(tid, pos_mm, speed_mm)
            if vfp_saved is None:
                out("CMD inject failed: set VFP regs")
                return
        do_inject(addr, thumb, args, vfp_saved)


def detach_all(tids):
    for tid in tids:
        ptrace_checked(PTRACE_DETACH, tid, None, None)


def find_chitu_pid(target_exe):
    best = None
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        exe_path = os.path.join(entry.path, "exe")
        try:
            resolved = os.readlink(exe_path)
        except OSError:
            continue
        if resolved == target_exe:
            if best is None or pid < best:
                best = pid
    return best


def set_stdin_nonblock():
    global STDIN_NONBLOCK
    if STDIN_NONBLOCK:
        return True
    try:
        flags = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        STDIN_NONBLOCK = True
        return True
    except Exception as exc:
        out(f"stdin nonblock failed: {exc}")
        return False


def main():
    target = "/customer/resources/chitu"
    pid = find_chitu_pid(target)
    if pid is None:
        out(f"could not find running process pointing to {target}")
        return 1
    out(f"using pid {pid} for target {target}")

    try:
        bps, watches, blocks = load_breakpoints("devmode.json")
    except Exception as exc:
        out(f"failed to load devmode.json: {exc}")
        return 1

    picked = pick_update_breakpoints(bps)
    if not picked:
        out("no do7-related breakpoints found")
        return 1
    out(
        f"loaded {len(bps)} entries, using {len(picked)} breakpoints, {len(watches)} watches, {len(blocks)} watch_blocks"
    )
    events = set()
    event_keys = {}
    keys = []
    for w in watches:
        keys.append(w.name)
        events.add(w.event)
        event_keys.setdefault(w.event, []).append(w.name)
    for b in blocks:
        events.add(b.event)
        event_keys.setdefault(b.event, [])
    for bp in picked:
        events.add(bp.event)
        event_keys.setdefault(bp.event, [])
    events = sorted(events)
    keys = sorted(keys)
    for key_list in event_keys.values():
        key_list.sort()

    cache = ValueCache()
    cmd_queue = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    event_bus = EventBus()
    plugin_mgr = PluginManager(event_bus, base_dir, cache, events, event_keys, keys, cmd_queue)
    plugin_mgr.load_all()

    tracer = Tracer(
        pid,
        picked,
        watches,
        blocks,
        cache,
        event_bus=event_bus,
        plugin_mgr=plugin_mgr,
        cmd_queue=cmd_queue,
    )
    def handle_signal(signum, _frame):
        tracer.request_stop(f"signal {signum}")

    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGPIPE):
        try:
            signal.signal(sig, handle_signal)
        except Exception:
            pass
    if not tracer.attach_all():
        out("attach failed")
        return 1
    exit_code = 0
    try:
        tracer.install_all()
        tracer.loop()
    except KeyboardInterrupt:
        out("KeyboardInterrupt received, cleaning up")
        exit_code = 1
    finally:
        tracer.cleanup()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
