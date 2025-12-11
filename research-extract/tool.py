#!/usr/bin/env python3
import re, sys, zlib, struct
from pathlib import Path


def linux_crc32(init, data):
    return zlib.crc32(data, init ^ 0xFFFFFFFF) ^ 0xFFFFFFFF


def parse_header(bin_path):
    parts = []
    name = None
    with open(bin_path, "rb") as f:
        for i, raw in enumerate(f):
            try:
                line = raw.decode("utf-8").strip()
            except UnicodeDecodeError:
                break  # hit binary
            if line.startswith("# File Partition:"):
                name = line.split(":", 1)[1].strip()
                continue
            m = re.search(r"fatload\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)\s+(\S+)", line)
            if m:
                length = int(m.group(1), 0)
                offset = int(m.group(2), 0)
                parts.append((name or "noname", offset, length))
    return parts


def crc32_ascii_tail(block):
    """If last 8 bytes are ASCII hex, return (crc_calc, crc_tail, ok, payload_len)."""
    if len(block) < 8:
        return None
    tail = block[-8:]
    try:
        tail_val = int(tail.decode("ascii"), 16)
    except ValueError:
        return None
    payload = block[:-8]
    calc = zlib.crc32(payload) & 0xFFFFFFFF
    return calc, tail_val, (calc == tail_val), len(payload)


def extract(bin_path, parts):
    data = Path(bin_path).read_bytes()
    for name, offset, length in parts:
        blk = data[offset : offset + length]
        out = Path(f"partition_{offset:08X}_{length:08X}.bin")
        out.write_bytes(blk)
        crc_full = zlib.crc32(blk) & 0xFFFFFFFF
        info = f"{name}: offset=0x{offset:X} len=0x{length:X} crc32_full={crc_full:08x}"
        tail_info = ""
        tail = crc32_ascii_tail(blk)
        if tail:
            calc, tail_val, ok, payload_len = tail
            tail_info = f" payload_len=0x{payload_len:X} tail_hex={tail_val:08x} calc={calc:08x} match={ok}"
        print(info + tail_info)


def rebuild(bin_path, parts, out_path):
    base = bytearray(Path(bin_path).read_bytes())
    for name, offset, length in parts:
        part_file = Path(f"partition_{offset:08X}_{length:08X}.bin")
        if not part_file.exists():
            print(f"{part_file} skipping (not found)")
            continue
        blk = bytearray(part_file.read_bytes())
        if len(blk) != length:
            print(f"{part_file} skipping (expected {length}, got {len(blk)})")
            continue
        # if block looks like [payload][ascii_crc8], recompute the tail
        tail = crc32_ascii_tail(blk)
        if tail:
            payload = blk[:-8]
            crc = zlib.crc32(payload) & 0xFFFFFFFF
            blk[-8:] = f"{crc:08x}".encode("ascii")
            print(f"rebuilt ASCII CRC for {part_file}: {crc:08x}")
        # splice back
        base[offset : offset + length] = blk
    Path(out_path).write_bytes(base)
    print(f"wrote {out_path}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: ChituUpgrade.bin [--extract|--shadow|--startup|--build]")
    bin_path = sys.argv[1]
    parts = parse_header(bin_path)
    if not parts:
        raise SystemExit("no partitions")

    if "--extract" in sys.argv:
        extract(bin_path, parts)

    if "--shadow" in sys.argv:
        shadowOld = b"$5$LWZE1Y5U$kQvhpcTMvhmcZdVZGPa2.yuOeUmtstssQBWWQRUDJ02"
        shadowNew = b"$5$LWZE1Y5U$Bp6aYr6/hntJ0ycLZY.IZGV5TxdVyIrBH98.stRpR.8"
        # openssl passwd -5 -salt LWZE1Y5U 'pass'
        p = Path("partition_00260000_01FF8008.bin")
        data = p.read_bytes()
        if shadowOld not in data:
            raise SystemExit("not found")
        p.write_bytes(data.replace(shadowOld, shadowNew, 1))
        print("patched shadow", p)

    if "--startup" in sys.argv:
        scriptNew = b'#!/bin/sh\n[ "$1" = "start" ] || exit 0\nuntil /media/sd?1/startup.sh ; do sleep 1 ; done &\nexit 0\n'
        p = Path("partition_00260000_01FF8008.bin")
        data = bytearray(p.read_bytes())
        off = data.find(b"TELNETD_ARGS=-F")
        if off < 0:
            raise SystemExit("not found")
        node_start = None
        start_candidate = off & ~0x7
        for cand in range(start_candidate, -1, -8):
            if data[cand : cand + 4] == b"\x31\x18\x10\x06":
                node_start = cand
                break
        if node_start is None:
            raise SystemExit("node_start")

        len_off = node_start + 4 + 4 + 8
        node_len = struct.unpack_from("<I", data, len_off)[0]

        script_len = len(scriptNew)

        payload_off = node_start + 0x30
        payload_len = node_len - 0x30
        data[payload_off : payload_off + payload_len] = b" " * payload_len
        data[payload_off : payload_off + script_len] = scriptNew

        # UBIFS_COMPR_NONE
        compr_type_off = node_start + 0x2C
        struct.pack_into("<H", data, compr_type_off, 0)
        compr_size_off = node_start + 0x2E
        struct.pack_into("<H", data, compr_size_off, 0)

        # UBIFS_DATA_NODE_SZ
        size_off = node_start + 0x28
        struct.pack_into("<I", data, size_off, payload_len)

        crc_region = bytes(data[node_start + 8 : node_start + node_len])
        new_crc = linux_crc32(0xFFFFFFFF, crc_region)
        struct.pack_into("<I", data, node_start + 4, new_crc)

        p.write_bytes(data)
        print("patched startup", p)

    if "--build" in sys.argv:
        rebuild(bin_path, parts, "ChituUpgrade.patched.bin")


if __name__ == "__main__":
    main()

# proof:
#   hexdump -C partition_00260000_01FF8008_.bin > partition_00260000_01FF8008_.bin.hex
#   hexdump -C partition_00260000_01FF8008.bin  > partition_00260000_01FF8008.bin.hex
#   diff -u partition_00260000_01FF8008_.bin.hex partition_00260000_01FF8008.bin.hex |head -n 50

# extract:
#   ubireader_extract_files partition_00260000_01FF8008.bin -o partition_00260000_01FF8008.bin_fs
