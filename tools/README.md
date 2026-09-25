# Tools

## Local FF-02 archive staging (optional)

The initial checkout had two character ZIPs at its root. They are now untracked and ignored, but **still exist in the baseline Git history**; resolve rights and purge that history before public distribution. For privately held archives, from the repository root:

```bash
python3 tools/ff02_stage_archive.py /path/to/your-furina.zip --candidate furina
python3 tools/ff02_stage_archive.py /path/to/your-columbina.zip --candidate columbina
```

The helper checks archive paths, entry types and sizes; it refuses to overwrite existing candidate folders and stages only models, textures and provenance text. It neither executes nor validates assets. Work with downloaded models in an isolated, unprivileged development environment.

## Model inventory

Run from the repository root:

```bash
python3 tools/model_inventory.py characters/local --output characters/local/inventory.json
```

The scanner is intentionally conservative. It records format, extension, size and SHA-256; **all** runtime capability fields (skeleton/humanoid, animations, morphs, materials, textures, expressions, eye/look-at and physics) remain `unknown` until tested with actual importers. Write inventory output inside `characters/local/` as well if it includes private local paths.

Keep proprietary/local character assets under `characters/local/`. They are ignored by Git by default.
