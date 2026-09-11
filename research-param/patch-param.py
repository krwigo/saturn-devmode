#!/usr/bin/env python3
# patch-param.py
#
# Data-only tool for the Chitu 16K machine param file
#   /media/mmcblk0p1/machine_param_ref.bin
# which is a small TLV-wrapped JSON blob. The time-lapse height gate
# ("aic_tlp_no_cap_pos", default 50 = 5 cm) and the post-print home flags
# ("z_home_move_to_zero", "x_home_move_to_zero") are plain JSON keys in it.
#
# Commands:
#   verify  <in.bin>
#       Check the stored 2-byte CRC against a fresh computation. Proves the
#       format/CRC is understood before touching anything.
#
#   read    <in.bin>  <out.json>
#       Extract the JSON payload to a plain .json file for editing.
#       (Verifies the source CRC first; refuses if it doesn't match.)
#
#   write   <template.bin>  <in.json>  [out.bin]
#       Repack: take the header + spare bytes from template.bin, insert the
#       (possibly edited) JSON, recompute the CRC, and write out.bin.
#       If out.bin is omitted it is written IN-PLACE (same file as template).
#       The JSON is re-serialized compactly; the firmware only parses the JSON
#       and checks the CRC, so cosmetic float-text differences are harmless.
#
#   patch   <in.bin>  [--key K]  [--value V]  [--apply]
#       Convenience: in-place single top-level scalar key edit. Default key
#       aic_tlp_no_cap_pos, value 0. Dry-run unless --apply. NOTE: only reaches
#       top-level scalar keys — use read/edit/write for arrays or nested dicts.
#
#   (no command)  <in.bin> [opts]   ==   patch <in.bin> [opts]   (legacy)
#
# Usage examples:
#   python3 patch-param.py verify  machine_param_ref.bin
#   python3 patch-param.py read    machine_param_ref.bin  params.json
#   # ... edit params.json (z_home_move_to_zero, aic_tlp_no_cap_pos, ...) ...
#   python3 patch-param.py write   machine_param_ref.bin  params.json  machine_param_ref.new.bin
#   python3 patch-param.py patch   machine_param_ref.bin  --apply --key aic_tlp_no_cap_pos --value 0
#
# CRC = faithful port of firmware sub_C7364 (VERIFIED: returns the on-device
# stored CRC for the shipped payload). It is NOT plain CRC-16/CCITT — the
# firmware folds each input byte through a nibble-swap + bit-matrix before the
# 0x1021 table lookup, then post-transforms the 16-bit result.

import sys
import re
import json

POLY = 0x1021
INIT = 0x0000


def make_crc_table(poly=POLY):
    table = []
    for i in range(256):
        c = i << 8
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFFFF if (c & 0x8000) else (c << 1) & 0xFFFF
        table.append(c)
    return table


T16 = make_crc_table()


def _post_byte(x):
    # firmware: ((4*rot4(x)) & 0xCC) | ((rot4(x) >> 2) & 0x33), rot4 = nibble swap
    x &= 0xFF
    r = ((x << 4) | (x >> 4)) & 0xFF
    return ((4 * r) & 0xCC) | ((r >> 2) & 0x33)


def crc16(data: bytes) -> int:
    """Faithful port of firmware sub_C7364 (VERIFIED against the on-device file)."""
    crc = INIT
    for b in data:
        v5 = (16 * b) | (b >> 4)                          # nibble swap
        v6 = (4 * v5) & 0xCC | (v5 >> 2) & 0x33
        idx = ((2 * v6) & 0xAA | (v6 >> 1) & 0x55) ^ (crc >> 8)
        crc = T16[idx] ^ ((crc << 8) & 0xFFFF)
    lo, hi = crc & 0xFF, (crc >> 8) & 0xFF
    v8, v9 = _post_byte(lo), _post_byte(hi)
    return ((2 * v9 & 0xAA) | (v9 >> 1 & 0x55)) | (((2 * v8 & 0xAA) | (v8 >> 1 & 0x55)) << 8)


# ---- file layout -----------------------------------------------------------
# VERIFIED against the on-device 4910-byte machine_param_ref.bin:
#
#   [header: bytes before the JSON]  +  [JSON payload]  +  [00 02 02 CRClo CRChi]  +  [spare]
#
# The header contains a quirky var-length field, so we do NOT re-encode it.
# We locate the JSON by its first '{' / last '}', compute the CRC over the JSON,
# and rebuild by splicing: [header][new JSON][00 02 02 newCRC][spare]. The header
# and spare are preserved verbatim from the template; only the JSON changes.

