# FF-02C Runbook — Target-Machine Validation

Status vocabulary: `PASS` = ran and met condition; `FAIL` = ran and did not;
`PENDING` = needs target/manual evidence; `UNKNOWN` = insufficient evidence;
`BLOCKED` = dependency unavailable; `SKIPPED` = not applicable.

Never mark PASS because a command exists. Never convert "not tested" into PASS.
Zero clips from one importer is `UNKNOWN`, never `NO ANIMATION`.

## What was implemented

- `scripts/ff02c-validate.sh` -> `scripts/ff02c_validate.py` (stdlib only):
  environment collection, `characters/local/` discovery + SHA-256 (in place,
  never uploaded/copied), Three.js probe presence/dependency check, Godot probe
  execution on already-staged `probes/godot-ff02/local/*.fbx` only, texture
  filename-match report, animation/structure aggregation, performance sanity
  snapshot, overlay precondition check, sanitization, consolidated report.
- `scripts/ff01-overlay-test.sh`: builds/runs existing `apps/overlay-linux`
  in the foreground, prints `OVERLAY_PID`, never daemonizes silently.
- Artifacts (gitignored): `artifacts/ff02c/{environment.txt,assets.json,
  threejs.json,godot.json,texture-report.json,animation-structure.json,
  performance.json,overlay.txt,FF-02C-REPORT.md}`.
- Tests: `tests/test_ff02c_validation.py` (fixtures only, never real models).

## What is automated / manual / optional

- Automated: env probing (missing commands -> unavailable), asset hashing,
  probe file/dependency presence, Godot CLI on pre-staged copies, texture
  string-match, report scaffolding with PENDING/UNKNOWN/BLOCKED.
- Manual (target machine): Three.js browser import (file picker, visual pose,
  clips, morphs), Godot editor visual inspection, FF-01 overlay visuals
  (transparency, layer, position, mouse, workspaces, multi-monitor, input
  capture), Ctrl+C SIGINT test, FPS/VRAM/CPU/GPU measurement.
- Optional deps: `godot`, `chromium`, `nvidia-smi`, `vulkaninfo`, `hyprctl`,
  `gtk4`, `gtk4-layer-shell`, `rust`/`cargo`, `node`/`npm`. Absence -> BLOCKED/UNKNOWN.

## Target workflow

### Step 1 — Update repository

```bash
git pull
```

### Step 2 — Verify local assets exist

```bash
find characters/local -maxdepth 3 -type f
```

Licensed assets only. Nothing is uploaded or committed.

### Step 3 — Install only documented prerequisites if missing

Do not auto-install large SDKs (notably Godot). Use system packages:

```bash
# Arch example (target):
sudo pacman -S --needed rust gtk4 gtk4-layer-shell nodejs npm chromium godot
```

Skip anything unavailable; the harness records BLOCKED.

### Step 4 — Run validation harness

```bash
./scripts/ff02c-validate.sh
```

Inspect `artifacts/ff02c/FF-02C-REPORT.md`. All paths sanitized (`$HOME`).

### Step 5 — Three.js manual import

```bash
npm ci --prefix apps/avatar-renderer/probes/ff02
python3 -m http.server 8765 --bind 127.0.0.1 --directory apps/avatar-renderer/probes/ff02
```

Open `http://127.0.0.1:8765/` on the same machine, select one FBX plus its
textures, click Import locally, record meshes/bones/clips/morphs/missing
textures and visual observations.

### Step 6 — Godot manual comparison (same FBX)

```bash
mkdir -p apps/avatar-renderer/probes/godot-ff02/local
cp characters/local/<candidate>/source/*.fbx apps/avatar-renderer/probes/godot-ff02/local/
cp characters/local/<candidate>/textures/*.png apps/avatar-renderer/probes/godot-ff02/local/
godot --version
godot --headless --path apps/avatar-renderer/probes/godot-ff02 --import
godot --headless --path apps/avatar-renderer/probes/godot-ff02 --script res://probe.gd -- res://local/<model.fbx>
godot --editor --path apps/avatar-renderer/probes/godot-ff02
```

Clear `godot-ff02/local/` between candidates. Record importer log + visuals.

### Step 7 — FF-01 overlay test

```bash
./scripts/ff01-overlay-test.sh
```

Manually inspect: transparent overlay, layer, position, mouse, workspace,
multi-monitor. Note the printed `OVERLAY_PID`.

### Step 8 — Ctrl+C test

1. Launch overlay, note PID. 2. Press `Ctrl+C` in the launching terminal.
3. Verify process termination, record exit code, verify prompt returns,
4. Verify no child remains (`ps -p <PID>` should fail).

`Ctrl+C` is terminal SIGINT. `Super+C` is a compositor shortcut. They are
NOT equivalent — record them separately.

### Step 9 — Send the sanitized report back

```bash
cat artifacts/ff02c/FF-02C-REPORT.md
```

Assets stay local. No asset upload is required. No telemetry is used.

## Asset protection / security

- Only `characters/local/` is read; never `$HOME`, never the filesystem root.
- Hashing reads files in place; no copies, no uploads, no `curl | sh`.
- Reports are sanitized: `$HOME` for home paths, `$USER`/`$HOST` for
  names, `[REDACTED]` for keys/tokens/secrets/private keys.
- `artifacts/ff02c/` is gitignored. Never commit proprietary models.
