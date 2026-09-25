# Tools

## Model inventory

Run from the repository root:

```bash
python3 tools/model_inventory.py characters/local --output model-inventory.json
```

The scanner is intentionally conservative. It records file format, size, and a SHA-256 hash, but it does **not** claim that an asset has a skeleton, animations, morph targets, or expressions without a real importer proving it.

Keep proprietary/local character assets under `characters/local/`. They are ignored by Git by default.
