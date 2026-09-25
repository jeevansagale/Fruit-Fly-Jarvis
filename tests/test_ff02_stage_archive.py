"""Small, asset-free safety tests for the FF-02 local staging helper."""
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZipInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from ff02_stage_archive import stage_archive  # noqa: E402
from model_inventory import inspect_file  # noqa: E402


class ArchiveStagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archive = self.root / "candidate.zip"
        self.dest = self.root / "local" / "candidate"

    def make_zip(self, files):
        with ZipFile(self.archive, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, data)

    def test_stages_model_textures_and_license_without_executable(self):
        self.make_zip({"source/model.fbx": b"dummy", "textures/face.png": b"png",
                       "LICENSE.txt": b"owner", "install.sh": b"do not run"})
        staged, skipped = stage_archive(self.archive, self.dest)
        self.assertEqual({p.relative_to(self.dest).as_posix() for p in staged},
                         {"source/model.fbx", "textures/face.png", "LICENSE.txt"})
        self.assertEqual(skipped, ["install.sh"])
        self.assertFalse((self.dest / "install.sh").exists())

    def test_rejects_traversal_before_writing(self):
        self.make_zip({"source/model.fbx": b"dummy", "../leak.png": b"secret"})
        with self.assertRaisesRegex(ValueError, "unsafe archive path"):
            stage_archive(self.archive, self.dest)
        self.assertFalse(self.dest.exists())
        self.assertFalse((self.root / "leak.png").exists())

    def test_rejects_absolute_and_backslash_paths(self):
        for invalid in ("/tmp/leak.png", "textures\\..\\leak.png"):
            self.make_zip({"model.fbx": b"dummy", invalid: b"bad"})
            with self.assertRaisesRegex(ValueError, "unsafe archive path"):
                stage_archive(self.archive, self.dest)
            self.assertFalse(self.dest.exists())

    def test_rejects_symlinks(self):
        with ZipFile(self.archive, "w") as archive:
            archive.writestr("model.fbx", b"dummy")
            entry = ZipInfo("textures/escape.png")
            entry.create_system = 3
            entry.external_attr = 0o120777 << 16
            archive.writestr(entry, b"/tmp/escape")
        with self.assertRaisesRegex(ValueError, "entry type"):
            stage_archive(self.archive, self.dest)
        self.assertFalse(self.dest.exists())

    def test_refuses_overwrite(self):
        self.make_zip({"model.fbx": b"dummy"})
        stage_archive(self.archive, self.dest)
        with self.assertRaisesRegex(ValueError, "will not overwrite"):
            stage_archive(self.archive, self.dest)
        self.assertEqual((self.dest / "model.fbx").read_bytes(), b"dummy")

    def test_rejects_non_model_archive(self):
        self.make_zip({"textures/face.png": b"png"})
        with self.assertRaisesRegex(ValueError, "no recognized model"):
            stage_archive(self.archive, self.dest)
        self.assertFalse(self.dest.exists())

    def test_inventory_does_not_infer_runtime_capabilities(self):
        model = self.root / "pretend.fbx"
        model.write_bytes(b"not actually a valid FBX")
        item = inspect_file(model, self.root)
        self.assertEqual(item["format"], "FBX")
        self.assertEqual(item["size_bytes"], model.stat().st_size)
        self.assertEqual(len(item["sha256"]), 64)
        metadata = item["renderer_metadata"]
        for field in ("has_skeleton", "has_humanoid_rig", "has_animation_data",
                      "has_morph_targets", "has_materials", "has_textures",
                      "has_expressions", "has_eye_look_at", "has_physics"):
            self.assertEqual(metadata[field], "unknown", field)


if __name__ == "__main__":
    unittest.main()
