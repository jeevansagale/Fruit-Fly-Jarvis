# Fruit-Fly Status (living)

## Vertical slice: IMPLEMENTED + TESTED (GUI visuals PENDING observation)
- `./Run.sh --dev`: brain HTTP + mock events + headless Godot avatar, one
  command, no display, no external network, no keys. Verified: behavior
  IDLE→…→IDLE, neuro drive signal (calm/alert/social WTA) live per event,
  look_at commands queued and applied by the avatar,
  policy allow/deny/confirm, controller denies unwired intents honestly.
- `./Run.sh --check`: all unit/integration tests in tests/ + brain/smoke. Green.
- Overlay: compiles + launches on target (PID 37041 observed before); visual
  + Ctrl+C re-verification PENDING human run.

## Renderer decision: Godot native runtime
Evidence: headless Furina import (1 mesh, 5 materials, 240 bones incl.
Head/Neck/Eye_L/Eye_R, 60 blend shapes, 0 clips, 0 errors); runtime loads
with skeleton + blink target, 60s error-free; transparent window configured.
Three.js: target-Firefox visual render proven, kept as probe.

## Mocks vs real
- IMPLEMENTED: contracts, behavior SM, policy+controller, character runtime,
  brain HTTP, Godot runtime, Hyprland adapter, logging.
- MOCK: voice in/out, brain reasoning (scripted events).
- IMPLEMENTED (needs user camera run): hand tracking — MediaPipe
  HandLandmarker backend, poses palm/fist/pinch/point, swipes with cooldowns,
  gesture→capability map (swipes→workspace/scroll, pinch→media toggle),
  all policy-gated. Live path BLOCKED in agent sandbox (native TFLite init
  SIGKILL); run `python3 scripts/vision_check.py` in your terminal.
- PENDING: overlay visuals, Ctrl+C re-verify, avatar on-screen look,
  STT/TTS, camera inference, memory persistence.

## Known limitations
- Furina has 0 imported clips → procedural idle fallback (by design).
- 3/3 texture filename refs unresolved; Firefox visual looked usable;
  Godot material visual PENDING editor check.
- Brain HTTP has no auth (localhost-only); pyyaml required by runtime.
- Baseline git history still contains unlicensed ZIPs (separate milestone).
