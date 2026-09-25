# FF-02 — Real-asset import experiment and model inventory

Status: **PARTIALLY TESTED — renderer decision PENDING** (2026-09-25). Goal: find out whether Fruit-Fly's real local character files can be *imported* and rendered before selecting a 3D engine. This is a **paired FBX importer probe**, not a desktop avatar or renderer commitment.

## Inputs and asset boundary

The baseline checkout contained **two tracked ZIPs at the repository root**, contrary to ADR-0003. Both archives passed ZIP CRC inspection; neither contained a license/redistribution statement in its member list. Staging was restricted to ignored `characters/local/`, and the original ZIPs were **removed from the Git index only** (`git rm --cached`), not deleted from this machine. **The baseline Git history still contains them. Do not publish/push this repository as a clean asset-free open-source history without resolving rights and purging the affected history or starting from a clean public history.** Do not publish screenshots, converted models or downloaded third-party character assets. The user's separate original Goth Mommy model was **not found** in this checkout.

| Candidate | Source evidence (local only) | FBX bytes | FBX SHA-256 | Inventory capability fields |
|---|---|---:|---|---|
| Columbina | `columbina-rigged-free.zip` → `characters/local/columbina/source/*.fbx`; 6 PNGs | 2,817,136 | `b9c0168a83f52bbcfbf1dc6f73829c52f1f6822a761af2140341fddb21b296b9` | All `unknown` |
| Furina | `genshin-impact-furina.zip` → `characters/local/furina/source/*.fbx`; 4 PNGs | 10,273,996 | `e1349749e0c234d777404500ab17287f33a2726a05cd72f0f4711ed18bc879b4` | All `unknown` |
| Original Goth Mommy | No model in supplied workspace | — | — | `unknown` |

The archives have `.fbx` binary headers, but neither the ZIP name nor format proves rig suitability or rights. The inventory tool records format/extension/bytes/hash; skeleton, humanoid mapping, animation, materials, textures, morphs, expressions, eye/look-at and physics stay **`unknown` in the scanner**, regardless of importer findings below. Per-candidate licensing provenance is **UNKNOWN** and must be established before any redistribution.

## Implementation of the smallest comparison

- `tools/ff02_stage_archive.py`: optional bounded, local ZIP staging; checks archive paths, symlinks, entry sizes/compression, refuses overwrites; never executes entries. `tools/model_inventory.py` remains metadata-only.
- `apps/avatar-renderer/probes/ff02/`: pinned Three.js **0.186.1** static browser import bench. Reads the FBX and selected texture files via File API, substitutes a visible warning/placeholder for missing paths, and never requests model-supplied external URLs. Logs imported mesh/bone/material/morph/clip data; renders with alpha, orbit camera and single morph/clip controls. **Only the static bench is served**, not local assets.
- `apps/avatar-renderer/probes/godot-ff02/`: isolated Godot 4.3+ `ufbx` project and read-only headless scene probe; `local/` and `.godot/` are ignored and are **outside** the served browser directory. This comparator has **not** been executed here.

### Repeat the test on a machine with the assets

```bash
# If the archives are still available locally, stage them once (no overwrite):
python3 tools/ff02_stage_archive.py /path/to/furina.zip --candidate furina
python3 tools/ff02_stage_archive.py /path/to/columbina.zip --candidate columbina
python3 tools/model_inventory.py characters/local --output characters/local/inventory.json

npm ci --prefix apps/avatar-renderer/probes/ff02
# Serve ONLY this static folder. Bind to 127.0.0.1 for private local use.
python3 -m http.server 8765 --bind 127.0.0.1 --directory apps/avatar-renderer/probes/ff02
```

Open `http://127.0.0.1:8765/` **on the same machine**. Select one FBX, then select PNGs from that candidate's `textures/` directory. Click **Import locally**. Inspect the entire model/face in the orbit view, try any imported clips/morphs, read the missing-texture list and copy findings into [the FF-02 checklist](FF-02-IMPORT-CHECKLIST.md). If assets are already extracted into `characters/local/`, skip staging. The browser-only file picker cannot read this sandbox's assets from a remote preview; select files on the machine running the browser. No proprietary files or screenshots need to be committed.

For **the same FBX** in Godot 4.3+ on the target machine:

