#!/usr/bin/env python3
"""Stage an FF-02 candidate ZIP locally, without executing or publishing its contents.

This is a staging helper, not a model validator. Use real importers to test capabilities.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import stat
import sys
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

# Keep unexpected archive contents out of the importer project. Include license
# and attribution text so that local provenance is not silently discarded.
MODEL_EXTENSIONS = {".fbx", ".glb", ".gltf", ".vrm", ".vrma", ".obj"}
OTHER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tga", ".bmp", ".dds", ".ktx2", ".bin", ".txt", ".md", ".json"}
MAX_MEMBERS = 256
MAX_MEMBER_SIZE = 128 * 1024 * 1024
MAX_TOTAL_SIZE = 512 * 1024 * 1024


def safe_members(archive: ZipFile) -> tuple[list, list]:
    """Validate *all* names/types/sizes before writing anything to disk."""
    entries = archive.infolist()
    if len(entries) > MAX_MEMBERS:
        raise ValueError("archive has too many entries")
    selected, skipped = [], []
    seen = set()
    total = 0
    for info in entries:
        name = info.filename
        parts = PurePosixPath(name).parts
        if (not parts or name.startswith("/") or "\\" in name or "\x00" in name
                or any(part in {".", ".."} for part in name.rstrip("/").split("/"))):
            raise ValueError(f"unsafe archive path: {name!r}")
        kind = stat.S_IFMT(info.external_attr >> 16)
        if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise ValueError(f"unsafe archive entry type: {name!r}")
        if info.is_dir():
            continue
        if info.file_size > MAX_MEMBER_SIZE:
            raise ValueError(f"oversized archive entry: {name!r}")
        total += info.file_size
        if total > MAX_TOTAL_SIZE or (info.file_size > 1024 * 1024 and info.file_size > 200 * max(info.compress_size, 1)):
            raise ValueError("archive is too large or has suspicious compression")
        # Case-fold as well: a cross-platform local candidate should not have
        # entries that overwrite each other on another filesystem.
        key = name.casefold()
        if key in seen:
            raise ValueError(f"duplicate archive path: {name!r}")
        seen.add(key)
        if PurePosixPath(name).suffix.lower() in MODEL_EXTENSIONS | OTHER_EXTENSIONS:
            selected.append(info)
        else:
            skipped.append(name)
    if not any(PurePosixPath(info.filename).suffix.lower() in MODEL_EXTENSIONS for info in selected):
        raise ValueError("archive contains no recognized model file")
    return selected, skipped


def stage_archive(archive_path: Path, destination: Path) -> tuple[list[Path], list[str]]:
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"destination already exists (will not overwrite): {destination}")
    with ZipFile(archive_path) as archive:
        selected, skipped = safe_members(archive)
        destination.mkdir(parents=True)
        try:
            for info in selected:
                output = destination.joinpath(*PurePosixPath(info.filename).parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, output.open("xb") as target:
                    shutil.copyfileobj(source, target)
        except Exception:
            shutil.rmtree(destination)
            raise
    return [destination.joinpath(*PurePosixPath(info.filename).parts) for info in selected], skipped


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="local ZIP containing model + textures")
    parser.add_argument("--candidate", required=True, choices=("furina", "columbina", "goth-mommy"))
    parser.add_argument("--root", type=Path, default=Path("characters/local"), help="local staging directory")
    args = parser.parse_args()
    destination = args.root / args.candidate
    try:
        files, skipped = stage_archive(args.archive, destination)
    except (OSError, ValueError, BadZipFile) as exc:
        print(f"FF-02 staging failed: {exc}", file=sys.stderr)
        return 1
    print(f"Staged locally at {destination} (not a capability test).")
    print(f"Archive SHA-256: {sha256(args.archive)}")
    for path in files:
        if path.suffix.lower() in MODEL_EXTENSIONS:
            print(f"Model: {path} | SHA-256: {sha256(path)}")
    if skipped:
        print(f"Skipped {len(skipped)} unsupported entries; inspect the original ZIP for provenance/other files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
