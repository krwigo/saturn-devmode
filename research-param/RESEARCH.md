# AGENTS.md — chitu-16K-V1.5.6B workspace

Firmware extracted from an **Elegoo Saturn 4 Ultra 16K 3D SLA (resin) printer**.
The `chitu` binary is the main ARM application on the Chitu 16K board.

## The chitu binary

- Path: `chitu` (IDB files `chitu.id0/.id1/.id2/.nam` + `chitu.til` in this dir)
- Format: 32-bit **ARM Linux ELF**, dynamically linked, glibc, PIE, base `0x10000`
- File size `0x2c6014`, image size `0x3d23dc`
- MD5 `e2510b7c0849830e349439cae83d2080`, SHA256 `08dc533a20397ec19494e4500ca4173fdd3040cf31f1c03d735325b9789e9d94`
- Entry: `start` @ `0x18970` (crt → `__libc_start_main`)
- Scale: **7,497 functions**, 8,015 strings, symbols mostly stripped (imports intact)

### Segments

| Segment | Range | Notes |
|---|---|---|
| `.text` | `0x186c0`–`0x20d324` | all code (r-x) |
| `.rodata` | `0x20d330`–`0x2b4a22` | strings, const data |
| `.ARM.extab/.exidx` | `0x2b4a24`–`0x2c1648` | C++ EH (ARM) |
| `.data.rel.ro` | `0x2d16a0`–`0x2deda4` | pointer tables |
| `.got` / `.data` | `0x2df000`–`0x2e5954` | |
| `.bss` | `0x2e5958`–`0x3e1d04` | **SEG_BSS, not file-backed — IDA shows 0xFF; runtime zero-filled** |
| `extern` | `0x3e1d08`–`0x3e23dc` | dynamic symbols |

Important: the whole **param block lives in .bss at `0x39FA30`–`0x39FE40`**
(all `flt_39F*`/`dword_39F*` globals). IDA's displayed values (0xFF/NaN) are
meaningless — values are loaded at runtime (see below).

### Key libraries (imports)

FFmpeg (avformat/avcodec/avutil/swscale 58/56) — camera + mp4 muxing;
libcurl — HTTP; OpenSSL 1.1 — TLS/MD5/SHA256/RSA (`RSA_sign` +
`PEM_read_bio_RSAPrivateKey` = device signing); libpng, libjpeg-turbo,
FreeType (display UI); libnl — link monitoring; `wpa_ctrl` — WiFi control;
miniz (`mz_zip_*`) — OTA packages; **Agora RTC** (`argus_lbs`,
`report-*.agora.io`) — cloud live view.

### What this binary does

- Talks to the MCU over serial (SDCP protocol, `sdcp_v3_*`); MCU runs the
  motion firmware. This ARM app is the "brain": UI, cloud, camera, printing.
- USB OTA upgrade flow: `ChituUpgrade.bin`, `ChituFPGA.bin`, `ChituEDP.bin`,
  `ChituGcode.gcode`; factory mode via `/etc/fw_printenv | grep chitu_factory_mode=1`
- Cloud: ChituBox MMS endpoints (`https://mms.chitubox.com`, `https://mms.chituiot.com`,
  `https://cbdss-chitucloud-mms-stg1.chuangbide.com`), device info reporting
- HTTP server + RTSP server (`rtsp://%s:%d/video`) for camera streaming
- V4L2 camera capture (`/sys/class/video4linux`), MJPEG → time-lapse pipeline

## Camera / time-lapse (tlp) task

The "video recording" feature is the **AI-camera time-lapse** (`aic_tlp`):
camera MJPEG frames are captured per-layer, encoded (H.264 ultrafast, 30fps)
into an mp4 on the SD card (`/media/mmcblk0p2/`, `.mp4.tmp` → `.mp4`),
then uploaded to cloud (`/elegoo/printer/upload/tlp`).

Key globals / functions:

- `dword_2FA0C0` = tlp_capture flag (set by `sub_51458`, "tlp_capture %d")
- `dword_2FA0C4`/`dword_2FA0CC` = pending frame / snapshot-mode flags
- `dword_2FA0D0`/`dword_2FA0D8` = last snapshot timestamps; `dword_39FC90/39FC94` = interval thresholds
- `dword_2FA11C` = file-mode flag; `dword_2FA120` = frame queue
- `sub_51660` — MJPEG frame handler: scans for JPEG EOI (FFD9), queues frame; snapshot gating by interval
  - Two modes, both feed the same mp4 queue (`sub_E7F58(dword_2FA120,…)`):
    - **Per-layer** (`dword_2FA0C4` set by `sub_51458`): one frame captured per
      trigger layer (cadence = `aic_tlp_interval_layers`). This is the real
      time-lapse — **one still per print layer**, not a continuous video.
    - **Snapshot** (`dword_2FA0CC`): continuous-mode gating —
      `if (now - last_snap < aic_tlp_snapshot_time(=10000)) skip;` and
      `if (now - last_snap2 >= aic_tlp_snapshot_int(=70)) take snapshot`.
      So `snapshot_time`/`snapshot_int` throttle the snapshot path's capture
      rate; they are **not** the mp4 frame rate.
  - mp4 output is always H.264 @ fixed 30 fps (set in `sub_522A4`
      `tlp_create_mp4`) — the framerate is fixed regardless of these params.
