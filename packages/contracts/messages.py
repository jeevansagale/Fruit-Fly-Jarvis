"""Typed local IPC contracts. Dict-based, stdlib-only, no transport assumptions.

Every message is {"type": <str>, ...fields}. validate_message() enforces the
shape; unknown types and missing fields are rejected, never defaulted.
"""
from __future__ import annotations

SCHEMAS = {
    "avatar.animation.play": {"required": {"name": str}, "optional": {"loop": bool}},
    "avatar.expression": {"required": {"expression": str}, "optional": {"intensity": float}},
    "avatar.look_at": {"required": {"x": (int, float), "y": (int, float)}, "optional": {}},
    "avatar.state": {"required": {"state": str}, "optional": {"detail": str}},
    "brain.intent": {"required": {"intent": str}, "optional": {"parameters": dict}},
    "capability.request": {"required": {"capability": str}, "optional": {"parameters": dict}},
    "capability.result": {"required": {"ok": bool}, "optional": {"detail": str}},
    "system.event": {"required": {"event": str}, "optional": {"data": dict}},
}

AVATAR_STATES = {"BOOT", "LOADING", "IDLE", "LISTENING", "THINKING",
                 "RESPONDING", "SPEAKING", "HAPPY", "ANNOYED", "SLEEPING", "ERROR"}


def _type_name(ftype) -> str:
    if isinstance(ftype, tuple):
        return "(" + ", ".join(t.__name__ for t in ftype) + ")"
    return ftype.__name__


def _check(value, ftype) -> bool:
    if ftype is bool:
        return type(value) is bool
    if isinstance(ftype, tuple):
        return any(_check(value, t) for t in ftype)
    if ftype is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if ftype is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, ftype)


# "id" is the transport envelope added by the brain queue after validation;
# validators ignore it so queued commands re-validate cleanly.
ENVELOPE_FIELDS = {"id"}


def validate_message(msg: dict) -> tuple[bool, str]:
    if not isinstance(msg, dict):
        return False, "message must be an object"
    mtype = msg.get("type")
    schema = SCHEMAS.get(mtype) if isinstance(mtype, str) else None
    if schema is None:
        return False, f"unknown message type: {mtype!r}"
    for field, ftype in schema["required"].items():
        if field not in msg:
            return False, f"missing required field: {field}"
        if not _check(msg[field], ftype):
            return False, f"field {field!r} must be {_type_name(ftype)}"
    for field, ftype in schema["optional"].items():
        if field in msg and not _check(msg[field], ftype):
            return False, f"field {field!r} must be {_type_name(ftype)}"
    allowed = set(schema["required"]) | set(schema["optional"]) | {"type"} | ENVELOPE_FIELDS
    for field in msg:
        if field not in allowed:
            return False, f"unexpected field: {field}"
    if mtype == "avatar.expression":
        intensity = msg.get("intensity", 0.7)
        if not 0.0 <= intensity <= 1.0:
            return False, "intensity must be within [0, 1]"
    if mtype == "avatar.state" and msg["state"] not in AVATAR_STATES:
        return False, f"unknown avatar state: {msg['state']!r}"
    return True, "valid"


def build_intent(intent: str, parameters: dict | None = None) -> dict:
    """Structured brain output. Never a shell command."""
    msg = {"type": "brain.intent", "intent": intent,
           "parameters": dict(parameters or {})}
    ok, reason = validate_message(msg)
    if not ok:
        raise ValueError(reason)
    return msg
