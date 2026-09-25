"""Deterministic behavior state machine. No LLM involved.

States: IDLE, LISTENING, THINKING, RESPONDING, SPEAKING, ERROR.
Outputs per state drive avatar expression/animation/overlay hints.
"""
from __future__ import annotations

STATES = ("IDLE", "LISTENING", "THINKING", "RESPONDING", "SPEAKING", "ERROR")

TRANSITIONS = {
    ("IDLE", "user_started_speaking"): "LISTENING",
    ("LISTENING", "user_stopped_speaking"): "THINKING",
    ("LISTENING", "user_started_speaking"): "LISTENING",
    ("THINKING", "brain_thinking"): "THINKING",
    ("THINKING", "brain_response"): "RESPONDING",
    ("RESPONDING", "tool_started"): "RESPONDING",
    ("RESPONDING", "tool_finished"): "SPEAKING",
    ("RESPONDING", "brain_response"): "SPEAKING",
    ("SPEAKING", "user_started_speaking"): "LISTENING",
    ("SPEAKING", "tool_finished"): "IDLE",
    ("IDLE", "system_error"): "ERROR",
    ("LISTENING", "system_error"): "ERROR",
    ("THINKING", "system_error"): "ERROR",
    ("RESPONDING", "system_error"): "ERROR",
    ("SPEAKING", "system_error"): "ERROR",
    ("ERROR", "reset"): "IDLE",
}

STATE_OUTPUT = {
    "IDLE": {"expression": "neutral", "animation": "idle", "overlay": "idle"},
    "LISTENING": {"expression": "attentive", "animation": "idle", "overlay": "listening"},
    "THINKING": {"expression": "focused", "animation": "idle", "overlay": "thinking"},
    "RESPONDING": {"expression": "neutral", "animation": "talk", "overlay": "working"},
    "SPEAKING": {"expression": "warm", "animation": "talk", "overlay": "speaking"},
    "ERROR": {"expression": "concerned", "animation": "idle", "overlay": "error"},
}


class BehaviorEngine:
    def __init__(self, initial: str = "IDLE"):
        if initial not in STATES:
            raise ValueError(f"unknown state: {initial!r}")
        self.state = initial

    def handle(self, event: str) -> str:
        """Apply event; unknown transitions leave state unchanged."""
        self.state = TRANSITIONS.get((self.state, event), self.state)
        return self.state

    def output(self) -> dict:
        return dict(STATE_OUTPUT[self.state])