- `sub_51514` — writes JPEG to per-layer file (`new/%08x`)
- `sub_510E8` — encodes queued frame to mp4 (`avcodec_send_frame` → `av_write_frame`)
- `sub_522A4` — `tlp_create_mp4`: opens mp4 (avformat, h264, preset ultrafast)
- `sub_5281C` — `mp4_handle_routine` (worker thread, created by `sub_E7464` in `sub_51CD8`)
- `sub_51CD8` — tlp engine init: mountpoint, cleanup of old mp4s
  (keeps ≤20 files, ≤0xC8=200MB), starts worker
- `sub_51398` — "tlp switch init"
- `sub_51458` — `tlp_capture` setter: sets `dword_2FA0C0=arg; dword_2FA0C4=1`
  (no direct callers — invoked via callback/function pointer)

### Param block (`0x39FA30`–`0x39FE40`, .bss)

Populated at runtime by:

- `sub_66EAC` (`mp_load`) — reads the **param_ref** file (CRC-checked),
  parses into struct, copies the whole block into `0x39FA30`+
- `sub_655A8` — copies block into live config struct at `0x34A6C0`+
  (`sub_655A8` is called from `sub_66EAC` after CRC check)
- `sub_6B3F8` — second loader (same writes)
- `sub_B7E94` — SDCP/JSON handler: `byte_39FC80 = json["Enable"] != 0`
  (tlp on/off from ChituBox app/cloud), then persists via `sub_68824`

### The 5 cm recording limit (target of the patch task)

Config keys in `.rodata` (no code xrefs — matched by name at runtime by the
param framework): `aic_tlp_switch` (0x213190), `aic_tlp_no_cap_pos` (0x2131a0),
`aic_tlp_start_cap_pos` (0x2131b4), `aic_tlp_interval_layers` (0x2131cc),
`aic_tlp_snapshot_time` (0x2131e4), `aic_tlp_snapshot_int` (0x2131fc).
SDCP/HTTP field names: `TLPNoCapPos`, `TLPStartCapPos`, `TLPInterLayers`.

The gate is in `sub_4345C` (app_print start/resume handler):

```
byte_39FC80 = tlp_switch (0/1)
flt_39FC84  = no_cap_pos (mm) — the ~5 cm (50 mm) limit
flt_39FC7C  = start_cap_pos (mm)
```

```c
if ( byte_39FC80 == 1 && flt_39FC84 < (float)total_layers * layer_height )
    → tlp switch init (sub_51398) → recording enabled
else
    → no recording
```

Observed symptom: with the stock `no_cap_pos` ≈ 50 mm, prints shorter than
~5 cm of total height never record. Semantically the field means "only
record if the print is taller than this" (a storage-saving default).

**CONFIRMED (decompile, lines 541-542):** the switch and the height limit are
ANDed into ONE condition — the `.ctb`/export sets `byte_39FC80=1`, but a short
print still fails the `&&` on the height term, so TLP is never initialized.
This is the "enabled in the .ctb but never records" bug. The `BPL` @ `0x44b5c`
is the compiled height term; the switch term is tested earlier and merges into
the same skip.

**`no_cap_pos` vs `start_cap_pos` — do not confuse them:**
- `flt_39FC84` (`aic_tlp_no_cap_pos`) = **print-start height gate** (the 5 cm
  blocker). Checked once in `sub_4345C` @ `0x44b5c`. This is what to patch.
- `flt_39FC7C` (`aic_tlp_start_cap_pos`) = **per-layer "start capture" Z
  position**, read in `sub_3F7F0` @ `0x3fe60`. One-shot: when Z crosses it it
  fires `sub_7FBB0` (trigger) then falls through. It is a "when to begin"
  parameter, NOT a cutoff — it does not block recording.
- `sub_51398` (tlp switch init) is clean: `v2[0]=1; strncpy(dest,src,0x400);
  return sub_E7F58(dword_2FA120,v2);` — no height gate inside.

Exact assembly (the patch target):

```
44b40  VLDR   S14, [R6,#(flt_39FC84 - 0x39FA30)]  ; S14 = no_cap_pos
44b44  VLDR   S15, [R2,#0xC]                     ; S15 = total_layers (u32)
44b48  VLDR   S13, [R2,#8]                       ; S13 = layer_height (f32)
44b4c  VCVT.F32.U32 S15, S15
44b50  VMUL.F32 S15, S15, S13                    ; S15 = total height (mm)
44b54  VCMPE.F32 S14, S15                        ; no_cap_pos < total_height?
44b58  VMRS   APSR_nzcv, FPSCR
44b5c  BPL    loc_43F0C                          ; if S14 >= S15 → skip TLP
```

To "always record": make the condition always true — e.g. patch the `BPL`
at `0x44b5c` to NOP (0xDEADBEEF) or to an unconditional `B` into the TLP-init
path, **or** force `byte_39FC80` handling so the whole `if` is bypassed.
Note `BPL` here means "S14 >= S15 or unordered → fall out (skip recording)".

**Patch plan (agreed target):**
1. Primary: `ida_patch` NOP (`DE AD BE EF`) at `0x44b5c` — the height check
   never skips TLP; `byte_39FC80` (user switch) still gates, which is desired.
2. `sub_51398` (tlp switch init) has exactly one caller: `sub_4345C` @ `0x44bac`
   (the `BL` inside the gated block) — no second gate there.
