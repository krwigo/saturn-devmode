#!/usr/bin/env python3
import ctypes
import ctypes.util
import os
import signal
import sys
from typing import Tuple


# Basic x86_64 register layout for PTRACE_GETREGS/SETREGS.
class user_regs_struct(ctypes.Structure):
    _fields_ = [
        ("r15", ctypes.c_ulonglong),
        ("r14", ctypes.c_ulonglong),
        ("r13", ctypes.c_ulonglong),
        ("r12", ctypes.c_ulonglong),
        ("rbp", ctypes.c_ulonglong),
        ("rbx", ctypes.c_ulonglong),
        ("r11", ctypes.c_ulonglong),
        ("r10", ctypes.c_ulonglong),
        ("r9", ctypes.c_ulonglong),
        ("r8", ctypes.c_ulonglong),
        ("rax", ctypes.c_ulonglong),
        ("rcx", ctypes.c_ulonglong),
        ("rdx", ctypes.c_ulonglong),
        ("rsi", ctypes.c_ulonglong),
        ("rdi", ctypes.c_ulonglong),
        ("orig_rax", ctypes.c_ulonglong),
        ("rip", ctypes.c_ulonglong),
        ("cs", ctypes.c_ulonglong),
        ("eflags", ctypes.c_ulonglong),
        ("rsp", ctypes.c_ulonglong),
        ("ss", ctypes.c_ulonglong),
        ("fs_base", ctypes.c_ulonglong),
        ("gs_base", ctypes.c_ulonglong),
        ("ds", ctypes.c_ulonglong),
        ("es", ctypes.c_ulonglong),
        ("fs", ctypes.c_ulonglong),
        ("gs", ctypes.c_ulonglong),
    ]


# ptrace request constants
PTRACE_TRACEME = 0
PTRACE_PEEKDATA = 2
PTRACE_POKEDATA = 5
PTRACE_CONT = 7
PTRACE_SINGLESTEP = 9
PTRACE_GETREGS = 12
PTRACE_SETREGS = 13
PTRACE_ATTACH = 16
PTRACE_DETACH = 17
PTRACE_INTERRUPT = 0x4207

WORD_MASK = (1 << (ctypes.sizeof(ctypes.c_void_p) * 8)) - 1


def load_libc() -> ctypes.CDLL:
    name = ctypes.util.find_library("c")
    if name:
        return ctypes.CDLL(name, use_errno=True)
    return ctypes.CDLL(None, use_errno=True)


libc = load_libc()
libc.ptrace.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
libc.ptrace.restype = ctypes.c_long


def ptrace(request: int, pid: int, addr: int = 0, data=0) -> int:
    if isinstance(data, int):
        data_arg = ctypes.c_void_p(data)
    else:
        data_arg = data
    res = libc.ptrace(request, pid, ctypes.c_void_p(addr), data_arg)
    if res == -1:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))
    return res