```bash
mkdir -p apps/avatar-renderer/probes/godot-ff02/local
# Example: copy the model and its PNGs into this ignored directory, WITHOUT changing the originals.
cp characters/local/furina/source/FurinaV2.fbx apps/avatar-renderer/probes/godot-ff02/local/
cp characters/local/furina/textures/*.png apps/avatar-renderer/probes/godot-ff02/local/
godot --version
godot --headless --path apps/avatar-renderer/probes/godot-ff02 --import
godot --headless --path apps/avatar-renderer/probes/godot-ff02 --script res://probe.gd -- res://local/FurinaV2.fbx
# Then launch the editor and VISUALLY inspect the imported scene and animation player:
godot --editor --path apps/avatar-renderer/probes/godot-ff02
```

Repeat using Columbina's FBX/PNGs after **clearing the ignored `godot-ff02/local/` manually** to avoid mixing textures. Capture the full importer log (warnings matter) and private screenshots. Run `--import` *before* the read-only probe. Godot reports `FF02_RESULT` on success; no successful parse alone establishes usable textures, expressions or animation. Check that this project uses its own ignored cache, never enables downloaded plugins, and does not run with unnecessary OS privileges. [Godot CLI import reference](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html) [1](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html)

## Tests and observations in this sandbox (Debian 12, Node 22.22.3)

| Test | Result | Evidence / limits |
|---|---|---|
| Bounded ZIP staging + inventory of both real FBXs | **PASS — tested** | Each archive staged only model+PNGs locally, 2 files inventoried with SHA-256; scanner fields remain unknown. 7 `unittest` cases for extraction/path safety and unknown fields passed. |
| Three.js r186 / Chromium 153 headless FBX parse and WebGL draw | **PASS — tested for parse/draw calls** | Both models parsed and generated a draw call; no browser console/page errors. Browser used **SwiftShader (software)**, not the target NVIDIA/Wayland system. Local `blob:` URLs handled selected textures; no external HTTP model requests observed. |
| Furina in Three | **PASS — importer data observed; visual fidelity UNKNOWN** | 1 mesh / 1 skinned mesh, 240 named bone nodes, 5 materials, 60 named morph channels, **0 imported animation clips**, no unresolved texture requests in the probe. A software-browser screenshot shows an upright, colored *rest/T-pose*; comparison to the source and material correctness are **UNKNOWN**. One selected morph changed 65 rendered pixels in the probe; expression correctness is **UNKNOWN**. |
| Columbina in Three | **FAIL — tested for texture resolution in this probe** | 17 meshes / 11 skinned meshes, 183 named bone nodes, 12 materials, 47 named morph channels, **0 imported clips**. **33 texture references unresolved** in this probe despite selecting the six bundled PNGs (missing files and/or mismatched reference names). Screenshot shows a largely near-black silhouette; correct materials are **not** established. A selected brow morph had no detectable pixel change in the software capture; expression function is **UNKNOWN**, not a proven absence. |
| Idle/gesture playback and animation switching | **FAIL — current imported files provide no clips in Three** | Neither FBX yielded an `AnimationClip`; additional local animation assets or a retargeting/authoring path are needed. No assumption about the original source data beyond this import. |
| Headless Godot `ufbx` import, visual comparison, packaging | **PENDING — environment unavailable** | No Godot executable installed; attempting official 4.7.2 release binary download returned EOF in this sandbox. The GDScript probe has **not** been executed/validated here. |
| Original Goth Mommy import | **PENDING — asset unavailable** | No original character file found; primary personality remains a separate future behavior-layer requirement, not a reason to invent a model. |
| Arch + Hyprland + NVIDIA + 60 FPS/VRAM/CPU/GPU + native transparency/passthrough | **PENDING — environment unavailable** | Sandbox has no Wayland session/NVIDIA hardware/Rust toolchain. Headless software draw calls are **not** native overlay or performance acceptance. FF-01 SIGINT must still be verified on the owner's machine. |

## Review and next decision

**What failed:** Three's current Columbina import references absent/mismatched texture names; both imports have no clips. The Goth Mommy asset and Godot/Wayland measurements are unavailable. There is no evidence yet to choose a renderer or to pass the FF-01 compositor checklist.

**One next milestone — FF-02B:** on the **actual Arch/Hyprland machine**, run the same asset through Godot's importer and the browser probe, collect side-by-side visual/texture/bone/clip evidence, and obtain an original/licensable avatar + an idle clip (or document the authoring path). Only then prototype the preferred renderer-to-layer-shell handoff and measure idle performance. Keep the LLM, voice and computer control disabled.
