"""Peripheral interfaces: voice, vision, memory. Mocks only — real inference
is a future milestone. Events produced here flow through the behavior engine.
"""
from __future__ import annotations


class VoiceProvider:
    name = "mock"

    def listen_once(self) -> dict:
        return {"type": "system.event", "event": "user_started_speaking",
                "data": {"provider": self.name, "simulated": True}}

    def speak(self, text: str) -> dict:
        return {"spoken": False, "provider": self.name,
                "note": "mock: no audio output; text retained", "text": text[:200]}


class VisionProvider:
    name = "mock"

    def poll(self) -> list[dict]:
        return []

    @staticmethod
    def gesture_event(gesture: str, confidence: float) -> dict:
        return {"type": "system.event", "event": "gesture",
                "data": {"gesture": gesture,
                         "confidence": max(0.0, min(1.0, confidence))}}


class SessionMemory:
    """Ephemeral session context + persistent preferences file (no vectors)."""

    def __init__(self):
        self.turns: list[dict] = []
        self.preferences: dict = {}

    def add_turn(self, role: str, text: str) -> None:
        self.turns.append({"role": role, "text": text[:500]})
        self.turns = self.turns[-20:]

    def set_preference(self, key: str, value: str) -> None:
        self.preferences[str(key)] = str(value)[:200]
