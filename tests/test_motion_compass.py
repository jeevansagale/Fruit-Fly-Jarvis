"""Motion-compass tests on synthetic frames (no camera needed)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

try:
    import numpy as np
    from vision.motion import HEIGHT, MotionCompass, WIDTH
    HAVE_CV = True
except ImportError:
    HAVE_CV = False


def blob(x, y, size=14):
    frame = np.zeros((HEIGHT, WIDTH), dtype="uint8")
    frame[max(0, y - size):y + size, max(0, x - size):x + size] = 200
    return frame


class FakeClock:
    def __init__(self):
        self.t = 50.0

    def __call__(self):
        return self.t


@unittest.skipUnless(HAVE_CV, "numpy required")
class CompassTests(unittest.TestCase):
    def sweep(self, positions, dt=0.2):
        clock = FakeClock()
        compass = MotionCompass(clock=clock)
        out = None
        for x, y in positions:
            out = compass.update(blob(x, y)) or out
            clock.t += dt
        return out

    def test_sweep_right(self):
        xs = [20, 50, 80, 110, 140]
        self.assertEqual(self.sweep([(x, 60) for x in xs]), "swipe_right")

    def test_sweep_left(self):
        xs = [140, 110, 80, 50, 20]
        self.assertEqual(self.sweep([(x, 60) for x in xs]), "swipe_left")

    def test_sweep_up(self):
        ys = [100, 80, 60, 40, 20]
        self.assertEqual(self.sweep([(80, y) for y in ys]), "swipe_up")

    def test_static_no_fire(self):
        self.assertIsNone(self.sweep([(80, 60)] * 6))

    def test_empty_frames(self):
        import numpy as np
        clock = FakeClock()
        compass = MotionCompass(clock=clock)
        out = None
        for _ in range(6):
            out = compass.update(np.zeros((HEIGHT, WIDTH), dtype="uint8")) or out
            clock.t += 0.2
        self.assertIsNone(out)

    def test_cooldown(self):
        clock = FakeClock()
        compass = MotionCompass(clock=clock)
        fired = []
        for x in (20, 60, 100, 140, 150):
            fired.append(compass.update(blob(x, 60)))
            clock.t += 0.2
        self.assertIn("swipe_right", fired)
        clock.t += 0.2
        self.assertIsNone(compass.update(blob(20, 60)))


if __name__ == "__main__":
    unittest.main()
