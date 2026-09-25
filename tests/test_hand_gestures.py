"""Hand classifier + swipe tests on synthetic landmarks (no camera needed)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))
from vision.hands import SwipeTracker, classify_static, gesture_event, gesture_intent

W = (0.5, 0.9)
OFFS = [-0.12, -0.04, 0.04, 0.12]


def make_hand(extended, thumb_tip=(0.3, 0.5), index_tip=None):
    lm = [W] * 21
    lm[3] = (0.4, 0.7)
    lm[4] = thumb_tip
    pips = [6, 10, 14, 18]
    tips = [8, 12, 16, 20]
    for i, (pip, tip) in enumerate(zip(pips, tips)):
        lm[pip] = (0.5 + OFFS[i], 0.55)
        if index_tip is not None and i == 0:
            lm[tip] = index_tip
        elif extended[i]:
            lm[tip] = (0.5 + OFFS[i], 0.3)
        else:
            lm[tip] = (0.5 + OFFS[i], 0.8)
    return lm


class StaticTests(unittest.TestCase):
    def test_open_palm(self):
        self.assertEqual(classify_static(make_hand([True] * 4)), "open_palm")

    def test_fist(self):
        self.assertEqual(classify_static(make_hand([False] * 4)), "fist")

    def test_pinch(self):
        lm = make_hand([True, False, False, False], index_tip=(0.32, 0.52))
        lm[4] = (0.33, 0.53)
        self.assertEqual(classify_static(lm), "pinch")

    def test_point(self):
        self.assertEqual(classify_static(make_hand([True, False, False, False])), "point")

    def test_short_list_unknown(self):
        self.assertEqual(classify_static([(0, 0)] * 5), "unknown")

    def test_gesture_event_shape(self):
        from contracts.messages import validate_message
        ok, reason = validate_message(gesture_event("swipe_left", 0.92))
        self.assertTrue(ok, reason)

    def test_gesture_intent_map(self):
        self.assertEqual(gesture_intent("swipe_left"), ("workspace.previous", {}))
        self.assertEqual(gesture_intent("pinch"), ("media.play_pause", {}))
        self.assertIsNone(gesture_intent("fist"))
        self.assertIsNone(gesture_intent("open_palm"))

    def test_control_cooldown(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        from vision_check import CONTROL_COOLDOWN, should_fire
        last: dict = {}
        self.assertTrue(should_fire(last, "swipe_right", 100.0))
        self.assertFalse(should_fire(last, "swipe_right", 100.0 + CONTROL_COOLDOWN - 0.1))
        self.assertTrue(should_fire(last, "swipe_right", 100.0 + CONTROL_COOLDOWN + 0.1))
        self.assertTrue(should_fire(last, "pinch", 100.0))


class CalibrationTests(unittest.TestCase):
    def test_undo_detection(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))
        from vision.calibration import detect_undo
        last = ("swipe_right", "workspace.next", 100.0)
        self.assertEqual(
            detect_undo(last, "workspace.previous", {}, 102.0), "swipe_right")
        self.assertIsNone(
            detect_undo(last, "workspace.previous", {}, 200.0))
        self.assertIsNone(
            detect_undo(last, "media.play_pause", {}, 102.0))
        self.assertIsNone(detect_undo(None, "workspace.previous", {}, 102.0))

    def test_learn_and_relax(self):
        import tempfile
        from vision.calibration import Calibration, DEFAULT_COOLDOWN, DEFAULT_DX
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cal.json"
            cal = Calibration(path)
            self.assertEqual((cal.dx, cal.cooldown), (DEFAULT_DX, DEFAULT_COOLDOWN))
            cal.record_undo()
            self.assertGreater(cal.dx, DEFAULT_DX)
            cal.save()
            self.assertEqual(Calibration(path).dx, cal.dx)
            for _ in range(50):
                cal.record_accept()
            self.assertLessEqual(cal.dx, DEFAULT_DX + 0.02)


class FakeClock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


class SwipeTests(unittest.TestCase):
    def test_swipe_right(self):
        clock = FakeClock()
        tracker = SwipeTracker(clock=clock)
        self.assertIsNone(tracker.update((0.3, 0.5)))
        clock.t += 0.3
        self.assertEqual(tracker.update((0.5, 0.5)), "swipe_right")

    def test_swipe_up(self):
        clock = FakeClock()
        tracker = SwipeTracker(clock=clock)
        tracker.update((0.5, 0.6))
        clock.t += 0.3
        self.assertEqual(tracker.update((0.5, 0.4)), "swipe_up")

    def test_cooldown_blocks_repeat(self):
        clock = FakeClock()
        tracker = SwipeTracker(clock=clock)
        tracker.update((0.3, 0.5))
        clock.t += 0.3
        self.assertEqual(tracker.update((0.5, 0.5)), "swipe_right")
        tracker.update((0.3, 0.5))
        clock.t += 0.3
        self.assertIsNone(tracker.update((0.5, 0.5)))

    def test_stale_window_resets(self):
        clock = FakeClock()
        tracker = SwipeTracker(clock=clock)
        tracker.update((0.3, 0.5))
        clock.t += 5.0
        self.assertIsNone(tracker.update((0.5, 0.5)))


class TrackingTests(unittest.TestCase):
    def test_smooth_points(self):
        from vision.hands import smooth_points
        prev = [(0.0, 0.0), (1.0, 1.0)]
        new = [(1.0, 1.0), (0.0, 0.0)]
        self.assertEqual(smooth_points(None, new), [(1.0, 1.0), (0.0, 0.0)])
        self.assertEqual(smooth_points(prev, new, alpha=0.5),
                         [(0.5, 0.5), (0.5, 0.5)])

    def test_bbox_and_crop_map(self):
        from vision.hands import bbox_of, map_crop_to_frame
        lm = [(0.4, 0.4), (0.6, 0.6)]
        box = bbox_of(lm, margin=0.0)
        self.assertEqual(box, (0.4, 0.4, 0.6, 0.6))
        mapped = map_crop_to_frame([(0.0, 0.0), (1.0, 1.0), (0.5, 0.5)], box)
        self.assertEqual(mapped, [(0.4, 0.4), (0.6, 0.6), (0.5, 0.5)])

    def test_custom_swipe_threshold(self):
        clock = FakeClock()
        tracker = SwipeTracker(clock=clock, dx_min=0.3)
        tracker.update((0.3, 0.5))
        clock.t += 0.3
        self.assertIsNone(tracker.update((0.5, 0.5)))
        clock.t += 1.5
        tracker.update((0.2, 0.5))
        clock.t += 0.3
        self.assertEqual(tracker.update((0.6, 0.5)), "swipe_right")


if __name__ == "__main__":
    unittest.main()
