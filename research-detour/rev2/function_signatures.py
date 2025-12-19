#!/usr/bin/env python3
import ctypes
import json
import os
import signal
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


class Breakpoint:
    def __init__(self, name, addr, meta):
        self.name = name
        self.addr = addr
        self.meta = meta
        self.is_thumb = False
        self.orig_word = None
        self.orig_halfword = None

    def label(self):
        return f"{self.name}@0x{self.addr:x}"


class Watch:
    def __init__(self, name, base, index, offset, kind, size, abs_addr):
        self.name = name
        self.base = base
        self.index = index
        self.offset = offset
        self.kind = kind
        self.size = size
        self.abs_addr = abs_addr
        self.last = None
        self.seen = False
        self.base_seen = False
        self.fail_count = 0
        self.last_fail = 0.0

    def label(self):
        return f"{self.name}[{self.index}]"


class WatchBlock:
    def __init__(self, name, base, index, size):
        self.name = name
        self.base = base
        self.index = index
        self.size = size
        self.last = None
        self.base_seen = False
        self.fail_count = 0
        self.last_fail = 0.0

    def label(self):
        return f"{self.name}[{self.index}]"


def ts():
    return f"{time.monotonic():.6f}"


def out(msg):
    print(f"{ts()} {msg}", flush=True)


def dbg(msg):
    if DEBUG:
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


def read_u32_mem(pid, addr):
    data, err = read_mem(pid, addr, 4)
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
            base = parse_address(entry.get("base"))
            index = entry.get("index", 0)
            size = int(entry.get("size") or 0)
            if base is None or size <= 0:
                continue
            blocks.append(WatchBlock(name, base, int(index), size))
            continue
        if entry.get("watch") is True:
            name = entry.get("name", "watch")
            base = parse_address(entry.get("base"))
            index = entry.get("index", 0)
            offset = parse_address(entry.get("offset"))
            kind = (entry.get("kind") or "s32").lower()
            size = int(entry.get("size") or 4)
            abs_addr = entry.get("abs") is True
            if base is None or offset is None:
                continue
            watches.append(Watch(name, base, int(index), offset, kind, size, abs_addr))
            continue
        name = entry.get("name", "unnamed")
        addr_val = parse_address(entry.get("address"))
        if not addr_val:
            continue
        meta = dict(entry)
        bps.append(Breakpoint(name, addr_val, meta))
    return bps, watches, blocks