3. Per-layer capture trigger (separate from the gate): `sub_3F7F0`
   (app_print layer-progress handler) at `0x40bc4` calls `sub_51458`
   (`tlp_capture`); cadence from `dword_39FC8C` (`aic_tlp_interval_layers`),
   plus a "layer 1st capture" path (log `"layer 1st capture : %d\n"`).
4. Alternative without code patch: set `aic_tlp_no_cap_pos` = 0 in the
   param_ref file / slicer export so `0 < total_height` is trivially true.

Caveat: the 50 mm value itself is NOT a constant in the binary — it comes
from the param_ref file / slicer settings at runtime, so patch the branch,
not a data constant.

### Exact patch bytes (for the boot script)

`chitu` is **PIE, base `0x10000`** → file offset = VA − 0x10000.

- Target: `BPL` @ VA `0x44b5c` → file offset `0x34b5c`
- Original 4 bytes (LE): `EA FC FF 5A`
- Patch (ARM NOP = `0xE320F000`, LE bytes): `00 F0 20 E3`
- 20-byte unique anchor @ file offset `0x34b50`:
  `A6 7A 67 EE E7 7A B4 EE 10 FA F1 EE EA FC FF 5A 10 30 8D E5`
  (VMUL / VCMPE / VMRS / **BPL** / STR — the script should match this whole
  window, then overwrite only the middle 4 BPL bytes with the NOP.)
- **VERIFIED on disk** (`xxd`): file offset `0x34b50` = `a67a67eee77ab4ee10faf1eeeafcff5a10308de5`.
  - The BPL word is anchor bytes 12–15 (file offset `0x34b5c`): `EA FC FF 5A`.
  - Both the 20-byte anchor and the 4-byte BPL word are **unique** in the
    binary (grep over `xxd -p` → count 1 each). NOP word `00 F0 20 E3`
    already occurs 111× (existing NOPs) — fine.
  - Boot script: search for the 20-byte anchor, then replace its bytes
    12–15 (`EA FC FF 5A`) with `00 F0 20 E3` (NOP). Do NOT rely on the bare
    4-byte word alone even though it is currently unique — the full anchor
    is self-documenting and robust to a future firmware bump.

Effect: `no_cap_pos < total_height` is no longer required; TLP init depends
only on the user switch `byte_39FC80`. The 5 cm default (and any slicer/
param_ref value) can no longer suppress recording.

Note on the `param_ref` path (why we do NOT edit the data file): `sub_66EAC`
(`mp_load`) does `fopen64(param_ref,"rb")`, `fread(0x2800)`, verifies a CRC
("crc failed" on mismatch → keeps defaults), then `sub_C89D0` parses into
`unk_34A6C0` and copies the block (incl. `byte_39FC80`/`flt_39FC7C`/
`qword_39FC84`) into BSS. Editing `param_ref` means reversing the format +
recomputing its CRC — strictly more fragile than the 4-byte branch NOP.

### Where the param file actually lives (boot flow `sub_682F4`)

- Base dir resolved by `sub_D6D40(1,0,...)` → `/media/<dev>` (device id 1).
  **CONFIRMED on the device: device id 1 = `mmcblk0p1` = INTERNAL memory
  partition, NOT the removable SD.** So the files are at
  `/media/mmcblk0p1/`:
  - `machine_info.bin` (~344 KB)
  - **`machine_param_ref.bin`** (4910 bytes) — the param_ref blob
  - `ui_param_ref.bin` (1237 bytes)
  - (`machine_param.bin`/`ui_param.bin` appear transiently, then are removed.)
- Files (all under that base, logged under tag `"params"`):
  - `machine_param.bin` — user/OTA-applied params; **loaded then `remove()`d**
    after use (one-shot).
  - **`machine_param_ref.bin`** — the persistent CRC'd param_ref blob that
    `mp_load` reads. **This is the file holding the `no_cap_pos` default.**
  - `ui_param.bin` / `ui_param_ref.bin` — UI params (separate block).
  - `machine_info.bin` — machine info (name "Saturn 4 Ultra 16K").
- Boot order: load `machine_param.bin` (or built-in defaults) → delete it →
  `mp_load(machine_param_ref.bin)` overwrites the block → if the `_ref` is
  missing/invalid, `sub_66D4C` **writes** it (serializes current block via
  vtable `off_2E4EEC`, recomputes CRC, `fopen("wb+")`+`fsync`).
- **Built-in default `no_cap_pos` = 50.0 mm**, confirmed in rodata:
  `unk_2136D0 + 0x254` = `0x213924` = bytes `00 00 48 42` = float 50.0.

**Reference copies of the on-device files (downloaded for analysis):**
```
$(pwd)/mmcblk0-copy/media/mmcblk0p1/machine_param_ref.bin   (4910 B)  <- the editable param blob
$(pwd)/mmcblk0-copy/media/mmcblk0p1/ui_param_ref.bin        (1237 B)
$(pwd)/mmcblk0-copy/media/mmcblk0p1/machine_info.bin        (344280 B)
```
Verified: `patch-param.py` dry-run on the real `machine_param_ref.bin`
→ JSON @ 23..4904 (4882 B), stored CRC `0xdfee` == computed (PASS).
On-device values (Dec 31 snapshot):
```
aic_tlp_switch=1  aic_tlp_no_cap_pos=50  aic_tlp_start_cap_pos=30
aic_tlp_interval_layers=10  aic_tlp_snapshot_time=10000  aic_tlp_snapshot_int=70
z_home_move_to_zero=0       x_home_move_to_zero=1
```
(`z_home=0` / `x_home=1` explains the "Z retracts ~50% but X fully homes" symptom.)
### `machine_param_ref.bin` format (CONFIRMED from on-device file)

