#!/usr/bin/env python3
"""Camera check: capture frames, classify gestures, print results. No GUI.

Default (observe): exit 0 with at least one classified gesture, 1 otherwise.
--control: execute mapped gestures through the policy-gated controller
(swipe left/right = workspace prev/next, swipe up/down = scroll page,
pinch = media toggle). Ctrl+C stops.
Missing backend/camera prints BLOCKED guidance, exit 2.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

try:
    from vision.hands import HandTracker, gesture_intent
except ImportError as exc:
    print(f"BLOCKED: {exc}")
    raise SystemExit(2)

CONTROL_COOLDOWN = 2.5  # seconds between executions of the same gesture


def should_fire(last_fired: dict, gesture: str, now: float) -> bool:
    if now - last_fired.get(gesture, 0.0) < CONTROL_COOLDOWN:
        return False
    last_fired[gesture] = now
    return True


def main() -> int:
    control = "--control" in sys.argv[1:]
    debug = "--debug" in sys.argv[1:]
    controller = None
    calib = None
    compass = None
    if control:
        from capability_policy.controller import ComputerController
        from capability_policy.policy import CapabilityPolicy
        from vision.calibration import Calibration, detect_undo, intent_key
        from vision.motion import MotionCompass
        controller = ComputerController(CapabilityPolicy())
        calib = Calibration()
        compass = MotionCompass()
        print(f"CONTROL MODE (dx={calib.dx:.2f} cooldown={calib.cooldown:.1f}s): "
              "gestures will switch workspaces, scroll, and toggle media. "
              "Motion-compass backup active: broad sweeps work even when "
              "landmarks miss. Undo a misfire with the opposite gesture to "
              "train sensitivity. Ctrl+C stops.")
    try:
        tracker_kwargs = {}
        if calib is not None:
            tracker_kwargs = {"swipe_dx": calib.dx, "swipe_cooldown": calib.cooldown}
        tracker = HandTracker(**tracker_kwargs)
    except RuntimeError as exc:
        print(f"BLOCKED: {exc}")
        return 2

    seen: set[str] = set()
    last_fired: dict = {}
    last_action: tuple | None = None
    last_backend = getattr(tracker, "backend_name", "?")
    print(f"backend={last_backend}")
    deadline = time.monotonic() + (3600 if control else 25)
    frames = 0
    try:
        while time.monotonic() < deadline:
            try:
                hands = tracker.read()
            except RuntimeError as exc:
                print(f"BLOCKED: {exc}")
                return 2
            frames += 1
            now = time.monotonic()
            if debug and frames % 10 == 0:
                score = getattr(getattr(tracker, "onnx", None), "last_score", 0.0)
                print(f"frame={frames} score={score:.2f} "
                      f"brightness={tracker.last_brightness:.0f} hands={len(hands)}")
            events = []
            for hand in hands:
                static, swipe = hand["static"], hand["swipe"]
                events.extend(("landmark", g) for g in (static, swipe)
                              if g and g != "unknown")
            if compass is not None and tracker.last_small is not None:
                backup = compass.update(tracker.last_small)
                if backup is not None:
                    events.append(("motion", backup))
            for source, gesture in events:
                if gesture not in seen:
                    seen.add(gesture)
                mapped = gesture_intent(gesture)
                if controller is not None and mapped is not None \
                        and should_fire(last_fired, gesture, now):
                    intent, params = mapped
                    undone = detect_undo(last_action, intent, params, now)
                    if undone is not None and calib is not None:
                        calib.record_undo()
                        calib.save()
                        print(f"frame={frames} learned: {undone} misfired "
                              f"(dx now {calib.dx:.2f})")
                    elif calib is not None:
                        calib.record_accept()
                        calib.save()
                    result = controller.execute(intent, params)
                    last_action = (gesture, intent_key(intent, params), now)
                    print(f"frame={frames} gesture={gesture} src={source} "
                          f"{intent} -> ok={result['ok']} {result['detail'][:120]}")
                elif controller is None:
                    print(f"frame={frames} gesture={gesture} capability={mapped}")
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    print(f"frames={frames} gestures={sorted(seen) or 'none'}")
    if not control:
        print("Show an open palm, fist, pinch, or swipe across the camera.")
    return 0 if seen - {"unknown"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
