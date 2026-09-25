# FF-02 Import Checklist

Run this once for **each** real candidate asset and **each** renderer on the target machine; record PASS — tested / FAIL — tested / PENDING — environment unavailable / UNKNOWN — insufficient evidence. Importer counts alone do not satisfy visual or rig checks. The first sandbox observations (Furina and Columbina in software Chromium; Godot and original Goth Mommy pending) are in [FF-02-MODEL-INVENTORY.md](FF-02-MODEL-INVENTORY.md). Do not publish candidate screenshots/models without confirmed rights.

## Identity

- [ ] Candidate name recorded
- [ ] Source/license recorded privately
- [ ] File format recorded
- [ ] File size recorded
- [ ] SHA-256 recorded

## Import

- [ ] Opens successfully
- [ ] No fatal importer errors
- [ ] Correct scale
- [ ] Correct orientation
- [ ] Materials render
- [ ] Textures resolve
- [ ] Skeleton/humanoid rig visible
- [ ] Idle animation works
- [ ] Additional animation works, if supplied
- [ ] Facial expressions/morph targets work, if supplied
- [ ] Blinking and mouth/viseme movement work, if supplied (or record absent)
- [ ] Eye bones/morphs and look-at/camera tracking work, if supplied
- [ ] Hair/clothing/accessory physics works, if supplied (or record absent)

## Runtime

- [ ] Overlay integration possible
- [ ] Animation switching stable
- [ ] No visible pose corruption
- [ ] Idle and animated FPS/frame time measured on target GPU
- [ ] VRAM, CPU usage and GPU usage measured on target hardware
- [ ] Packaging/relaunch repeatable

## Evidence

Record screenshots, terminal output, renderer/importer version, and any conversion steps. Do not mark an unknown capability as PASS merely because the file format commonly supports it.
