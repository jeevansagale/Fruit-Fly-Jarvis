"""Motion-compass backup detector: directional sweeps from frame differences.

No ML, no model files — plain OpenCV on downscaled grayscale frames. Runs
alongside the landmark backend and catches what it misses (low scores, bad
light, small hands): a hand sweeping left reads as swipe_left even when no
landmarks resolve. Emits the same swipe_* names so the intent map applies.
"""
from __future__ import annotations

import time

WIDTH, HEIGHT = 160, 120
DIFF_THRESHOLD = 25
MIN_FRACTION = 0.02   # ignore sensor noise
MAX_FRACTION = 0.50   # ignore full-frame flashes / auto-exposure jumps
MIN_TRAVEL = 0.15     # normalized displacement to count as a sweep
MAX_LATERAL = 0.45    # cross-axis drift allowed as fraction of travel
MIN_DT = 0.15
MAX_DT = 1.2
COOLDOWN = 1.5


class MotionCompass:
    def __init__(self, clock=time.monotonic, cooldown: float = COOLDOWN):
        self.clock = clock
        self.cooldown = cooldown
        self.prev = None
        self.trail: list = []
        self.last_fire = 0.0

    def _centroid(self, gray):
        import numpy as np
        if self.prev is None:
            self.prev = gray
            return None
        diff = (abs(gray.astype(int) - self.prev.astype(int)) > DIFF_THRESHOLD)
        self.prev = gray
        frac = diff.mean()
        if not MIN_FRACTION < frac < MAX_FRACTION:
            return None
        ys, xs = np.where(diff)
        return (float(xs.mean()) / WIDTH, float(ys.mean()) / HEIGHT)

    def update(self, gray) -> str | None:
        """Feed a WIDTHxHEIGHT uint8 grayscale frame; get swipe_* or None."""
        now = self.clock()
        center = self._centroid(gray)
        if center is None:
            return None
        self.trail.append((now, center))
        self.trail = [(t, p) for t, p in self.trail if now - t <= MAX_DT]
        if now - self.last_fire < self.cooldown:
            return None
        (t0, p0), (t1, p1) = self.trail[0], self.trail[-1]
        dt = t1 - t0
        if dt < MIN_DT:
            return None
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        travel = max(abs(dx), abs(dy))
        if travel < MIN_TRAVEL:
            return None
        gesture = None
        if abs(dx) >= abs(dy) and abs(dy) <= travel * MAX_LATERAL + 0.03:
            gesture = "swipe_right" if dx > 0 else "swipe_left"
        elif abs(dy) > abs(dx) and abs(dx) <= travel * MAX_LATERAL + 0.03:
            gesture = "swipe_down" if dy > 0 else "swipe_up"
        if gesture:
            self.last_fire = now
            self.trail = []
        return gesture

    def reset(self) -> None:
        self.prev = None
        self.trail = []
