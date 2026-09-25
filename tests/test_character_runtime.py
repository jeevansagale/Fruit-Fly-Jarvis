"""Cycle 2 tests: character runtime (renderer-independent)."""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "packages"))
from character_runtime.runtime import CharacterRuntime


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.rt = CharacterRuntime(REPO / "characters" / "goth-mommy.yaml")

    def test_load_identity(self):
        self.assertEqual(self.rt.id, "goth-mommy")
        self.assertEqual(self.rt.state, "BOOT")

    def test_state_transitions_validated(self):
        self.assertEqual(self.rt.set_state("IDLE"), "IDLE")
        with self.assertRaises(ValueError):
            self.rt.set_state("FLYING")

    def test_expression_bounds(self):
        self.assertEqual(self.rt.set_expression("happy", 0.5)["intensity"], 0.5)
        with self.assertRaises(ValueError):
            self.rt.set_expression("happy", 9.0)

    def test_look_at_clamped(self):
        self.assertEqual(self.rt.set_look_at(5.0, -5.0), {"x": 1.0, "y": -1.0})

    def test_idle_pose_bounded(self):
        for t in (0.0, 1.0, 2.5, 10.0):
            pose = self.rt.idle_pose(t)
            self.assertLessEqual(abs(pose["breath"]), 0.02)
            self.assertLessEqual(abs(pose["sway"]), 0.031)
            self.assertLessEqual(pose["blink_phase"], 1.0)

    def test_character_swap(self):
        furina = CharacterRuntime(REPO / "characters" / "furina.yaml")
        self.assertEqual(furina.id, "furina")
        self.assertNotEqual(furina.data["personality"]["archetype"],
                            self.rt.data["personality"]["archetype"])

    def test_personality_never_list(self):
        self.assertIn("sexual content", self.rt.data["behavior"]["never"])

    def test_missing_section_rejected(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("character:\n  id: x\n")
            name = f.name
        with self.assertRaises(ValueError):
            CharacterRuntime(name)


if __name__ == "__main__":
    unittest.main()