def find_libc_base(pid: int, expected_path: str = "") -> Tuple[int, str]:
    maps_path = f"/proc/{pid}/maps"
    with open(maps_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 6:
                continue
            addr_range, perms, _offset, _dev, _inode, path = parts[0:6]
            if "r-xp" not in perms:
                continue
            if expected_path and path == expected_path:
                start_str, _end = addr_range.split("-", 1)
                return int(start_str, 16), path
            if not expected_path and "libc" in os.path.basename(path):
                start_str, _end = addr_range.split("-", 1)
                return int(start_str, 16), path
    raise RuntimeError("Could not locate libc in maps")


def calc_target_printf(pid: int) -> int:
    target_base, target_path = find_libc_base(pid)
    # Align to the same on-disk libc so the symbol offset matches.
    self_base, _ = find_libc_base(os.getpid(), expected_path=target_path)
    local_libc = ctypes.CDLL(target_path, use_errno=True)
    local_printf = ctypes.cast(local_libc.printf, ctypes.c_void_p).value
    printf_offset = local_printf - self_base
    return target_base + printf_offset


def set_breakpoint(pid: int, addr: int):
    orig = ptrace(PTRACE_PEEKDATA, pid, addr, 0) & WORD_MASK
    patched = (orig & ~0xFF) | 0xCC
    ptrace(PTRACE_POKEDATA, pid, addr, patched)
    return orig


def restore_word(pid: int, addr: int, word: int):
    ptrace(PTRACE_POKEDATA, pid, addr, word & WORD_MASK)


def adjust_rip_back(pid: int):
    regs = user_regs_struct()
    ptrace(PTRACE_GETREGS, pid, 0, ctypes.byref(regs))
    regs.rip -= 1
    ptrace(PTRACE_SETREGS, pid, 0, ctypes.byref(regs))


def wait_for_stop(pid: int):
    while True:
        _wpid, status = os.waitpid(pid, 0)
        if os.WIFSTOPPED(status):
            return os.WSTOPSIG(status)
        if os.WIFEXITED(status) or os.WIFSIGNALED(status):
            raise ChildProcessError("target exited")


def main():
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <pid>", file=sys.stderr)
        sys.exit(1)

    pid = int(sys.argv[1])
    target_addr = calc_target_printf(pid)
    print(f"[*] hooking printf at 0x{target_addr:x}")

    ptrace(PTRACE_ATTACH, pid, 0, 0)
    wait_for_stop(pid)
    print("[*] attached")

    original_word = set_breakpoint(pid, target_addr)
    print("[*] breakpoint installed")

    try:
        ptrace(PTRACE_CONT, pid, 0, 0)
        while True:
            sig = wait_for_stop(pid)
            if sig != signal.SIGTRAP:
                print(f"[!] stopped with signal {sig}, forwarding")
                ptrace(PTRACE_CONT, pid, 0, sig)
                continue

            regs = user_regs_struct()
            try:
                ptrace(PTRACE_GETREGS, pid, 0, ctypes.byref(regs))
                # SysV x86_64: rdi = fmt string, rsi = first vararg. The heartbeat printf
                # only passes the counter now, so read it from rsi instead of rdx.
                counter = regs.rsi
            except OSError:
                counter = None

            if counter is not None:
                print(f"[+] printf hit: counter={counter}")
            else:
                print("[+] printf hit (counter unavailable)")

            adjust_rip_back(pid)
            restore_word(pid, target_addr, original_word)

            # Run the original instruction once, then restore the breakpoint.
            ptrace(PTRACE_SINGLESTEP, pid, 0, 0)
            wait_for_stop(pid)
            original_word = set_breakpoint(pid, target_addr)
            ptrace(PTRACE_CONT, pid, 0, 0)
    except KeyboardInterrupt:
        print("[*] detaching")
    finally:
        stopped = False
        try:
            # Ensure target is stopped before poking memory.
            try:
                ptrace(PTRACE_INTERRUPT, pid, 0, 0)
                wait_for_stop(pid)
                stopped = True
            except OSError:
                try:
                    os.kill(pid, signal.SIGSTOP)
                    wait_for_stop(pid)
                    stopped = True
                except Exception:
                    pass

            regs = None
            if stopped:
                regs = user_regs_struct()
                try:
                    ptrace(PTRACE_GETREGS, pid, 0, ctypes.byref(regs))
                except OSError:
                    regs = None

            if stopped:
                try:
                    restore_word(pid, target_addr, original_word)
                except OSError:
                    pass

            if stopped and regs and regs.rip == target_addr + 1:
                # Landed on the breakpoint; back up RIP and single-step the real instruction.
                regs.rip = target_addr
                try:
                    ptrace(PTRACE_SETREGS, pid, 0, ctypes.byref(regs))
                    ptrace(PTRACE_SINGLESTEP, pid, 0, 0)
                    wait_for_stop(pid)
                    stopped = True
                    try:
                        restore_word(pid, target_addr, original_word)
                    except OSError:
                        pass
                except OSError:
                    pass
        except Exception:
            pass
        try:
            ptrace(PTRACE_DETACH, pid, 0, 0 if stopped else signal.SIGCONT)
        except OSError:
            pass


if __name__ == "__main__":
    main()
