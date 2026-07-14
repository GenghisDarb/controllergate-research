from __future__ import annotations

import re


FRAME = re.compile(r'File "([^"]+)", line (\d+), in ([^\n]+)')


def call_graph(traceback_text: str) -> dict[str, object]:
    frames = [{"path": p, "line": int(line), "symbol": symbol.strip()} for p, line, symbol in FRAME.findall(traceback_text)]
    return {"status": "PASS" if frames else "BLOCK", "frames": frames,
            "edges": [{"from": frames[i]["symbol"], "to": frames[i + 1]["symbol"]} for i in range(len(frames) - 1)]}
