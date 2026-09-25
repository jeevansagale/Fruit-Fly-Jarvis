"""Hyprland typed adapter. All actions go through CapabilityPolicy first;
this module never talks to an LLM and never runs unvalidated commands."""
from __future__ import annotations

import json
import subprocess


def _run(cmd: list[str], timeout: int = 10) -> tuple[bool, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode == 0, ((proc.stdout or "") + (proc.stderr or ""))[:2000]
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return False, f"backend unavailable: {exc}"


def _hyprctl(*args: str, timeout: int = 10) -> tuple[bool, str]:
    try:
        proc = subprocess.run(["hyprctl", *args], capture_output=True,
                              text=True, timeout=timeout)
        return proc.returncode == 0, (proc.stdout or "")[:8000]
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return False, f"hyprctl unavailable: {exc}"


class MediaAdapter:
    """playerctl play/pause toggle. Graceful failure, no exceptions."""

    def toggle(self) -> tuple[bool, str]:
        return _run(["playerctl", "play-pause"])


class ScrollAdapter:
    """Page scroll via ydotool keys. Needs the ydotool daemon; fails cleanly."""

    def page(self, direction: str) -> tuple[bool, str]:
        if direction not in ("up", "down"):
            return False, "invalid direction"
        key = "Page_Up" if direction == "up" else "Page_Down"
        return _run(["ydotool", "key", key])


class HyprlandAdapter:
    def __init__(self):
        self.lua_mode: bool | None = None  # auto-detected, then cached

    def _dispatch_workspace(self, arg: str) -> tuple[bool, str]:
        """Legacy `dispatch workspace <arg>` works on hyprlang configs; on
        Lua-config Hyprland (>=0.55) it fails with an hl.dispatch parse
        error, so fall back to the Lua focus() call and remember."""
        if self.lua_mode is False:
            return _hyprctl("dispatch", "workspace", arg)
        if self.lua_mode is True:
            return _hyprctl("dispatch", f'hl.dsp.focus({{workspace = "{arg}"}})')
        ok, out = _hyprctl("dispatch", "workspace", arg)
        if not ok and "hl.dispatch" in out:
            self.lua_mode = True
            return _hyprctl("dispatch", f'hl.dsp.focus({{workspace = "{arg}"}})')
        self.lua_mode = False
        return ok, out

    def workspaces(self) -> tuple[bool, object]:
        ok, out = _hyprctl("workspaces", "-j")
        if not ok:
            return False, out
        try:
            return True, json.loads(out)
        except ValueError:
            return False, "hyprctl returned non-JSON"

    def active_workspace(self) -> tuple[bool, object]:
        ok, out = _hyprctl("activeworkspace", "-j")
        if not ok:
            return False, out
        try:
            return True, json.loads(out)
        except ValueError:
            return False, "hyprctl returned non-JSON"

    def switch_workspace(self, name: str) -> tuple[bool, str]:
        from capability_policy.policy import NAME_PATTERN
        if not NAME_PATTERN.match(name):
            return False, "invalid workspace name"
        return self._dispatch_workspace(name)

    def move_workspace(self, delta: int) -> tuple[bool, str]:
        """Relative switch (+1/-1) through the version-proof dispatcher."""
        if delta not in (1, -1):
            return False, "delta must be +1 or -1"
        return self._dispatch_workspace(f"{delta:+d}")


class ComputerController:
    """Executes only policy-approved intents via typed adapters."""

    def __init__(self, policy, hyprland: HyprlandAdapter | None = None,
                 media: MediaAdapter | None = None, scroll: ScrollAdapter | None = None):
        self.policy = policy
        self.hyprland = hyprland or HyprlandAdapter()
        self.media = media or MediaAdapter()
        self.scroll = scroll or ScrollAdapter()

    def execute(self, intent: str, parameters: dict) -> dict:
        allowed, reason = self.policy.validate(intent, parameters)
        if not allowed:
            return {"ok": False, "detail": reason}
        if intent == "workspace.switch":
            ok, out = self.hyprland.switch_workspace(parameters["name"])
            return {"ok": ok, "detail": out[:200] + ("...[truncated]" if len(out) > 200 else "")}
        if intent == "workspace.next":
            ok, out = self.hyprland.move_workspace(1)
            return {"ok": ok, "detail": out[:200]}
        if intent == "workspace.previous":
            ok, out = self.hyprland.move_workspace(-1)
            return {"ok": ok, "detail": out[:200]}
        if intent == "media.play_pause":
            ok, out = self.media.toggle()
            return {"ok": ok, "detail": out[:200]}
        if intent == "scroll.page":
            ok, out = self.scroll.page(parameters["direction"])
            return {"ok": ok, "detail": out[:200]}
        return {"ok": False, "detail": f"no adapter wired for {intent}"}
