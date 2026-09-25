"""Capability policy: allowlisted actions with typed argument schemas.

There is intentionally no generic shell/python/filesystem capability.
Dangerous-but-allowed actions require explicit confirmation.
"""
from __future__ import annotations

import re

# capability -> {"args": {name: validator}, "confirm": bool}
CAPABILITIES = {
    "workspace.next": {"args": {}, "confirm": False},
    "workspace.previous": {"args": {}, "confirm": False},
    "workspace.switch": {"args": {"name": str}, "confirm": False},
    "workspace.focus": {"args": {}, "confirm": False},
    "app.launch": {"args": {"app": str}, "confirm": True},
    "app.close": {"args": {"app": str}, "confirm": True},
    "open_url": {"args": {"url": str}, "confirm": True},
    "media.play_pause": {"args": {}, "confirm": False},
    "media.next": {"args": {}, "confirm": False},
    "media.previous": {"args": {}, "confirm": False},
    "scroll.page": {"args": {"direction": str}, "confirm": False},
    "volume.set": {"args": {"level": int}, "confirm": False},
}

SAFE_URL_PREFIXES = ("http://", "https://")
NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,32}$")

DEFAULT_ALLOWED = {"workspace.next", "workspace.previous", "workspace.focus",
                   "app.launch", "media.play_pause", "media.next", "media.previous",
                   "scroll.page"}


class CapabilityPolicy:
    def __init__(self, allowed=None):
        self.allowed = set(allowed) if allowed is not None else set(DEFAULT_ALLOWED)

    def validate(self, action, arguments):
        spec = CAPABILITIES.get(action)
        if spec is None:
            return False, "unknown capability"
        if action not in self.allowed:
            return False, "capability not allowlisted"
        if not isinstance(arguments, dict):
            return False, "arguments must be an object"
        for name, ftype in spec["args"].items():
            if name not in arguments:
                return False, f"missing argument: {name}"
            value = arguments[name]
            if ftype is int and isinstance(value, bool):
                return False, f"argument {name!r} has wrong type"
            if not isinstance(value, ftype):
                return False, f"argument {name!r} has wrong type"
        if action == "workspace.switch" and not NAME_PATTERN.match(arguments["name"]):
            return False, "workspace name must match [A-Za-z0-9_-]{1,32}"
        if action == "app.launch" and len(arguments["app"]) > 128:
            return False, "application name too long"
        if action == "open_url":
            url = arguments["url"]
            if len(url) > 2048:
                return False, "url too long"
            if not url.startswith(SAFE_URL_PREFIXES):
                return False, "url scheme not permitted"
        if action == "volume.set" and not 0 <= arguments["level"] <= 100:
            return False, "volume level must be within [0, 100]"
        if action == "scroll.page" and arguments["direction"] not in ("up", "down"):
            return False, "direction must be up or down"
        if spec["confirm"] and not arguments.get("confirmed", False):
            return False, "confirmation required"
        return True, "validated"