The file is **TLV-wrapped JSON**, NOT an opaque blob. Layout (4910 B example):

```
0x00  00 01 94            header (magic/version/flags)
0x03  FF × 15             padding
0x14  25                  '%' marker
0x15  7B …                JSON object (the machine params) — 4882 bytes here
…
end-7  00 02 02           (0,2) tag + len 2
end-5  10 E5              16-bit CRC (of the JSON payload), little-endian
end  +2 spare bytes
```

**Payload size is the key fact:** the CRC covers a **4882-byte** JSON that
starts at `0x15`. (The on-device stored CRC for that payload is `0xE510`.)

- The body is a **TLV stream** parsed by `sub_D1F6C`: each record is
  `[tag_hi, tag_lo, length, payload]`; the length byte uses high-bit encoding
  (bit7 set → next `len-128` bytes are the real length sum).
  - tag **(0,1)** = the JSON payload  (descriptor at `0x212588` = bytes `00 01`)
  - tag **(0,2)** = the 2-byte CRC     (descriptor at `0x21258C` = bytes `00 02`)
- `mp_load` (`sub_66EAC`) CRC-checks: `sub_C7364(json)` must equal the stored
  CRC field, else "crc failed" → keeps defaults and the file is ignored.
- Descriptor table `off_2DFB10` (array of ptrs to 2-byte tags) drives which
  TLV fields are recognized; unknown tags are skipped.

**The (0,1) var-length field MUST equal the JSON length (gotcha, hit on device).**
The (0,1) record's length field is a **20-byte sum** at file offsets `0x03..0x16`
(offset `0x02` = `0x94` = "20 length bytes"; `{` starts at `0x17`). The firmware
(`sub_D1F6C`) sums those 20 bytes → `v9`, then `malloc(v9)` + `memcpy(v9 bytes)`.
So **the 20 bytes must sum to the actual JSON payload length**, or the firmware
reads the wrong number of bytes (overshoots into the CRC record) and the whole
load fails → `sub_66D4C` **rewrites the file from factory defaults at boot**.
Firmware writer convention: `19×0xFF` + remainder in the last byte, e.g.
4882 = `19×0xFF + 0x25`, 4860 = `19×0xFF + 0x0F`. **If you change the JSON length,
you MUST update byte `0x16` (and friends) to keep the sum correct** — recomputing
only the trailing CRC is NOT enough. (`patch-param.py` now does this in
`pack()`; `verify` checks declared-vs-actual length.)

**TLP JSON key → BSS global map** (this is how the file drives the gate).
BSS offsets confirmed from the descriptor table (32-byte entries in `.data`
`~0x2e0bc4`: `[flag, key_ptr, struct_off, type, 3, default_ptr, 0, 0]`):

