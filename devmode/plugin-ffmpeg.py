import subprocess
import threading
import time

RTSP_URL = "rtsp://127.0.0.1:554/video"

_proc = None
_recording = False
_lock = threading.Lock()


def _timestamp_ns():
    return int(time.monotonic() * 1000000000)


def _output_path():
    return f"ffmpeg-{_timestamp_ns()}.mkv"


def _proc_alive(proc):
    return proc is not None and proc.poll() is None


def _start_ffmpeg(ctx):
    global _proc
    if _proc_alive(_proc):
        return
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-rtsp_transport",
        "udp",
        "-i",
        RTSP_URL,
        "-c",
        "copy",
        _output_path(),
    ]
    try:
        _proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        _proc = None
        ctx.log(f"ffmpeg start failed err={exc}")
        return
    ctx.log(f"ffmpeg started pid={_proc.pid} file={cmd[-1]}")


def _wait_for_exit(proc, ctx):
    try:
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=2)
        except Exception:
            pass
    if ctx is not None:
        ctx.log(f"ffmpeg stopped pid={proc.pid}")


def _stop_ffmpeg(ctx):
    global _proc
    if not _proc_alive(_proc):
        _proc = None
        return
    proc = _proc
    _proc = None
    try:
        proc.terminate()
    except Exception:
        pass
    threading.Thread(target=_wait_for_exit, args=(proc, ctx), daemon=True).start()


def _recording_active(ctx):
    values = []
    for key in ("printing_sync_mode", "printing_level_mode", "lattice_busy"):
        val = ctx[key]
        if val is not None:
            values.append(val)
    if not values:
        return False
    for val in values:
        try:
            if int(val) != 0:
                return True
        except Exception:
            if val:
                return True
    return False


def _update_recording(ctx, _payload=None):
    global _recording
    with _lock:
        active = _recording_active(ctx)
        if active and not _recording:
            _recording = True
            _start_ffmpeg(ctx)
        elif not active and _recording:
            _recording = False
            _stop_ffmpeg(ctx)


def plugin_load(ctx):
    for event in ("printing", "printing_busy", "printer"):
        if event in ctx.events():
            ctx.on(event, _update_recording)
    ctx.log("ffmpeg plugin loaded")


def plugin_unload(ctx):
    global _recording
    with _lock:
        _recording = False
    _stop_ffmpeg(ctx)