def pick_update_breakpoints(bps):
    picked = []
    for bp in bps:
        if bp.meta.get("disabled") is True:
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
        dbg(f"INSTALL thumb addr=0x{bp.addr:x} ok={ok}")
        return ok
    orig = read_word(tid, bp.addr)
    if orig is None:
        return False
    bp.orig_word = orig
    ok = write_word(tid, bp.addr, ARM_BKPT)
    dbg(f"INSTALL arm addr=0x{bp.addr:x} ok={ok}")
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
    def __init__(self, pid, bps, watches, blocks):
        self.pid = pid
        self.bps = bps
        self.watches = watches
        self.blocks = blocks
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
        self.axis_state = {}
        self.print_state = {"level": None, "sync": None, "last_print": 0.0}
        self.temp_state = {"temp_c": None, "online": None, "state": None, "control": None, "flag": None, "last_print": 0.0}

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
            ok = install_breakpoint(self.mem_tid, bp)
            ok_all = ok_all and ok
            if ok:
                out(f"armed {bp.label()} mode={'thumb' if bp.is_thumb else 'arm'}")
            else:
                out(f"install failed {bp.label()}")
        return ok_all

    def continue_tid(self, tid, sig=0):
        ptrace_checked(PTRACE_CONT, tid, None, sig)

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
                            out(f"WATCH_FAIL {w.label()} base=0x{w.base:x} err={err}")
                            w.last_fail = now
                        w.fail_count += 1
                        continue
                if base_ptr == 0:
                    if not w.base_seen:
                        w.base_seen = True
                        out(f"WATCH_BASE {w.label()} base_ptr=0x0")
                    continue
                if not w.base_seen:
                    w.base_seen = True
                    out(f"WATCH_BASE {w.label()} base_ptr=0x{base_ptr:x}")
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
                    out(f"WATCH_FAIL {w.label()} addr=0x{addr:x} err={err}")
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
                out(f"WATCH {w.label()} addr=0x{addr:x} value={val}")
                self.update_axis_state(w, val)
                self.update_print_state(w, val)
                self.update_temp_state(w, val)
                continue
            if w.last != val:
                w.last = val
                out(f"WATCH {w.label()} addr=0x{addr:x} value={val}")
                self.update_axis_state(w, val)
                self.update_print_state(w, val)
                self.update_temp_state(w, val)
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
                        out(f"WATCH_FAIL {b.label()} base=0x{b.base:x} err={err}")
                        b.last_fail = now
                    b.fail_count += 1
                    continue
            if base_ptr == 0:
                if not b.base_seen:
                    b.base_seen = True
                    out(f"WATCH_BASE {b.label()} base_ptr=0x0")
                continue
            if not b.base_seen:
                b.base_seen = True
                out(f"WATCH_BASE {b.label()} base_ptr=0x{base_ptr:x}")
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
                    out(f"WATCH_FAIL {b.label()} addr=0x{base_ptr:x} err={err}")
                    b.last_fail = now
                b.fail_count += 1
                continue
            if b.last is None:
                b.last = data
                out(f"WATCH_BLOCK {b.label()} addr=0x{base_ptr:x} size=0x{b.size:x}")
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
                    for off, old, new in changed:
                        if old & 0x80000000 or new & 0x80000000:
                            out(
                                "WATCH_BLOCK %s off=0x%x old=%d new=%d (u32 old=%d new=%d)"
                                % (b.label(), off, to_s32(old), to_s32(new), old, new)
                            )
                        else:
                            out(f"WATCH_BLOCK {b.label()} off=0x{off:x} old={old} new={new}")
                continue

    def axis_label(self, index):
        if index == 0:
            return "Z"
        if index == 1:
            return "X"
        if index == 2:
            return "Y"
        return f"A{index}"

    def update_axis_state(self, watch, value):
        name = watch.name
        if not name.startswith("axis_"):
            return
        st = self.axis_state.get(watch.index)
        if st is None:
            st = {"cur": None, "tgt": None, "delta": None, "zero": None, "max": None, "last_print": 0.0}
            self.axis_state[watch.index] = st
        if name == "axis_target_position_in_step":
            st["tgt"] = value
        elif name == "axis_zero_position_in_step":
            st["zero"] = value
        elif name == "axis_max_position_in_step":
            st["max"] = value
        elif name == "axis_current_position_in_step":
            st["cur"] = value
        elif name == "axis_remaining_step":
            st["delta"] = value
        now = time.monotonic()
        if (now - st["last_print"]) < 0.2:
            return
        if st["cur"] is None and st["tgt"] is None:
            return
        pct = None
        if st["cur"] is not None and st["zero"] is not None and st["max"] is not None:
            span = st["max"] - st["zero"]
            if span != 0:
                pct = int((st["cur"] - st["zero"]) * 100 / span)
        label = self.axis_label(watch.index)
        msg = f"AXIS {label} cur={st['cur']} target={st['tgt']} delta={st['delta']} home={st['zero']} max={st['max']}"
        if pct is not None:
            msg += f" pct={pct}"
        out(color(msg, "33"))
        st["last_print"] = now

    def update_print_state(self, watch, value):
        if watch.name == "printing_level_mode":
            self.print_state["level"] = value
        elif watch.name == "printing_sync_mode":
            self.print_state["sync"] = value
        else:
            if watch.name == "lattice_busy":
                out(f"PRINTING lattice_busy={value}")
            return
        now = time.monotonic()
        if (now - self.print_state["last_print"]) < 0.5:
            return
        level = self.print_state["level"]
        sync = self.print_state["sync"]
        active = 1 if (level or sync) else 0
        out(f"PRINTING active={active} level_mode={level} sync_mode={sync}")
        self.print_state["last_print"] = now

    def update_temp_state(self, watch, value):
        name = watch.name
        if name == "tank_temp_c":
            self.temp_state["temp_c"] = value
        elif name == "tank_temp_online":
            self.temp_state["online"] = value
        elif name == "tank_heat_state":
            self.temp_state["state"] = value
        elif name == "tank_heat_control":
            self.temp_state["control"] = value
        elif name == "tank_temp_flag":
            self.temp_state["flag"] = value
        else:
            return
        now = time.monotonic()
        if (now - self.temp_state["last_print"]) < 0.5:
            return
        temp_c = self.temp_state["temp_c"]
        online = self.temp_state["online"]
        state = self.temp_state["state"]
        control = self.temp_state["control"]
        flag = self.temp_state["flag"]
        temp_txt = "n/a" if temp_c is None else f"{temp_c:.2f}C"
        status = "OK" if (online == 1 and flag == 1) else "CHECK"
        msg = (
            "VAT_TEMP %s temp=%s online=%s state=%s control=%s"
            % (status, temp_txt, online, state, control)
        )
        out(color(msg, "32"))
        self.temp_state["last_print"] = now

    def handle_hit(self, tid, bp, pc):
        proto = bp.meta.get("prototype") or ""
        addr_txt = color(f"BREAKPOINT_ADDR=0x{bp.addr:x}", "33")
        proto_txt = color(f"prototype=\"{proto}\"", "32")
        out(f"{addr_txt} {proto_txt}")
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
        if ok_restore and ok_pc:
            ptrace_checked(PTRACE_SINGLESTEP, tid, None, None)
            deadline = time.monotonic() + 0.02
            while time.monotonic() < deadline:
                r, status = wait_for(tid, os.WNOHANG)
                if r == 0:
                    time.sleep(0.001)
                    continue
                if r == tid and os.WIFSTOPPED(status):
                    ok_step = True
                break
            if ok_step:
                ok_rearm = rearm_breakpoint(tid, bp)
            out(
                "single_step -> step=%s rearm=%s"
                % ("True" if ok_step else "False", "True" if ok_rearm else "False")
            )
        if not ok_step:
            bp.meta["disabled_runtime"] = True
            out("breakpoint disabled_runtime after step failure")
        self.watch_tid = tid
        self.watch_last_stop = time.monotonic()
        self.watch_last_warn = 0.0
        hit_txt = (
            "HIT_CONFIRMED restore=%d setpc=%d step=%d rearm=%d tid=%d pc=0x%x"
            % (
                1 if ok_restore else 0,
                1 if ok_pc else 0,
                1 if ok_step else 0,
                1 if ok_rearm else 0,
                tid,
                pc,
            )
        )
        out(color(hit_txt, "35"))
        self.continue_tid(tid)

    def loop(self):
        for tid in list(self.attached):
            self.continue_tid(tid)
        while self.attached:
            now = time.monotonic()
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
                            continue
                        if match_breakpoint(pc_val, bp):
                            bp_hit = bp
                            break
                if bp_hit:
                    self.handle_hit(tid, bp_hit, pc_val)
                else:
                    self.continue_tid(tid)
                continue
            self.continue_tid(tid, sig)

    def cleanup(self):
        if self.attached and self.bps:
            restore_tid = next(iter(self.attached))
            for bp in self.bps:
                restore_breakpoint(restore_tid, bp)
        detach_all(self.attached)
        if self.mem_fd is not None:
            try:
                os.close(self.mem_fd)
            except OSError:
                pass


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