| JSON key | struct_off | BSS global | type | Role |
|---|---|---|---|---|
| `aic_tlp_switch` | 0x1F8 | `byte_39FC80` | byte | on/off (the `.ctb` "Enable" sets this too) |
| `aic_tlp_no_cap_pos` | 0x200 | `flt_39FC84` | float | **print-start height gate** (the 5 cm blocker, in `sub_4345C`) |
| `aic_tlp_start_cap_pos` | 0x208 | `flt_39FC88` | float | **per-layer capture threshold** (mm of build height) |
| `aic_tlp_interval_layers` | 0x210 | `dword_39FC8C` | u32 | capture cadence (every N layers) |
| `aic_tlp_snapshot_time` | 0x214 | `dword_39FC90` | u32 | **HARD CAP (ms) on total retract/snapshot capture duration** — at this age the snapshot path stops (`dword_2FA0CC=0`). Default 10000. |
| `aic_tlp_snapshot_int` | 0x218 | `dword_39FC94` | u32 | **minimum spacing (ms)** between snapshot frames. Default 70. (Camera's ~100 ms cadence is the real rate.) |
| `z_home_move_to_zero` | 0x21C | `byte_39FC98` | byte | home-sequence flag (see below) |
| `x_home_move_to_zero` | 0x21D | `byte_39FC99` | byte | home-sequence flag (see below) |
| `aic_enable` / `aic_capture_position` | (AI-camera block) | | | camera enable / capture pos |

**TWO separate height gates — do not confuse them (root cause of the
"only recorded the 3 s retract" bug):**
1. **`no_cap_pos` (`flt_39FC84`)** — checked ONCE at print start in `sub_4345C`:
   `if (byte_39FC80 && flt_39FC84 < total_layers*layer_height) → tlp init`.
   This is the *boot/init* gate. Setting it to 0 makes TLP initialize.
2. **`start_cap_pos` (`flt_39FC88`)** — checked PER LAYER in `sub_3F7F0`:
   `if (byte_39FC80 && cur_layer*layer_height >= flt_39FC88) → capture every
   aic_tlp_interval_layers layers`. This is the *real time-lapse* gate.
   **If the print is shorter than `start_cap_pos` (mm), no per-layer frame is
   ever captured** — only the post-print retract path records (a few frames).
   For a ~4 mm print with the default `start_cap_pos=30`, the per-layer path
   never fires. **Set `start_cap_pos` to 0 (or below the print height) to get
   a real per-layer time-lapse on short prints.**

Note: an earlier note mapped `start_cap_pos` to `flt_39FC7C` — that was wrong;
the descriptor table puts it at struct_off 0x208 = BSS `flt_39FC88`.
`flt_39FC7C` (struct_off 0x1F0) is a *different* field (also loaded in mp_load).

**ON-DEVICE TEST RESULTS (2026-09-02/03) — why the video is "retract only, ~3 s":**

Two independent capture paths feed the ONE mp4 queue (`dword_2FA120`):

| Path | Trigger | Cadence | Thread (log) |
|---|---|---|---|
| **Per-layer** (`dword_2FA0C4`, set by `sub_51458` from `sub_3F7F0`) | every `aic_tlp_interval_layers` layers during the print | 1 frame / N layers | 567 |
| **Retract/snapshot** (`dword_2FA0CC`) | post-print retract + home | camera rate (~10 fps / ~100 ms), capped by `aic_tlp_snapshot_time` | 640 |

So a short print's mp4 = **few per-layer frames (the "8") + ~100 retract
frames (the "100")** = the "8+100" the user sees. The retract burst dominates
the short clip because the muxer plays everything back at a fixed rate.

Test `local_1` (params: `no_cap_pos=0`, `z_home=1`): TLP initialized, but
per-layer capture NEVER fired (print only ~4 mm tall < `start_cap_pos`=30 mm).
100 frames all from the post-print retract path → 3 s retract video.

Test `local_2` (params: `no_cap_pos=0`, `start_cap_pos=0`, `z_home=0`):
per-layer capture NOW FIRES, but the video is STILL mostly retract. Confirmed
frame accounting (mp4 `mvhd` duration = 3567 ms, `stts` = 108 samples):

| Path | Frames | Real capture span | Where in the 3.57 s mp4 |
|---|---|---|---|
| Per-layer (the real time-lapse, thread 567) | **8** (layers 0,10,20,30,40,50,60,70) | 285 s–1187 s (~15 min, ~145 s apart) | first ~0.3 s (too fast to see) |
| Retract/home burst (snapshot path, thread 640) | **100** | 1244 s–1254 s (a 9.8 s burst, ~100 ms apart) | last ~3.3 s (what you actually see) |

Test `local_3` (OLD param, `snapshot_time=10000` still in effect):
retract burst = **88 frames over 10.1 s** (4998281→5008407); Z retract ran
4997954→5019395 (**21.4 s**) but the last frame was at 5008407 (**10.5 s in,
Z≈51 mm, ~49% retracted**) — **still cuts off mid-retract**, confirming the
10 s `snapshot_time` cap is the blocker. User also saved the raw **720p
(1280×720) JPEG frames** (`frames/000000{6f..b2}.jpg`, 68 of them, indices
111–178) before H.264 encoding — they are ordinary valid JPEGs (nothing
special); they confirm the camera delivers ~10 fps of full-res stills during
the retract. mp4 = 98 frames / 3.23 s. **This run did NOT have the fix.**

Test `local_4` (FIXED param, `snapshot_time=45000`): **WORKS.**
mp4 = **226 frames / 7.50 s** (1280×720 H.264 @30 fps, 12.2 MB).
Retract burst = **216 frames over 21.3 s** (1505521→1526836, ~10.1 fps);
Z retract 1505140→1526578 (**21.4 s**); last frame at **1526836** = right as
the retract finishes, so the **object is visible** (the reveal is captured).
10 per-layer + 216 retract = 226.

**The ~7.5 s length and the "cuts off right after the retract" are BY DESIGN
(user accepted 2026-09-03):**
- Clip length = (frames captured) ÷ 30 fps. Frame count = real capture time ×
  camera rate (~10 fps). The retract is a fixed 21.4 s (160000 steps @ 8000),
  so it yields ~216 frames → ~7.2 s of playback. **There is no "duration"
  param** — `snapshot_time` is only a non-binding cap (already 45 s).
- Capture STOPS at **`tlp complte`**, logged in `sub_3F7F0`:
  `if ( v279 == 9 && dword_2EBA28 ) { log; sub_513DC(1); }` where
  `v279 = sub_7C90C(...)` = print state; **state 9 = retract/home complete**.
  `sub_513DC` sets `dword_2FA0CC=0` → stops the snapshot path. So the video
  ends exactly when the plate tops out — by design.
- To make it longer you'd need to keep the camera rolling *after* the retract
  (hold at top ~7 s for ~74 more frames → ~10 s), which is either a home/
  retract-sequence change or a small code patch — NOT a data param. Not done
  (out of scope / accepted as-is).

**WHY THE VIDEO CUTS OFF MID-RETRACT (the real bug) — ROOT CAUSE + FIX:**

The user's actual complaint: *the video ends before the build plate finishes
retracting, so the printed object is never seen.*

`local_2` axis timeline (the Z retract is the "reveal"):
```
1241353  X (axis 1) -> 140        (X swings out of the way)
1243778  Z (axis 0) -> 100.0      (FULL retract, 160000 steps @ ~7980)
1265219  axis 0 is idle           (Z reaches 100.0 = TOP, object revealed)
1265260  tlp complte              (TLP stops here)
```
The Z retract takes **21.4 s** (1243778→1265219). But the **last captured frame
was at 1254109** = only **10.3 s** into the retract, at an estimated **Z≈50 mm
(~48% retracted)**. The plate never reaches the top in the video.

**Root cause (assembly-confirmed, `sub_51660` snapshot path `@0x516c8`):**
```
now = D2EE0()
if (now - dword_2FA0D0) >= aic_tlp_snapshot_time (dword_39FC90, =10000):
    dword_2FA0CC = 0        # *** STOPS the snapshot/retract capture ***
    return
else:
    if (now - dword_2FA0D8) >= aic_tlp_snapshot_int (70):
        capture frame;  dword_2FA0D8 = now
```
**`aic_tlp_snapshot_time` (default 10000 = 10 s) is a HARD CAP on the total
retract/snapshot capture duration.** The retract takes 21.4 s, so the 10 s cap
cuts the video at Z≈50 mm. (The 100-frame burst = camera's ~10 fps for 10 s;
`snapshot_int`=70 ms is only a *minimum* spacing — the camera's ~100 ms cadence
is the real rate.)

**FIX (data-only, in the new `machine_param_ref.bin_patched`):**
- **`aic_tlp_snapshot_time` = 45000** (45 s) — was 10000. Covers the 21.4 s
  retract with ~2× margin (and taller/slower retracts). The snapshot path now
  runs until the retract completes.
- `tlp complte` (`sub_513DC`) fires when the Z axis goes idle (retract done)
  and sets `dword_2FA0CC=0`, so capture stops right as the plate tops out —
  the last frames show the **finished, revealed object**.
- Note: the mp4 muxer still stamps frames at a fixed rate (`sub_510E8`: frame
  PTS = `dword_2FA118` counter, not wall-clock), so the longer retract simply
  adds more frames to the clip; it does not change the 30 fps playback rate.

**Other levers (already applied or optional):**
- `aic_tlp_no_cap_pos`=0 (boot/init gate), `aic_tlp_start_cap_pos`=0 (per-layer
  gate on short prints) — both needed for capture to start.
- `aic_tlp_interval_layers` (default 10) = per-layer cadence; lower for a
  denser print time-lapse (e.g. 1 = every layer).
- `z_home_move_to_zero`/`x_home_move_to_zero` = home-sequence flags, NOT TLP;
  keep at stock (0 / 1). `z_home=1` was observed to break homing.

**FINAL `machine_param_ref.bin_patched` values (ready to test longer recording):**
```
aic_tlp_switch        = 1      (TLP enabled)
aic_tlp_no_cap_pos    = 0      (was 50)   boot/init height gate off
aic_tlp_start_cap_pos = 0      (was 30)   per-layer capture on for short prints
aic_tlp_interval_layers = 10   (default)  1 per-layer frame / 10 layers
aic_tlp_snapshot_time = 45000  (was 10000) THE FIX: retract capture 10s -> 45s
aic_tlp_snapshot_int  = 70     (default)  min snapshot spacing (ms)
z_home_move_to_zero   = 0      (stock)    keep — 1 broke homing
x_home_move_to_zero   = 1      (stock)
```

**Data flow / override caveat (RESOLVED):**
- `no_cap_pos` (`flt_39FC84`) is written ONLY by the param framework:
  `sub_66EAC` (mp_load, from `machine_param_ref.bin` at boot), `sub_655A8`
  (config copy), `sub_688A8` (save), and `sub_6B3F8` (serial **'M' machine-param
  message**, dispatched by `sub_6CCCC` on `*a1=='M'`).
- `tlp_switch` (`byte_39FC80`) is written by mp_load, `sub_6B3F8` (same 'M'
  path), and `sub_B7E94` (SDCP/JSON `"Enable"` field).
- **The `.ctb` print file does NOT write these TLP globals.** The `.ctb` parser
  only supplies print geometry (total_layers, layer_height) which the gate in
  `sub_4345C` compares *against*. So editing `machine_param_ref.bin` sets a
  value the `.ctb` will NOT override.
- Net: the only thing that can re-push `no_cap_pos` is an app/cloud serial 'M'
  machine-param message — not the slicer file. For normal `.ctb` prints, the
  `machine_param_ref.bin` value is authoritative.

**The TLP params are plain JSON keys** in that payload (on-device values):

```
"z_i_run":18,"aic_enable":1,"aic_capture_position":100,
"aic_tlp_switch":1,"aic_tlp_no_cap_pos":50,"aic_tlp_start_cap_pos":30,
"aic_tlp_interval_layers":10,"aic_tlp_snapshot_time":10000,
"aic_tlp_snapshot_int":70
```

So **`aic_tlp_no_cap_pos` = 50 (the 5 cm limit) is directly editable** — and
`aic_tlp_switch` is already `1` (enabled), confirming the ".ctb enables it"
hypothesis.

**Data-only fix (no binary patch):** change `"aic_tlp_no_cap_pos":50` → `0` in
`machine_param_ref.bin`, then recompute the trailing CRC and rewrite it.

**The CRC is NOT plain CRC-16/CCITT.** It is a faithful port of firmware
`sub_C7364`: each input byte is folded through a nibble-swap + bit-matrix
*before* the 0x1021 table lookup, and the 16-bit result is post-transformed.
Table `T16` is the standard CRC-16/CCITT-0x1021 table (`word_277998`).
**VERIFIED**: this implementation reproduces the on-device stored CRC for the
shipped 4910-byte file (stored `0xdfee` over the 4882-byte JSON payload → PASS).

```python
def crc16(data: bytes) -> int:
    crc = 0
    for b in data:
        v5 = (16 * b) | (b >> 4)                 # nibble swap
        v6 = (4 * v5) & 0xCC | (v5 >> 2) & 0x33
        idx = ((2 * v6) & 0xAA | (v6 >> 1) & 0x55) ^ (crc >> 8)
        crc = T16[idx] ^ ((crc << 8) & 0xFFFF)
    lo, hi = crc & 0xFF, (crc >> 8) & 0xFF
    def t(x): x &= 0xFF; r = ((x<<4)|(x>>4)) & 0xFF
              return ((4*r)&0xCC) | ((r>>2)&0x33)
    v8, v9 = t(lo), t(hi)
    return ((2 * v9 & 0xAA) | (v9 >> 1 & 0x55)) | (((2 * v8 & 0xAA) | (v8 >> 1 & 0x55)) << 8)
```

**Ready-to-use script: `patch-param.py`** (this directory). It
- locates the JSON by braces and the `(0,2)` CRC record by tag (robust to the
  quirky var-length header and the 2 spare trailing bytes),
- **verifies** `crc16(payload) == stored CRC` first and aborts on mismatch,
- rebuilds by splicing `[header][new JSON][00 02 02 newCRC][spare]` (header and
  spare preserved verbatim; only the JSON changes).

Four subcommands:
```
# 1) verify the stored CRC (safe, read-only)
python3 patch-param.py verify  <in.bin>

# 2) read  <in.bin> <out.json>      extract the JSON payload (pretty-printed)
# 3) write <template.bin> <in.json> [out.bin]   repack + recompute CRC
#       (out.bin optional -> in-place; template supplies header/spare)
python3 patch-param.py read   machine_param_ref.bin  params.json
#    ... edit params.json (any key, arrays, nested dicts) ...
python3 patch-param.py write  machine_param_ref.bin  params.json  machine_param_ref.new.bin

# 4) patch <in.bin> [--key K] [--value V] [--apply]   convenience: single
#    top-level scalar key, in-place, byte-minimal (no full re-serialize).
#    Default key aic_tlp_no_cap_pos, value 0; dry-run unless --apply.
python3 patch-param.py patch  machine_param_ref.bin --apply --key z_home_move_to_zero --value 1
```
`write` re-serializes the JSON compactly (`separators=(',',':')`, matching the
file's no-space style). This is value-safe: the firmware parses JSON to
float32/64 + checks the CRC, never compares raw bytes. The only cosmetic diff
is one float's 17th sig digit (`4.6367372913546363e+18`→`…36e+18`), which is
below float32 precision — the parsed value is identical. For a byte-minimal
edit (preserve every untouched byte), use `patch --key --value` instead.

### Post-print Z/X home ("retract") params — `z_home_move_to_zero` / `x_home_move_to_zero`

Machine params (same JSON payload / param framework as the TLP keys) that
control whether the axes **fully drive to position 0.0 after a home**, or stop
short. **CONFIRMED 0/1 flags (not a percentage)** by the home code:

| JSON key | BSS global | type | Meaning |
|---|---|---|---|
| `z_home_move_to_zero` | `byte_39FC98` | 1 byte | Z: after homing, drive all the way to 0.0 (full retract). `0` = stop short. |
| `x_home_move_to_zero` | `byte_39FC99` | 1 byte | X: after homing, drive all the way to 0.0 (full retract). `0` = stop short. |

Proof (assembly):
- Home sequence `sub_2D40C`:
  ```
  2dc00  LDRB R3,[byte_39FC98]   ; z_home_move_to_zero
  2dc04  CMP  R3,#0
  2dc08  BNE  loc_2DE08          ; set -> Z full-home-to-zero path
  ...  (else: normal home, sub_53774 — stops short)
  2dc1c  LDRB R3,[byte_39FC99]   ; x_home_move_to_zero
  2dc20  CMP  R3,#0
  2dc24  BEQ  loc_2D7D4          ; clear -> skip X move-to-zero
  2dc38  BL   sub_5361C          ; set  -> sub_5361C(1, 0.0, flt_39FAA8) : move X to 0.0
  ```
- SDCP home handler `sub_19AF8` (case 4, "axis_home(AXIS_X)") reads `byte_39FC99`
  at `0x19ddc` the same way.
- So the flag is a pure enable: `1` = the extra "move to 0.0" step runs (full
  retract home); `0` = that step is skipped (the "retracts ~50% but not fully"
  symptom). `sub_5361C(axis, 0.0, flt_39FAA8)` is the absolute move to zero.

**CAUTION (verified on device, 2026-09-02):** setting `z_home_move_to_zero=1`
routed the post-print home into a *different* path (`loc_2DE08`) and the
homing/retract behavior was observed to be **wrong** on the real machine. It is
a home-sequence flag, not a simple "retract fully" toggle — do NOT use it to
tweak retraction. Keep it at its stock value (0). The TLP recording is
controlled by the `aic_tlp_*` keys, not by these.

These live in `machine_param_ref.bin` (same param block `0x39FA30`–`0x39FE40`),
so they are editable the same data-only way as the TLP keys:
```
python3 patch-param.py /media/mmcblk0p1/machine_param_ref.bin --apply --key z_home_move_to_zero --value 1
```
(Descriptor table: 32-byte entries `[flag, key_ptr, struct_off, type, 3,
default_ptr, 0, 0]` in `.data` ~`0x2e0c84`; `z_home`/`x_home` are `type 1`.
Note the descriptor `struct_off` field does NOT map to a single clean base for
all keys — the authoritative BSS addresses are the code xrefs above, not the
descriptor offset.)

**Recommendation ranking:**
1. **Branch NOP in `chitu`** (4 bytes, verified unique anchor) — most robust,
   immune to any param file / slicer / cloud value. Requires reflashing.
2. **Edit `machine_param_ref.bin`** (`no_cap_pos`→0) + recompute CRC — no
   binary patch, but the value can be overwritten again by an OTA/param push,
   and you must get the CRC exactly right or the file is rejected.

Either is safe; pick #1 for permanence, #2 if you'd rather not touch the
firmware image.

### Print-file (`.ctb`/`.cbddlp`) → TLP params

- The TLP settings are NOT compile-time; they arrive with the job:
  - **param_ref file** (CRC-checked blob) parsed by `sub_66EAC` (`mp_load`)
    and `sub_6B3F8` → fills the `0x39FA30` block (incl. `byte_39FC80`,
    `flt_39FC7C/84`, `dword_39FC8C`).
  - **SDCP/JSON** message from app/cloud: `sub_B7E94` reads `"Enable"`
    → `byte_39FC80`; fields `TLPNoCapPos`/`TLPStartCapPos`/`TLPInterLayers`
    (0x276168–0x276184) and `TLPStatus`/`TLPPushed`/`TLPTime`/`TLPSize`
    (0x27427c–0x27434c) appear in status reports (`/elegoo/printer/upload/tlp`).
  - The `.ctb`/`.cbddlp` parsers (`sub_3F7F0` family, "ctb not support crc32"
    string at 0x26bc40) extract job params at print start (`sub_4345C` reads
    total layers @ `v188+12`, layer height @ `v188+8` from the job struct).
- Hypothesis to verify: if the slicer/export doesn't set `TLPNoCapPos`
  correctly, the firmware's default (param_ref) of ~50 mm applies and short
  prints never record. Inspect a `.ctb` from the slicer for the TLP block,
  and/or the param_ref file on the SD.

## MCP (IDA Pro) quirks — IMPORTANT

- **Array parameters get stringified.** Tools that accept `addrs`/`patterns`/
  `targets` as *array or single string* break when you pass a real JSON array:
  the whole array is stringified into one element
  (e.g. `addrs=["0x2131a0", ...]` → `Failed to parse address: ["0x2131a0"`).
  **Pass a single string** (e.g. `addrs="0x2131a0"`) and call the tool once
  per item.
- `ida_search` type=`immediate`: passing decimal integers misbehaved
  (searched for 0). Prefer `ida_find_insn_operands` with mnem/op filters, or
  `ida_find_bytes` with hex byte patterns (single string!).
- `ida_find_bytes` also stringifies arrays — one pattern per call.
- **`ida_find_bytes` returned 0 matches for byte patterns that verifiably
  exist** (confirmed via `ida_get_bytes` and on-disk `xxd`). Treat its results
  as unreliable in this session; fall back to dumping the binary with
  `xxd -p` + `grep -o -a <hex> | wc -l` for byte searches / uniqueness checks.
- `ida_py_eval` runs `eval()` then falls back to `exec()`:
  - multi-statement code fails `eval` (SyntaxError) and runs via `exec` — fine,
    but the *value* of the last expression is lost; use `print()`.
  - correct IDA 9.2 module/attr names: `ida_hexrays` (not `ida_hexrays_c`),
    `ida_xref` (not `ida_xrefs`), no `HexRana` module, `ida_lines.tag_remove`
    (not `tagremove`), `ida_segment.getseg(addr)`, `seg.align` (not `alignmt`),
    `seg.end_ea` exists but `ida_segment.getnseg(i)` is deprecated-ish.
  - `cfunc.get_pseudocode()` returns a **strvec_t of simpleline_t SWIG
    proxies** — `str()` of each proxy gives the repr, not the line. Easiest:
    use the MCP `ida_decompile` tool for clean pseudocode instead.
- Big tool outputs (function lists, disasm, large decompiles) are truncated
  to a file under `~/.local/share/opencode/tool-output/`; the file is a single
  giant JSON line. Grep it via the Grep tool with `include=<filename>` or
  parse with python (`json.load`, then inspect `d[0]['code']` /
  `d[0]['asm']['lines']` — note `lines` may be a **string**, not a list).
- `ida_list_funcs` with `count:0` returns everything (huge). Use filters or
  `ida_py_eval` with `idautils.Functions()` + `len()` for counts.
- Bash in this env is heavily permission-restricted: allowed ≈
  `ls, wc, head, tail, cat, rg, grep, sed, awk, xxd, curl, git, ...`;
  `file`, `readelf`, `python3` (generic) are denied/ask. Use IDA MCP +
  Read/Grep tools instead.
- Plan mode vs build mode: IDA tools are read-only for analysis;
  `ida_patch` / `ida_patch_asm` mutate the IDB (and `ida_dbg_write_mem`
  the live process) — only in build mode.

## Conventions

- Working dir: `/home/user/chitu-16K-V1.5.6B`
- Binary + IDB live in the working dir; IDA is already attached to this IDB.
- Log prefix convention in this firmware: `"aic_tlp"`, `"app_print"`,
  `"param_ref"`, `"hl_camera"` (source files: `ai_camera.c`,
  `hl/devices/hl_camera.c` — build path leaks:
  `/var/lib/jenkins/workspace/PPL_100-PACKAGE-FIRMWARE-CL103/...`)
