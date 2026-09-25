"""Online gesture calibration: the control loop learns from undo patterns.

If the user fires gesture A and within seconds fires its opposite
(swipe_right then swipe_left, pinch twice), gesture A probably misfired, so
its swipe travel requirement grows (fewer accidental fires). Steady use
without undos relaxes it back. Persisted per-machine under configs/local/.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_DX = 0.12
DEFAULT_COOLDOWN = 1.2
DX_STEP = 0.02
DX_MAX = 0.22
COOLDOWN_STEP = 0.3
COOLDOWN_MAX = 3.0
ACCEPTS_TO_RELAX = 50
UNDO_WINDOW_S = 4.0

OPPOSITES = {
    "workspace.next": "workspace.previous",
    "workspace.previous": "workspace.next",
    "scroll.page:up": "scroll.page:down",
    "scroll.page:down": "scroll.page:up",
    "media.play_pause": "media.play_pause",
}

DEFAULT_PATH = Path("configs/local/gesture_calibration.json")


def intent_key(intent: str, params: dict) -> str:
    if intent == "scroll.page":
        return f"scroll.page:{params.get('direction', '')}"
    return intent


def detect_undo(last: tuple | None, intent: str, params: dict, now: float) -> str | None:
    """Return the earlier gesture if this fire undoes it, else None.
    last = (gesture, intent_key, timestamp)."""
    if last is None:
        return None
    gesture, key, stamp = last
    if now - stamp > UNDO_WINDOW_S:
        return None
    if OPPOSITES.get(intent_key(intent, params)) == key:
        return gesture
    return None


class Calibration:
    def __init__(self, path: Path | str = DEFAULT_PATH):
        self.path = Path(path)
        self.dx = DEFAULT_DX
        self.cooldown = DEFAULT_COOLDOWN
        self.accepts = 0
        self.undos = 0
        self.load()

    def load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(data, dict):
            self.dx = min(max(float(data.get("dx", self.dx)), DEFAULT_DX), DX_MAX)
            self.cooldown = min(max(float(data.get("cooldown", self.cooldown)),
                                    DEFAULT_COOLDOWN), COOLDOWN_MAX)
            self.accepts = int(data.get("accepts", 0))
            self.undos = int(data.get("undos", 0))

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({
                "dx": self.dx, "cooldown": self.cooldown,
                "accepts": self.accepts, "undos": self.undos,
            }), encoding="utf-8")
        except OSError:
            pass

    def record_accept(self) -> None:
        self.accepts += 1
        if self.accepts % ACCEPTS_TO_RELAX == 0:
            self.dx = max(DEFAULT_DX, self.dx - DX_STEP / 2)
            self.cooldown = max(DEFAULT_COOLDOWN, self.cooldown - COOLDOWN_STEP / 2)

    def record_undo(self) -> None:
        self.undos += 1
        self.dx = min(DX_MAX, self.dx + DX_STEP)
        self.cooldown = min(COOLDOWN_MAX, self.cooldown + COOLDOWN_STEP)
