#!/usr/bin/env python3
"""Fruit-Fly local character asset inventory.

This tool does not copy, modify, or upload model assets. It only inventories
files already present in a local directory and records information useful for
renderer selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FORMATS = {
    ".vrm": "VRM",
    ".vrma": "VRMA",
    ".glb": "glTF Binary",
    ".gltf": "glTF JSON",
    ".fbx": "FBX",
    ".blend": "Blender",
    ".obj": "OBJ",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_file(path: Path, root: Path) -> dict:
    stat = path.stat()
    suffix = path.suffix.lower()
    item = {
        "path": str(path.relative_to(root)),
        "format": FORMATS.get(suffix, "unknown"),
        "extension": suffix,
        "size_bytes": stat.st_size,
        "sha256": sha256(path),
        "renderer_metadata": {
            "has_animation_data": "unknown",
            "has_skeleton": "unknown",
            "has_humanoid_rig": "unknown",
            "has_morph_targets": "unknown",
            "has_materials": "unknown",
            "has_textures": "unknown",
            "has_expressions": "unknown",
            "has_eye_look_at": "unknown",
            "has_physics": "unknown",
            "notes": [],
        },
    }
    if suffix == ".fbx":
        item["renderer_metadata"]["notes"].append(
            "Compatibility must be verified by importing into the candidate renderer; FBX is not self-describing enough for this scanner."
        )
    elif suffix in {".glb", ".gltf"}:
        item["renderer_metadata"]["notes"].append(
            "glTF-family asset: inspect scene nodes, skins, animations, morph targets, materials, and external textures during renderer spike."
        )
    elif suffix == ".vrm":
        item["renderer_metadata"]["notes"].append(
            "VRM asset: renderer must support VRM runtime semantics, humanoid rig, expressions, and look-at behavior as required."
        )
    elif suffix == ".vrma":
        item["renderer_metadata"]["notes"].append(
            "VRMA animation asset: verify compatible VRM runtime and retargeting workflow."
        )
    return item


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory Fruit-Fly character assets")
    parser.add_argument("root", nargs="?", default="characters/local", help="Directory to scan")
    parser.add_argument("--output", default="model-inventory.json", help="Output JSON path")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Directory does not exist: {root}")

    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in FORMATS)
    inventory = {
        "schema_version": 1,
        "root": str(root),
        "asset_count": len(files),
        "assets": [inspect_file(p, root) for p in files],
    }

    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(f"Fruit-Fly model inventory: {len(files)} asset(s)")
    print(f"Wrote: {output}")
    for asset in inventory["assets"]:
        print(f"- {asset['path']} [{asset['format']}] {asset['size_bytes']} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