def find_json(buf: bytes):
    start = buf.find(b"{")
    end = buf.rfind(b"}")
    if start < 0 or end < 0 or end < start:
        raise ValueError("no JSON {..} found")
    return start, end + 1


def encode_len_field(length_bytes: bytes, L: int) -> bytes:
    """Encode a var-length field of `len(length_bytes)` bytes summing to L.

    Matches the firmware writer convention: fill leading bytes with 0xFF, put
    the remainder in the next byte, zeros after. E.g. L=4882 over 20 bytes ->
    19x0xFF + 0x25. The parser (sub_D1F6C) simply sums the bytes, so any valid
    decomposition works, but we mirror the firmware for byte-for-byte safety.
    """
    n = len(length_bytes)
    if L < 0 or L > 255 * n:
        raise ValueError(f"length {L} does not fit in {n} bytes")
    out = bytearray(n)
    full, rem = divmod(L, 255)
    # full bytes of 0xFF, then one partial byte, then zeros
    for i in range(n):
        if i < full:
            out[i] = 255
        elif i == full:
            out[i] = rem
        else:
            out[i] = 0
    return bytes(out)


def find_crc_record(buf: bytes, json_end):
    """Return (crc_off, crc_end) where the 2-byte CRC lives at crc_off..crc_end."""
    i = buf.find(b"\x00\x02", json_end)
    if i < 0:
        raise ValueError("no (0,2) CRC record found")
    if i + 3 >= len(buf) or buf[i + 2] != 2:
        raise ValueError("unexpected (0,2) record layout")
    if i + 5 > len(buf):
        raise ValueError("truncated CRC record")
    return i + 3, i + 5      # crc_off, crc_end (exclusive)


def analyze(buf: bytes):
    """Return dict with the parsed layout of a param .bin buffer."""
    js_start, js_end = find_json(buf)
    crc_off, crc_end = find_crc_record(buf, js_end)
    return {
        "buf": buf,
        "js_start": js_start,
        "js_end": js_end,
        "json": buf[js_start:js_end],
        "crc_off": crc_off,
        "crc_end": crc_end,
        "stored_crc": int.from_bytes(buf[crc_off:crc_end], "little"),
        "header": buf[:js_start],
        "spare": buf[crc_end:],
    }


def pack(header: bytes, json_bytes: bytes, spare: bytes) -> bytes:
    # The header's var-length field (bytes 3..22, 20 bytes) must sum to the
    # JSON length, so recompute it whenever the JSON size changes.
    assert len(header) >= 23, "header too short to contain the length field"
    new_header = bytearray(header)
    new_header[3:23] = encode_len_field(bytes(header[3:23]), len(json_bytes))
    c = crc16(json_bytes)
    out = bytearray()
    out += bytes(new_header)
    out += json_bytes
    out += bytes([0x00, 0x02, 0x02])      # (0,2) tag + len 2
    out += c.to_bytes(2, "little")        # new CRC
    out += spare
    return bytes(out)


# ---- commands --------------------------------------------------------------

def declared_len(buf: bytes) -> int:
    """Decode the (0,1) var-length field: the 20 bytes at offsets 3..22 sum to it."""
    return sum(buf[3:23])


def cmd_verify(path):
    with open(path, "rb") as f:
        buf = f.read()
    a = analyze(buf)
    calc = crc16(a["json"])
    decl = declared_len(buf)
    print(f"file size   : {len(buf)}")
    print(f"json        : {len(a['json'])} bytes @ {a['js_start']}..{a['js_end']-1}")
    print(f"declared len: {decl}")
    print(f"stored CRC  : 0x{a['stored_crc']:04x}")
    print(f"computed CRC: 0x{calc:04x}")
    crc_ok = a["stored_crc"] == calc
    len_ok = decl == len(a["json"])
    print(f"CRC verify  : {'PASS' if crc_ok else 'FAIL'}")
    print(f"len verify  : {'PASS' if len_ok else 'FAIL (declared != actual JSON length)'}")
    if not crc_ok:
        sys.exit("stored CRC != computed CRC")
    if not len_ok:
        sys.exit(f"declared length {decl} != actual JSON length {len(a['json'])}")


