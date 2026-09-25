"""Asset-free tests for the FF-02C validation harness."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ff02c_validate as v  # noqa: E402


class StatusTests(unittest.TestCase):
    def test_only_known_statuses_accepted(self):
        for s in ("PASS", "FAIL", "PENDING", "UNKNOWN", "BLOCKED", "SKIPPED"):
            self.assertEqual(v.check_status(s), s)
        with self.assertRaises(ValueError):
            v.check_status("pass")
        with self.assertRaises(ValueError):
            v.check_status("NOT TESTED")


class SanitizeTests(unittest.TestCase):
    def test_home_path_replaced(self):
        self.assertEqual(v.sanitize_text("/home/example/fruit-fly"), "$HOME/fruit-fly")

    def test_secrets_redacted(self):
        out = v.sanitize_text("api_key=supersecretvalue123 token bearer abcdefgh12345678")
        self.assertNotIn("supersecretvalue123", out)
        self.assertNotIn("abcdefgh12345678", out)
        self.assertIn("[REDACTED]", out)

    def test_private_key_redacted(self):
        blob = "-----BEGIN RSA PRIVATE KEY-----\nMIIBsecret\n-----END RSA PRIVATE KEY-----"
        self.assertNotIn("MIIBsecret", v.sanitize_text(blob))


class MissingCommandTests(unittest.TestCase):
    def test_nonexistent_command_returns_unavailable(self):
        r = v.run_cmd(["ff02c-definitely-not-a-real-command-xyz"])
        self.assertFalse(r["available"])
        self.assertIsNone(r["exit_code"])


class MissingAssetDirTests(unittest.TestCase):
    def test_missing_characters_local_is_controlled(self):
        real = v.LOCAL_ASSETS
        try:
            v.LOCAL_ASSETS = Path(tempfile.mkdtemp()) / "does-not-exist"
            out = v.collect_assets()
            self.assertIn(out["status"], ("BLOCKED", "UNKNOWN"))
        finally:
            v.LOCAL_ASSETS = real


class ShaTests(unittest.TestCase):
    def test_sha256_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.bin"
            p.write_bytes(b"fruit-fly-ff02c")
            import hashlib
            self.assertEqual(v.sha256_file(p), hashlib.sha256(b"fruit-fly-ff02c").hexdigest())


class ReportTests(unittest.TestCase):
    def _minimal(self):
        env = {"commands": {k: {"available": False, "exit_code": None, "stdout": "", "stderr": "x"}
                            for k in ("uname", "hyprctl", "nvidia_smi", "godot", "chromium",
                                      "gtk4", "gtk4_layer_shell", "rustc", "cargo", "node")},
               "session_env": {}}
        env["commands"]["uname"] = {"available": True, "exit_code": 0, "stdout": "Linux test", "stderr": ""}
        base = lambda s: {"status": s, "reason": "t"}
        assets = {"status": "UNKNOWN", "reason": "t", "asset_count": 0}
        three = {"status": "PENDING", "warnings": ["w"], "probe_dir": "x", "three_version": "x", "uses_FBXLoader": True}
        godot = {"status": "BLOCKED", "reason": "t", "godot_version": "unavailable"}
        textures = {"status": "UNKNOWN", "reason": "t", "entries": []}
        anim = {"status": "UNKNOWN", "reason": "t", "clips": [], "skeleton_present": None,
                "bone_count": None, "morph_target_count": None, "skinned_mesh_count": None,
                "candidates": {"eye": [], "head": []}}
        perf = {"status": "UNKNOWN", "reason": "t", "asset_hash_elapsed_s": 0.0,
                "fps": None, "frame_time_ms": None}
        overlay = {"status": "BLOCKED", "reason": "t", "checks": {}}
        return env, assets, three, godot, textures, anim, perf, overlay

    def test_required_sections_present(self):
        env, assets, three, godot, textures, anim, perf, overlay = self._minimal()
        md = v.build_report(env, assets, three, godot, textures, anim, perf, overlay)
        for section in ("# FF-02C Target-Machine Validation", "Date", "Git commit",
                        "Overall status", "Environment", "Asset inventory", "Three.js",
                        "Godot", "Texture validation", "Animation validation",
                        "Character structure", "Performance", "FF-01 overlay", "Ctrl+C",
                        "Automated checks", "Manual checks", "Known limitations",
                        "Unresolved issues", "Renderer decision:", "PENDING"):
            self.assertIn(section, md)

    def test_renderer_decision_pending(self):
        env, assets, three, godot, textures, anim, perf, overlay = self._minimal()
        md = v.build_report(env, assets, three, godot, textures, anim, perf, overlay)
        self.assertIn("Renderer decision:\nPENDING", md)

    def test_animation_unknown_not_no_animation(self):
        three = {"status": "PENDING", "animation_clip_count": 0, "animation_names": []}
        godot = {"results": []}
        out = v.collect_animation_structure(three, godot)
        self.assertEqual(out["status"], "UNKNOWN")
        self.assertIn("UNKNOWN", out["reason"])
        self.assertNotEqual(out["reason"].strip(), "NO ANIMATION")


if __name__ == "__main__":
    unittest.main()
