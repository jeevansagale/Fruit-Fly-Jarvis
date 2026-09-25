# Fruit-Fly

Local-first 3D desktop companion for Arch Linux + Wayland + Hyprland.
Working vertical slice: desktop overlay + Godot avatar runtime + character/
behavior runtime + policy-gated capabilities + mock brain/voice/vision.
No LLM gets direct OS/shell access — ever.

## Architecture

Brain/Intents (HTTP, localhost) → Behavior engine → Character runtime →
Godot avatar renderer + GTK overlay. Capability requests → allowlist policy
with typed args → typed adapters (Hyprland). Voice/vision are mock
interfaces; memory is session-scoped. See
[system design](docs/architecture/system-design.md) and
[status](docs/development/STATUS.md).

## Requirements

Arch Linux, Wayland/Hyprland, Python 3.11+ (+pyyaml), Godot 4.7, Rust/cargo
for the overlay, Node for the Three.js probe. NVIDIA + Firefox verified on
target. No API keys, no network, no cloud.

## Installation

```bash
git pull
npm ci --prefix apps/avatar-renderer/probes/ff02   # probe only
```

Licensed character assets go under ignored `characters/local/` (never
committed). Furina layout: `characters/local/Furina/source/*.fbx` +
`characters/local/Furina/textures/*.png`. Baseline git history still
contains two unlicensed ZIPs — resolve before public release
([ADR-0003](docs/decisions/ADR-0003-character-assets.md)).

## Running

```bash
./Run.sh --dev     # one-command slice: brain + mock events + headless avatar
./Run.sh --check   # offline verification (tests + smoke)
./Run.sh --overlay # FF-01 overlay in foreground (Ctrl+C stops it)
./Run.sh --probe   # Three.js probe server (import in Firefox manually)
./Run.sh --validate# FF-02C target validation harness
```

Godot editor visual check:
`godot --editor --path apps/avatar-renderer/runtime` (manual observation).

## Development mode

`--dev` uses scripted events and mock providers; swapping in real STT/TTS/
vision means implementing `VoiceProvider`/`VisionProvider` interfaces in
`packages/perception/providers.py` — no architecture change.

## Character assets

Swap characters via YAML (`characters/*.yaml`): furina, columbina,
goth-mommy (personality config, no model yet). Runtime never imports a
renderer; renderer reads character data + procedural-idle parameters.

## Security model

Allowlisted capabilities with typed arguments and confirmation gates
(`packages/capability_policy/`); denied intents never reach adapters;
localhost-only HTTP; details in
[COMPUTER_CONTROL.md](docs/security/COMPUTER_CONTROL.md).

## Testing

```bash
python3 -m unittest discover -s tests -v   # 53 tests, all must pass
```

GUI/visual claims stay PENDING without human observation.

## Known limitations

Furina has 0 imported clips (procedural idle fallback active); texture
filename refs 3/3 unresolved but Firefox render looked usable; brain HTTP
has no auth; overlay visuals + Ctrl+C re-verify pending.

## Future work

Real STT/TTS, camera inference, persistent memory, overlay↔Godot window
compositing, FPS/VRAM budgets, renderer decision revisit only on new
evidence.
