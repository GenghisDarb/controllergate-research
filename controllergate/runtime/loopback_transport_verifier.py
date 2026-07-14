from __future__ import annotations

import hashlib
import http.server
import threading
import urllib.request


def verify_loopback(payload: bytes = b"controllergate-loopback") -> dict[str, object]:
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200); self.end_headers(); self.wfile.write(payload)
        def log_message(self, *_: object) -> None:
            return
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.handle_request, daemon=True); thread.start()
    with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=3) as response:
        observed = response.read()
    thread.join(timeout=3); server.server_close()
    return {"status": "PASS" if observed == payload else "BLOCK", "server_address": "127.0.0.1",
            "payload_hash": hashlib.sha256(observed).hexdigest(), "same_process_namespace": True}
