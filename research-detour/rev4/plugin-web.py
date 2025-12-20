import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_ctx = None
_server = None
_thread = None
_latest_vat = None
_lock = threading.Lock()


def on_vat_temp(payload):
    global _latest_vat
    with _lock:
        _latest_vat = payload


class VatHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        if self.path != "/api/vat_temp":
            self.send_response(404)
            self.end_headers()
            return
        with _lock:
            payload = _latest_vat
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def plugin_load(ctx):
    global _ctx, _server, _thread
    _ctx = ctx
    ctx.on("vat_temp", on_vat_temp)
    _server = ThreadingHTTPServer(("0.0.0.0", 8000), VatHandler)
    _thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _thread.start()
    ctx.log("web listening on http://0.0.0.0:8000/api/vat_temp")


def plugin_unload(ctx):
    if _server is not None:
        _server.shutdown()
    if _ctx is not None:
        _ctx.log("web stopped")
