"""Brain HTTP service (localhost only): behavior engine + capability policy.

GET  /health               -> {"status","behavior_state","avatar"}
GET  /commands?since=N     -> {"commands":[{"id",...validated message}]}
POST /event {"event":...}  -> runs behavior SM, queues avatar directives
POST /intent {"intent":...,"parameters":{...}} -> capability request verdict
"""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages"))
from behavior.engine import BehaviorEngine
from capability_policy.policy import CapabilityPolicy
from character_runtime.runtime import CharacterRuntime
from contracts.messages import validate_message
from neuro.motif import DriveNetwork, salience_for
from observability.log import log

HOST, PORT = "127.0.0.1", 8771
CHARACTER_PATH = os.environ.get("FRUIT_FLY_CHARACTER",
                                str(ROOT / "characters" / "furina.yaml"))


def load_persona() -> CharacterRuntime | None:
    try:
        return CharacterRuntime(CHARACTER_PATH)
    except (ValueError, OSError) as exc:
        log("brain", "WARN", f"character unavailable, persona disabled: {exc}")
        return None


class BrainState:
    def __init__(self):
        self.lock = threading.RLock()
        self.engine = BehaviorEngine()
        self.drives = DriveNetwork()
        self.policy = CapabilityPolicy()
        self.persona = load_persona()
        self.queue: list[dict] = []
        self.next_id = 1

    def persona_card(self) -> dict:
        if self.persona is None:
            return {"character": "none", "display_name": "Fruit-Fly"}
        data = self.persona.data
        return {"character": self.persona.id,
                "display_name": str(data.get("display_name", self.persona.id)),
                "tone": str(data.get("speech", {}).get("humor", "dry")),
                "greeting": str(data.get("speech", {}).get(
                    "greeting", "Hello."))}

    def push(self, msg: dict) -> None:
        ok, reason = validate_message(msg)
        if not ok:
            log("brain", "WARN", f"rejected outbound message: {reason}")
            return
        with self.lock:
            msg = dict(msg, id=self.next_id)
            self.next_id += 1
            self.queue.append(msg)

    def commands_since(self, since: int) -> list[dict]:
        with self.lock:
            return [m for m in self.queue if m["id"] > since]

    LOOK_TARGETS = {
        "LISTENING": {"x": 0.0, "y": 0.0},
        "SPEAKING": {"x": 0.15, "y": -0.05},
        "RESPONDING": {"x": -0.1, "y": 0.0},
    }

    def on_event(self, event: str) -> dict:
        with self.lock:
            state = self.engine.handle(event)
            out = self.engine.output()
            drive = self.drives.step(salience_for(event))
            self.push({"type": "avatar.state", "state": state})
            self.push({"type": "avatar.expression", "expression": out["expression"]})
            self.push({"type": "avatar.animation.play", "name": out["animation"], "loop": True})
            target = self.LOOK_TARGETS.get(state, {"x": 0.0, "y": 0.0})
            self.push({"type": "avatar.look_at", "x": target["x"], "y": target["y"]})
        log("brain", "INFO", f"event={event[:80]} state={state} drive={drive}")
        return {"behavior_state": state, "avatar": out, "drive": drive,
                "persona": self.persona_card()}

    def on_intent(self, intent: str, parameters: dict) -> dict:
        allowed, reason = self.policy.validate(intent, parameters or {})
        log("brain", "INFO" if allowed else "WARN",
            f"capability intent={str(intent)[:80]} allowed={allowed} reason={reason}")
        return {"intent": intent, "allowed": allowed, "reason": reason}


STATE = BrainState()


class Handler(BaseHTTPRequestHandler):
    server_version = "FruitFlyBrain/0.1"

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> tuple[dict, bool]:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0 or length > 65536:
            return {}, length == 0
        try:
            body = self.rfile.read(length) or b"{}"
        except OSError:
            return {}, False
        try:
            parsed = json.loads(body)
        except ValueError:
            return {}, False
        return parsed if isinstance(parsed, dict) else {}, isinstance(parsed, dict)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/health":
            self._json(200, {"status": "ok",
                             "behavior_state": STATE.engine.state,
                             "avatar": STATE.engine.output(),
                             "persona": STATE.persona_card()})
        elif url.path == "/commands":
            try:
                since = int(parse_qs(url.query).get("since", ["0"])[0] or 0)
            except ValueError:
                self._json(400, {"error": "since must be an integer"})
                return
            self._json(200, {"commands": STATE.commands_since(since)})
        else:
            self._json(404, {"error": "unknown endpoint"})

    def do_POST(self) -> None:
        body, ok = self._read_json()
        if not ok:
            self._json(400, {"error": "invalid JSON body"})
            return
        if self.path == "/event" and isinstance(body.get("event"), str):
            self._json(200, STATE.on_event(body["event"]))
        elif self.path == "/intent":
            self._json(200, STATE.on_intent(str(body.get("intent", "")),
                                            body.get("parameters", {})))
        else:
            self._json(404, {"error": "unknown endpoint"})

    def log_message(self, *args) -> None:  # keep stdout for payloads
        pass


def run(host: str = HOST, port: int = PORT) -> ThreadingHTTPServer:
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise ValueError("brain server binds loopback only")
    server = ThreadingHTTPServer((host, port), Handler)
    log("brain", "INFO", f"listening on {host}:{server.server_port}")
    return server


if __name__ == "__main__":
    run().serve_forever()
