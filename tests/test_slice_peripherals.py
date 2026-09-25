"""Peripheral + controller tests (mocked hyprctl)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))
from capability_policy.controller import ComputerController
from capability_policy.policy import CapabilityPolicy
from perception.providers import SessionMemory, VisionProvider, VoiceProvider


class PeripheralTests(unittest.TestCase):
    def test_voice_mock_shapes(self):
        v = VoiceProvider()
        self.assertEqual(v.listen_once()["event"], "user_started_speaking")
        self.assertFalse(v.speak("hi")["spoken"])

    def test_gesture_confidence_clamped(self):
        event = VisionProvider.gesture_event("swipe_left", 9.0)
        self.assertEqual(event["type"], "system.event")
        self.assertEqual(event["data"]["confidence"], 1.0)

    def test_memory_bounds(self):
        m = SessionMemory()
        for i in range(30):
            m.add_turn("user", f"msg {i}")
        self.assertEqual(len(m.turns), 20)
        m.set_preference("theme", "goth")
        self.assertEqual(m.preferences["theme"], "goth")


class ControllerTests(unittest.TestCase):
    def test_denied_intent_never_reaches_adapter(self):
        calls = []

        class FakeHypr:
            def switch_workspace(self, name):
                calls.append(name)
                return True, "ok"

        ctrl = ComputerController(CapabilityPolicy(allowed=set()), FakeHypr())
        result = ctrl.execute("workspace.switch", {"name": "2"})
        self.assertFalse(result["ok"])
        self.assertEqual(calls, [])

    def test_unconfirmed_launch_blocked(self):
        ctrl = ComputerController(CapabilityPolicy())
        result = ctrl.execute("app.launch", {"app": "firefox"})
        self.assertFalse(result["ok"])

    def test_allowed_passthrough(self):
        class FakeHypr:
            def switch_workspace(self, name):
                return True, "ok"

        ctrl = ComputerController(CapabilityPolicy(allowed={"workspace.switch"}), FakeHypr())
        self.assertTrue(ctrl.execute("workspace.switch", {"name": "2"})["ok"])

    def test_relative_workspace_syntax(self):
        import capability_policy.controller as ctrl_mod
        from capability_policy.controller import HyprlandAdapter
        calls = []
        lua_err = "error: [string \"return hl.dispatch(workspace +1)\"]"
        real = ctrl_mod._hyprctl

        def fake(*a):
            calls.append(a)
            if a[1].startswith("hl.dsp"):
                return True, "ok"
            return False, lua_err

        ctrl_mod._hyprctl = fake
        try:
            adapter = HyprlandAdapter()
            self.assertTrue(adapter.move_workspace(1)[0])
            self.assertTrue(adapter.move_workspace(-1)[0])
            self.assertFalse(adapter.move_workspace(5)[0])
            self.assertTrue(adapter.lua_mode)
        finally:
            ctrl_mod._hyprctl = real
        self.assertIn(("dispatch", "workspace", "+1"), calls)
        self.assertIn(("dispatch", 'hl.dsp.focus({workspace = "+1"})'), calls)
        self.assertIn(("dispatch", 'hl.dsp.focus({workspace = "-1"})'), calls)


if __name__ == "__main__":
    unittest.main()