def cmd_read(in_bin, out_json):
    with open(in_bin, "rb") as f:
        buf = f.read()
    a = analyze(buf)
    calc = crc16(a["json"])
    if a["stored_crc"] != calc:
        sys.exit(f"source CRC mismatch (stored 0x{a['stored_crc']:04x} != computed "
                 f"0x{calc:04x}); refusing to read")
    # Validate it's real JSON before handing it to the user.
    obj = json.loads(a["json"].decode("utf-8"))
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {out_json} ({len(a['json'])} bytes of JSON, pretty-printed)")
    print("edit it, then run: write <template.bin> " + out_json + " [out.bin]")


def cmd_write(template_bin, in_json, out_bin):
    with open(template_bin, "rb") as f:
        buf = f.read()
    a = analyze(buf)
    # sanity: template should currently be valid (warn only)
    calc = crc16(a["json"])
    if a["stored_crc"] != calc:
        print(f"warning: template CRC mismatch (stored 0x{a['stored_crc']:04x} != "
              f"computed 0x{calc:04x}); using its header/spare anyway")
    with open(in_json, "rb") as f:
        raw = f.read()
    obj = json.loads(raw.decode("utf-8"))          # validates + normalizes
    new_json = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    out = pack(a["header"], new_json, a["spare"])
    if out_bin is None:
        out_bin = template_bin                      # in-place
    with open(out_bin, "wb") as f:
        f.write(out)
    print(f"wrote {len(out)} bytes to {out_bin} "
          f"(json {len(a['json'])} -> {len(new_json)} bytes, CRC 0x{crc16(new_json):04x})")


def cmd_patch(path, key, value, apply_mode):
    with open(path, "rb") as f:
        buf = f.read()
    a = analyze(buf)
    calc = crc16(a["json"])
    if a["stored_crc"] != calc:
        sys.exit(f"stored CRC != computed CRC (0x{a['stored_crc']:04x} vs 0x{calc:04x}); "
                 "not touching the file")
    text = a["json"].decode("utf-8")
    m = re.search(r'"' + re.escape(key) + r'"\s*:\s*\d+(?:\.\d+)?', text)
    if not m:
        sys.exit(f"key '{key}' not found in JSON")
    old = m.group(0)
    new = re.sub(r"(\d+(?:\.\d+)?)$", str(value), old)
    print(f"found field : {old}")
    print(f"will change : {new}")
    if not apply_mode:
        print("\ndry-run only (no --apply). Re-run with --apply to write.")
        return
    new_text = text[:m.start()] + new + text[m.end():]
    out = pack(a["header"], new_text.encode("utf-8"), a["spare"])
    with open(path, "wb") as f:
        f.write(out)
    print(f"wrote {len(out)} bytes to {path} (CRC 0x{crc16(new_text.encode()):04x})")


USAGE = __doc__


def main():
    args = sys.argv[1:]
    if not args:
        print(USAGE)
        sys.exit(1)

    cmd = args[0]
    rest = args[1:]

    # Legacy: no subcommand, or subcommand looks like a file path.
    if cmd not in ("verify", "read", "write", "patch"):
        print(USAGE)
        sys.exit(1)

    if cmd == "verify":
        if len(rest) != 1:
            sys.exit("usage: verify <in.bin>")
        cmd_verify(rest[0])
        return

    if cmd == "read":
        if len(rest) != 2:
            sys.exit("usage: read <in.bin> <out.json>")
        cmd_read(rest[0], rest[1])
        return

    if cmd == "write":
        if len(rest) not in (2, 3):
            sys.exit("usage: write <template.bin> <in.json> [out.bin]")
        cmd_write(rest[0], rest[1], rest[2] if len(rest) == 3 else None)
        return

    # cmd == "patch"
    if len(rest) < 1:
        sys.exit("usage: patch <in.bin> [--key K] [--value V] [--apply]")
    path = rest[0]
    apply_mode = "--apply" in rest
    key = "aic_tlp_no_cap_pos"
    value = 0
    if "--key" in rest:
        key = rest[rest.index("--key") + 1]
    if "--value" in rest:
        value = rest[rest.index("--value") + 1]
    cmd_patch(path, key, value, apply_mode)


if __name__ == "__main__":
    main()