def main():
    target = "/customer/resources/chitu"
    pid = find_chitu_pid(target)
    if pid is None:
        out(f"could not find running process pointing to {target}")
        return 1
    out(f"using pid {pid} for target {target}")

    try:
        bps, watches, blocks = load_breakpoints("function_signatures.json")
    except Exception as exc:
        out(f"failed to load function_signatures.json: {exc}")
        return 1

    picked = pick_update_breakpoints(bps)
    if not picked:
        out("no do7-related breakpoints found")
        return 1
    out(
        f"loaded {len(bps)} entries, using {len(picked)} breakpoints, {len(watches)} watches, {len(blocks)} watch_blocks"
    )
    for w in watches:
        out(
            "watch %s base=0x%x index=%d offset=0x%x kind=%s size=%d"
            % (w.name, w.base, w.index, w.offset, w.kind, w.size)
        )
    for b in blocks:
        out("watch_block %s base=0x%x index=%d size=0x%x" % (b.name, b.base, b.index, b.size))

    tracer = Tracer(pid, picked, watches, blocks)
    if not tracer.attach_all():
        out("attach failed")
        return 1
    try:
        tracer.install_all()
        tracer.loop()
    except KeyboardInterrupt:
        out("KeyboardInterrupt received, cleaning up")
        tracer.cleanup()
        return 1
    finally:
        tracer.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
