# Fruit-Fly

Research/implementation project for a **local-first 3D desktop companion** on Arch Linux + Wayland + Hyprland. It is **not** yet an AI assistant or usable avatar. The character's personality, model, renderer and OS capabilities are separate layers; no LLM gets direct OS/shell access.

## Current engineering status

- **FF-01:** Rust/GTK4/gtk4-layer-shell debug overlay exists. Transparency, pointer passthrough, multi-monitor, performance and terminal `Ctrl+C` behavior still need real Arch + Hyprland testing; see [FF-01 report](docs/development/FF-01-TEST-REPORT.md).
- **FF-02:** metadata inventory and a local FBX import comparison experiment are available. Two provided FBXs parsed in a software-browser Three.js probe, but the Godot and native Wayland comparisons are pending; see [FF-02 evidence](docs/development/FF-02-MODEL-INVENTORY.md) and the undecided [renderer ADR](docs/decisions/ADR-0002-renderer.md).
- Brain, vision, voice, memory, personality and computer control are **not operational**. The existing policy module is a stub, not a security boundary ready to drive the OS.

## Local-only assets

Put licensed-for-your-use models under ignored `characters/local/`; never commit them or private screenshots. **The baseline history already contains two candidate ZIPs without verified redistribution rights**. They have been untracked without deleting local originals, but the affected *history* must be resolved before public release; see [asset ADR](docs/decisions/ADR-0003-character-assets.md). The original Goth Mommy character asset is not present in this checkout.

## Development entry points

```bash
python3 scripts/smoke_test.py
python3 -m unittest discover -s tests -p 'test_ff02_*.py' -v
```

See [the isolated importer instructions](apps/avatar-renderer/README.md), [overlay instructions](apps/overlay-linux/README.md) and [architecture audit](docs/architecture/system-design.md). Do not treat import data as proof of usable animation or a correct-looking avatar.
