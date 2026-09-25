"""Cycle 1 tests: contracts, behavior engine, capability policy, brain."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))
from behavior.engine import BehaviorEngine
from capability_policy.policy import CapabilityPolicy
from contracts.messages import AVATAR_STATES, build_intent, validate_message


class ContractTests(unittest.TestCase):
    def test_animation_play_valid(self):
        self.assertEqual(validate_message(
            {"type": "avatar.animation.play", "name": "idle", "loop": True})[0], True)

    def test_unknown_type_rejected(self):
        self.assertEqual(validate_message({"type": "shell.exec"})[0], False)

    def test_missing_field_rejected(self):
        self.assertEqual(validate_message({"type": "avatar.look_at", "x": 1})[0], False)

    def test_expression_intensity_bounds(self):
        ok, _ = validate_message({"type": "avatar.expression", "expression": "happy", "intensity": 2.0})
        self.assertFalse(ok)

    def test_no_shell_capability_message(self):
        self.assertNotIn("shell.exec", __import__("contracts.messages", fromlist=["SCHEMAS"]).SCHEMAS)

    def test_avatar_states_cover_runtime(self):
        for s in ("IDLE", "LISTENING", "THINKING", "SPEAKING", "ERROR"):
            self.assertIn(s, AVATAR_STATES)

    def test_build_intent_shape(self):
        intent = build_intent("open_application", {"application": "firefox"})
        self.assertEqual(intent["type"], "brain.intent")
        self.assertNotIn("command", intent)


class BehaviorTests(unittest.TestCase):
    def test_happy_path(self):
        eng = BehaviorEngine()
        for event, expect in (("user_started_speaking", "LISTENING"),
                              ("user_stopped_speaking", "THINKING"),
                              ("brain_response", "RESPONDING"),
                              ("tool_finished", "SPEAKING"),
                              ("tool_finished", "IDLE")):
            self.assertEqual(eng.handle(event), expect)

    def test_error_and_reset(self):
        eng = BehaviorEngine()
        self.assertEqual(eng.handle("system_error"), "ERROR")
        self.assertEqual(eng.output()["animation"], "idle")
        self.assertEqual(eng.handle("reset"), "IDLE")

    def test_unknown_transition_stable(self):
        eng = BehaviorEngine()
        self.assertEqual(eng.handle("brain_response"), "IDLE")

    def test_output_has_avatar_directives(self):
        out = BehaviorEngine("SPEAKING").output()
        self.assertEqual(set(out), {"expression", "animation", "overlay"})


class PolicyTests(unittest.TestCase):
    def test_allowlisted_no_arg_action(self):
        self.assertTrue(CapabilityPolicy().validate("workspace.next", {})[0])

    def test_unknown_capability_denied(self):
        self.assertEqual(CapabilityPolicy().validate("shell.exec", {})[1], "unknown capability")

    def test_missing_argument_denied(self):
        self.assertFalse(CapabilityPolicy().validate("workspace.switch", {})[0])

    def test_confirm_gated_action(self):
        p = CapabilityPolicy(allowed={"app.launch"})
        self.assertFalse(p.validate("app.launch", {"app": "firefox"})[0])
        self.assertTrue(p.validate("app.launch", {"app": "firefox", "confirmed": True})[0])

    def test_url_scheme_restricted(self):
        p = CapabilityPolicy(allowed={"open_url"})
        self.assertFalse(p.validate("open_url", {"url": "file:///etc/passwd", "confirmed": True})[0])
        self.assertTrue(p.validate("open_url", {"url": "https://example.com", "confirmed": True})[0])

    def test_volume_bounds(self):
        p = CapabilityPolicy(allowed={"volume.set"})
        self.assertFalse(p.validate("volume.set", {"level": 150})[0])
        self.assertTrue(p.validate("volume.set", {"level": 40})[0])

    def test_empty_allowlist_stays_empty(self):
        self.assertEqual(CapabilityPolicy(allowed=set()).allowed, set())


if __name__ == "__main__":
    unittest.main()
