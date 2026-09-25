"""Renderer-independent character runtime.

Loads character YAML, tracks avatar state, holds expression/look-at targets,
and exposes procedural-idle parameters as data (the renderer interprets them;
this package never imports a renderer). Requires pyyaml on the target.
"""
from __future__ import annotations

import math
from pathlib import Path

import yaml

from contracts.messages import AVATAR_STATES

REQUIRED_TOP = ("id", "model", "personality")


class CharacterRuntime:
    def __init__(self, character_path: str | Path):
        path = Path(character_path)
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ValueError(f"cannot read character file {path}: {exc}") from exc
        except yaml.YAMLError as exc:
            raise ValueError(f"invalid YAML in {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("character file must be a mapping")
        for key in REQUIRED_TOP:
            if key not in data:
                raise ValueError(f"character file missing section: {key}")
        self.data = data
        self.state = "BOOT"
        self.expression = {"expression": "neutral", "intensity": 0.7}
        self.look_at = {"x": 0.0, "y": 0.0}
        self.animation = {"name": "idle", "loop": True}

    @property
    def id(self) -> str:
        return str(self.data.get("id", "unknown"))

    def set_state(self, state: str) -> str:
        if state not in AVATAR_STATES:
            raise ValueError(f"unknown avatar state: {state!r}")
        self.state = state
        return self.state

    def set_expression(self, expression: str, intensity: float = 0.7) -> dict:
        known = self.data.get("expressions")
        if isinstance(known, dict) and expression not in known:
            raise ValueError(f"unknown expression for {self.id}: {expression!r}")
        if not 0.0 <= intensity <= 1.0:
            raise ValueError("intensity must be within [0, 1]")
        self.expression = {"expression": expression, "intensity": intensity}
        return dict(self.expression)

    def set_look_at(self, x: float, y: float) -> dict:
        self.look_at = {"x": max(-1.0, min(1.0, x)),
                        "y": max(-1.0, min(1.0, y))}
        return dict(self.look_at)

    @staticmethod
    def _num(cfg: dict, key: str, default: float) -> float:
        try:
            value = float(cfg.get(key, default))
        except (TypeError, ValueError):
            return default
        return value if value == value and abs(value) != float("inf") else default

    def idle_pose(self, t: float) -> dict:
        """Procedural fallback idle as data: breath, sway, blink phase."""
        cfg = self.data.get("procedural_idle", {})
        if not isinstance(cfg, dict):
            cfg = {}
        breath = self._num(cfg, "breath_amplitude", 0.02)
        sway = self._num(cfg, "sway_amplitude", 0.03)
        rate = self._num(cfg, "breath_rate_hz", 0.25)
        return {
            "breath": breath * math.sin(2 * math.pi * rate * t),
            "sway": sway * math.sin(2 * math.pi * rate * t / 2),
            "blink_phase": (t % 4.0) / 4.0,
        }

    def personality_directive(self, behavior_output: dict) -> dict:
        """Merge personality traits with a behavior-engine output."""
        traits = self.data.get("personality", {})
        return {"character": self.id, "display_name": str(self.data.get("display_name", self.id)),
                "traits": dict(traits),
                "behavior": dict(behavior_output),
                "expression": dict(self.expression)}
