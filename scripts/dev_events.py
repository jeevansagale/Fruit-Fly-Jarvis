#!/usr/bin/env python3
"""Dev event feed: drives the brain through a full slice conversation."""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8771"


def post(path: str, obj: dict) -> dict | None:
    req = urllib.request.Request(BASE + path, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.load(resp)
    except urllib.error.URLError as exc:
        print(f"dev_events: brain unreachable at {BASE}: {exc}", file=sys.stderr)
        return None


def main() -> int:
    # Two tool_finished events: RESPONDING->SPEAKING, then SPEAKING->IDLE.
    for event in ("user_started_speaking", "user_stopped_speaking",
                  "brain_response", "tool_finished", "tool_finished"):
        result = post("/event", {"event": event})
        if result is None:
            return 1
        print(result)
        time.sleep(0.3)
    for intent, params in (("workspace.next", {}),
                           ("app.launch", {"app": "firefox"}),
                           ("shell.exec", {})):
        result = post("/intent", {"intent": intent, "parameters": params})
        if result is None:
            return 1
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
