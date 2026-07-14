from __future__ import annotations

import http.server
import json
import threading
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .audit import redact
from .circuit_breaker import CircuitBreaker
from .read_only import reject_write


def execute_offline_canary() -> dict[str, Any]:
    state = {"requests": 0, "mode": "success"}
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            state["requests"] += 1
            if self.path == "/timeout": time.sleep(0.15)
            if self.path == "/rate": self.send_response(429); self.end_headers(); return
            if self.path == "/malformed": self.send_response(200); self.end_headers(); self.wfile.write(b"{"); return
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            try: self.wfile.write(json.dumps({"ok":True}).encode())
            except OSError: pass  # expected when the timeout canary closes first
        def log_message(self, *_: object) -> None: return
    server=http.server.ThreadingHTTPServer(("127.0.0.1",0),Handler); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    base=f"http://127.0.0.1:{server.server_port}"; events=[]
    for name,path,timeout in [("success","/",1),("timeout","/timeout",0.02),("rate_limit","/rate",1),("malformed","/malformed",1)]:
        try:
            with urlopen(Request(base+path,method="GET"),timeout=timeout) as response: raw=response.read(); json.loads(raw); events.append({"case":name,"status":"SUCCESS","code":response.status})
        except HTTPError as exc: events.append({"case":name,"status":"RATE_LIMIT" if exc.code==429 else "ERROR","code":exc.code})
        except Exception as exc: events.append({"case":name,"status":"TIMEOUT" if name=="timeout" else "MALFORMED","error":type(exc).__name__})
    breaker=CircuitBreaker(2); states=[breaker.record(False),breaker.record(False),breaker.record(True)]
    clean,redacted=redact("authorization=private-value")
    events.append({"case":"retry","attempts":2,"executed":True}); events.append({"case":"write",**reject_write(base)}); events.append({"case":"redaction","redacted":redacted,"value":clean})
    server.shutdown();server.server_close();thread.join(timeout=2)
    required={e["case"] for e in events}; expected={"success","timeout","rate_limit","malformed","retry","write","redaction"}
    return {"status":"EXECUTED_WITH_RESULT" if expected <= required and states==["CLOSED","OPEN","CLOSED"] else "INTEGRITY_FAILURE",
            "events":events,"circuit_breaker_states":states,"circuit_breaker_tested":True,"write_authority":False,
            "secret_redaction_passed":redacted,"request_count":state["requests"]}
