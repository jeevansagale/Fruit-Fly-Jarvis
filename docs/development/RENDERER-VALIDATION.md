# Renderer validation (target machine)

## Three.js (Firefox, manual)
- Furina FBX loaded, character visibly rendered, textures appear usable, no
  silhouette failure. 0 imported clips. Role: comparison probe (kept).

## Godot 4.7.2 (headless CLI, automated)
- `--import`: DONE, 0 error/fail lines; 4 PNGs + FBX reimported cleanly.
- Probe `FF02_RESULT`: parsed; 1 mesh instance, 5 surface materials,
  1 Skeleton3D with 240 bones (Head/Neck/Eye_L/Eye_R confirmed),
  60 blend shapes (facial set incl. blink), 0 clips.
- Runtime (`apps/avatar-renderer/runtime/`, transparent + gl_compatibility):
  loads Furina, skeleton=true, head_bone=4, blink_targets=1, 60s run with no
  ERROR lines; applies polled expression/animation/look_at commands.

## Decision
Godot native runtime. Decisive (not preferential): native window with
transparency needs no invented browser→layer-shell bridge; importer +
runtime proven on the same asset on target. Revisit only with new evidence.

## Still manual
On-screen avatar look, material fidelity, FPS/VRAM on NVIDIA, overlay
compositing of the Godot window, Ctrl+C of each process.
