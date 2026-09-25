# FF-02B — Controlled renderer validation result

**Renderer decision: KEEP PENDING.** Cycle: 2026-09-25; target-machine validation **PENDING — environment unavailable**. [Exact machine/version report](FF-02B-ENVIRONMENT.md). Previous FF-02 software-browser evidence is retained, not promoted to an Arch/Hyprland/NVIDIA PASS. This cycle ran the **existing** Three.js bench against the two local FBXs; Godot and FF-01 could not run here. No production renderer, brain, OS-control logic, new model, conversion, or new dependency was added. ADR-0002 remains [PENDING](../decisions/ADR-0002-renderer.md); its decision has **not** been changed.

Status vocabulary: **PASS — tested**, **FAIL — tested**, **PENDING — environment unavailable**, **UNKNOWN — insufficient evidence**, **BLOCKED — dependency/asset prevents test**. The qualifier **sandbox only** is mandatory for the Three.js PASSes below.

## 1. Environment report

**PASS — tested:** the machine is Debian 12 (kernel 6.1.158+, 2 vCPUs, 3.8 GiB RAM); Node v22.22.3, npm 10.9.8, temporary Chromium 153.0.8010.0 with software rendering, Three.js r186. **PENDING — environment unavailable:** Arch, Hyprland, Wayland session, NVIDIA driver/GPU, Godot executable, Rust/Cargo, GTK4/gtk4-layer-shell and Vulkan tools. Driver/CUDA/library versions are **UNKNOWN — insufficient evidence**, not inferred. See the exact command table in [FF-02B-ENVIRONMENT.md](FF-02B-ENVIRONMENT.md). The missing target environment is the stopping blocker; no replacement stack was installed.

## 2. Asset report

**PASS — tested (metadata only):** Furina FBX (10,273,996 bytes, SHA-256 `e1349749e0c234d777404500ab17287f33a2726a05cd72f0f4711ed18bc879b4`), Columbina FBX (2,817,136 bytes, SHA-256 `b9c0168a83f52bbcfbf1dc6f73829c52f1f6822a761af2140341fddb21b296b9`) and their four/six PNGs exist in ignored local folders; original ZIPs remain locally available. No standalone animation/material sidecar found in either archive or staged candidate directory. **BLOCKED — asset absent:** original Goth Mommy candidate **NOT PRESENT**. No original or texture was modified or publicly served.

## 3. Three.js report — same files, existing bench, **sandbox only**

Procedure: existing `apps/avatar-renderer/probes/ff02/` static server, Chromium File API selection of each FBX and exactly its supplied PNGs, `FBXLoader r186` via Three.js 0.186.1. No asset path was requested by HTTP; Playwright's observed browser `pageerror` count and off-origin HTTP requests were both **0**. The bench substitutes a placeholder for missing image references. It reports a successful draw call, not a visually accepted character. No pure parser timing or total Object3D count is instrumented: both **UNKNOWN — insufficient evidence** (do not substitute browser click latency).

| Import observation | Furina | Columbina |
|---|---|---|
| FBX parse + rendered frame | **PASS — tested (sandbox only)** | **PASS — tested (sandbox only)**; draw is **not** material correctness |
| Meshes / skinned meshes | **1 / 1** | **17 / 11** |
| Distinct imported bone names | **240** | **183** |
| Imported materials / texture references on materials | **5 / 5** | **12 / 13** |
| Imported named morph channels | **60** | **47** |
| Imported animation clips | **0** | **0** |
| Unresolved texture requests | **0** in this loader path | **33** (see §7) |
| Importer fatal errors / page errors | **0 observed** | **0 observed**; missing-texture warning shown |
| Pure parse time / total object count | **UNKNOWN — insufficient evidence** | **UNKNOWN — insufficient evidence** |

A previous private screenshot showed an upright, colored Furina rest pose and a largely dark Columbina silhouette in **software** rendering. Neither proves source-accurate scale, normals, textures, alpha, animation quality, or target GPU behavior. A named bone is not a validated humanoid mapping.

## 4. Godot report

**PENDING — environment unavailable.** `godot --version` is unavailable, and there is no compositor/GPU target session; `apps/avatar-renderer/probes/godot-ff02/` is unchanged and unexecuted in this cycle. **Do not claim** Godot import, scene/skeleton/material/texture/blend-shape counts, importer warnings or clips. A previous attempt to obtain an official binary in this sandbox ended with a download EOF; this cycle did not repeat it or install an unrelated build. On the real machine, follow [existing Godot instructions](FF-02-MODEL-INVENTORY.md) with an ignored local copy, run `--import`, then the read-only GDScript probe and an editor visual check. If its importer errors, retain the exact log before a minimal fix; no speculative correction was made here.

## 5. Overlay report

**PENDING — environment unavailable:** no Wayland socket, `hyprctl`, Rust/Cargo, GTK4/gtk4-layer-shell, monitor metadata or NVIDIA output is accessible here. No transparency-on-desktop, overlay-layer, tiling/focus, pointer passthrough, workspace, multimonitor or renderer embedding tests were performed. Three's configured `alpha: true` **inside a canvas** is not evidence that an avatar can be composited by Hyprland; a default Godot window is also not the tested GTK layer-shell surface. [ADR-0002](../decisions/ADR-0002-renderer.md) records the relevant GTK-embedded, separate-layer surface and renderer-owned-window boundaries; architectures A/B/C remain **UNKNOWN — insufficient evidence** in this run. Keep the existing GTK FF-01 spike.

`cargo run --release` could not be executed here (**PENDING — environment unavailable**); neither terminal `Ctrl+C` exit code/process tree nor compositor shortcut `Super+C` was tested. Source inspection shows the existing SIGINT listener calls `std::process::exit(0)`; this is **not** proof of graceful teardown. `Ctrl+C` and `Super+C` are different tests.

## 6. Performance report

**PENDING — environment unavailable** for both renderers on Arch/NVIDIA. **No target FPS, frame time, CPU, GPU usage or VRAM measurement exists.** The bench's software-Chromium draw call is not a benchmark. Model-only (A), model+animation (B: no imported clip) and model+animation+transparency (C) were **not** measured on target hardware. Do not score 60 FPS or infer GPU cost from the sandbox.

## 7. Texture investigation — Columbina

**Observation:** the actual sandbox browser probe requested **33** names it could not resolve after all **six** bundled PNGs were selected. **Evidence:** `window.__ff02Report.unresolved_texture_requests` (33 entries), read-only scan of FBX binary's visible `Textures/…png` strings (all 33 matched a raw-visible path), `zipfile.infolist()`, and case-folded comparison to every supplied PNG basename (zero exact/case-only matches). This is not a mere directory-prefix or Linux capitalization fix. Some names (`*_Diffuse.png`) resemble included `*_Di.png`/`*_D.png`, but **semantic equivalence is unverified**; no textures were renamed or substituted. Missing entries include normal/light/ramp/mask/effect maps that have no evident bundled equivalents. The first two loaded image references seen in the previous probe do not establish the other materials are correct.

Each row gives the FBX-requested relative path and the case-folded basename the **current Three bench** uses to resolve selected local textures. For **all 33 rows**, the exact/case-folded local file path is **NONE** among `characters/local/columbina/textures/*.png`; the bench's resolved URI is an in-memory `data:image/png` **placeholder**, not a recovered image path; `case mismatch? NO`; `path-only mismatch? NO`. These are **absent from the supplied archive under their requested names**, not proof the *creator's entire* original texture package never contained them. Embedded/unsupported-texture behavior and Godot's independent resolution are **UNKNOWN — insufficient evidence**. Do not fix by copying arbitrary images.

| Requested path in FBX | Browser lookup basename (lowercase) | Actual exact/case-only local match |
|---|---|---|
| `Textures/Avatar_Girl01_Tex_FaceLightmap.png` | `avatar_girl01_tex_facelightmap.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Body_Diffuse.png` | `avatar_girl_catalyst_columbina_tex_body_diffuse.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Body_Lightmap.png` | `avatar_girl_catalyst_columbina_tex_body_lightmap.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Body_Normalmap.png` | `avatar_girl_catalyst_columbina_tex_body_normalmap.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Body_Shadow_Ramp.png` | `avatar_girl_catalyst_columbina_tex_body_shadow_ramp.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Dress_Diffuse.png` | `avatar_girl_catalyst_columbina_tex_dress_diffuse.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Dress_Lightmap.png` | `avatar_girl_catalyst_columbina_tex_dress_lightmap.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Dress_Shadow_Ramp.png` | `avatar_girl_catalyst_columbina_tex_dress_shadow_ramp.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Face_Diffuse.png` | `avatar_girl_catalyst_columbina_tex_face_diffuse.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Hair_Diffuse.png` | `avatar_girl_catalyst_columbina_tex_hair_diffuse.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Hair_Lightmap.png` | `avatar_girl_catalyst_columbina_tex_hair_lightmap.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Hair_Shadow_Ramp.png` | `avatar_girl_catalyst_columbina_tex_hair_shadow_ramp.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Columbina_Tex_Veil_Diffuse.png` | `avatar_girl_catalyst_columbina_tex_veil_diffuse.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Mualani_Tex_Mask.png` | `avatar_girl_catalyst_mualani_tex_mask.png` | NONE |
| `Textures/Avatar_Girl_Catalyst_Mualani_Tex_NyxState_Ramp.png` | `avatar_girl_catalyst_mualani_tex_nyxstate_ramp.png` | NONE |
| `Textures/Avatar_Tex_Appear_Face01_Mask.png` | `avatar_tex_appear_face01_mask.png` | NONE |
| `Textures/Avatar_Tex_Appear_Pupil_Mask.png` | `avatar_tex_appear_pupil_mask.png` | NONE |
| `Textures/Avatar_Tex_Face01_Shadow.png` | `avatar_tex_face01_shadow.png` | NONE |
| `Textures/Avatar_Tex_MetalMap.png` | `avatar_tex_metalmap.png` | NONE |
| `Textures/Avatar_Tex_Specular_Ramp.png` | `avatar_tex_specular_ramp.png` | NONE |
| `Textures/Eff_Avatar_Furina_13_06.png` | `eff_avatar_furina_13_06.png` | NONE |
| `Textures/Eff_Avatar_NyxState.png` | `eff_avatar_nyxstate.png` | NONE |
| `Textures/Eff_Mask_60.png` | `eff_mask_60.png` | NONE |
| `Textures/Eff_Mask_61.png` | `eff_mask_61.png` | NONE |
| `Textures/Eff_Matcap_Liquid_Bubble_06.png` | `eff_matcap_liquid_bubble_06.png` | NONE |
| `Textures/Eff_Noise_13.png` | `eff_noise_13.png` | NONE |
| `Textures/Eff_Noise_26.png` | `eff_noise_26.png` | NONE |
| `Textures/Eff_Sc_EdgeNoise_02_RougeTrap.png` | `eff_sc_edgenoise_02_rougetrap.png` | NONE |
| `Textures/Eff_Turbulence_09.png` | `eff_turbulence_09.png` | NONE |
| `Textures/Eff_Turbulence_13_02.png` | `eff_turbulence_13_02.png` | NONE |
| `Textures/Eff_Turbulence_27.png` | `eff_turbulence_27.png` | NONE |
| `Textures/Eff_Turbulence_29.png` | `eff_turbulence_29.png` | NONE |
| `Textures/Eff_Universe_12.png` | `eff_universe_12.png` | NONE |

**Inference:** **FAIL — tested** for *complete Columbina texture resolution in the supplied package with this Three import path*. Cause class **A (absent from supplied ZIP under requested names)** has direct evidence for all 33; **D (exporter/reference mismatch)** is plausible for the near-matching diffuse names but not verified; B/C path/case alone cannot fix absent basenames; E/F remain **UNKNOWN — insufficient evidence**. Furina's **0 unresolved lookups** is only a filename-resolution result, not a PASS for all shader/material properties (normal/roughness/metalness/emission/alpha need asset-specific visual tests). Godot texture result is **PENDING — environment unavailable**.

## 8. Animation investigation — zero imported clips

**Observation:** the Three.js loader returned **0 clips for both** in this and previous sandbox runs; each ZIP and local candidate folder contains only one FBX and PNGs, no animation sidecar. **Read-only binary clue:** headers identify FBX binary v7400 (Furina) and v7300 (Columbina); scanning their raw bytes found **0** occurrences of standard node-name strings `AnimationStack`, `AnimationLayer`, `AnimationCurveNode`, `AnimationCurve`, `KeyTime` or `KeyValueFloat`. These are *literal-byte scans*, **not** a validated full FBX semantic decode or independent Godot/Blender import. **Inference:** lack of an embedded clip is plausible; an importer limitation cannot yet be ruled out. **Decision:** actual idle/gesture playback and clip switching are **BLOCKED — dependency/asset prevents test**; source animation availability is **UNKNOWN — insufficient evidence** until Godot or another appropriate FBX inspector verifies stacks. Do not author, retarget or infer new clips here.

## 9. Character-control report

**Morph inventory: PASS — tested (sandbox only)** for naming/counting 60 Furina and 47 Columbina imported channels. The previous FF-02 software screenshot comparison found a 65-pixel change from a selected Furina morph weight and no detectable change for the selected Columbina brow in a mostly dark render; this establishes neither correct emotion mapping nor useful blinking/mouth control. Facial expression quality **UNKNOWN — insufficient evidence**. Imported bone-name examples: Furina `Eye_L`, `Eye_R`, `Head`; Columbina `+EyeBone_L_A01`, `+EyeBone_R_A01`, `Bip001_Head` (plus paired `_A02` bones). Eye bones are present in importer output, but active camera/cursor look-at, blink, eye limits and face/rig quality are **UNKNOWN — insufficient evidence**. No runtime look-at controller or animation system was built. Physics is **UNKNOWN — insufficient evidence**.

## 10. Side-by-side test matrix / security and Git report

Every cell either reports a direct observation or uses the required status vocabulary. `PASS (sandbox)` does **not** mean target-machine PASS.

| Capability | Three.js — Furina / Columbina | Godot 4 — same two assets |
|---|---|---|
| FBX import | **PASS — tested (sandbox only)** / **PASS — tested (sandbox only)**; actual imports and draw calls | **PENDING — environment unavailable** |
| Materials | **UNKNOWN — insufficient evidence** / **FAIL — tested** for full texture resolution; visual fidelity not established | **PENDING — environment unavailable** |
| Textures | 0 unresolved lookups, quality **UNKNOWN — insufficient evidence** / 33 missing, **FAIL — tested** | **PENDING — environment unavailable** |
| Skeleton / humanoid map | 240 / 183 named nodes; humanoid map **UNKNOWN — insufficient evidence** | **PENDING — environment unavailable** |
| Animation import/play/switch | 0 / 0 clips; playback **BLOCKED — dependency/asset prevents test** | **PENDING — environment unavailable** |
| Morph targets | 60 / 47 imported named channels, **PASS — tested (sandbox only)** | **PENDING — environment unavailable** |
| Facial expression quality | **UNKNOWN — insufficient evidence** / **UNKNOWN — insufficient evidence** | **PENDING — environment unavailable** |
| Eye control / look-at | Eye/head bone names present; runtime **UNKNOWN — insufficient evidence** | **PENDING — environment unavailable** |
| Transparent desktop background | WebGL alpha configured, Wayland composition **PENDING — environment unavailable** | **PENDING — environment unavailable** |
| Desktop layer-shell overlay | **PENDING — environment unavailable** | **PENDING — environment unavailable** |
| Workspace/focus/pointer | **PENDING — environment unavailable** | **PENDING — environment unavailable** |
| Multiple monitors | **PENDING — environment unavailable** | **PENDING — environment unavailable** |
| Idle FPS / frame time | **PENDING — environment unavailable** | **PENDING — environment unavailable** |
| VRAM / CPU / GPU use | **PENDING — environment unavailable** | **PENDING — environment unavailable** |
| Packaging / local relaunch | Static probe exists, production **UNKNOWN — insufficient evidence** | Isolated probe exists, **PENDING — environment unavailable** |
| Linux/Wayland integration | Browser on Debian is not Hyprland; **PENDING — environment unavailable** | **PENDING — environment unavailable** |
| Development complexity | Browser-side importer exists; overlay bridge **UNKNOWN — insufficient evidence** | Project scaffold exists; target import/bridge **UNKNOWN — insufficient evidence** |
| Original Goth Mommy | **BLOCKED — asset absent** | **BLOCKED — asset absent** |

Security/Git: **PASS — tested** for no tracked ZIPs in the current tree; **FAIL — tested** for being history-clean (baseline `9a0c3ce` still includes both). The existing PR only removes them from HEAD, not history; no history rewrite occurred. Rights remain **UNKNOWN — insufficient evidence**. See [exact Git/asset audit and recommended separate cleanup](FF-02B-ENVIRONMENT.md#asset-historysecurity-audit). **FF-BRAIN-001** (brain tuple/`.allowed`) is documented, out of scope.

## 11. Weighted renderer decision (no fictitious scoring)

| Engineering weight | Three.js evidence now | Godot evidence now |
|---|---|---|
| Asset compatibility 20% | Both FBXs parsed in sandbox; one texture package incomplete | **PENDING — environment unavailable** |
| Animation control 15% | 0 imported clips; no controllable idle | **PENDING — environment unavailable** |
| Facial/expression control 15% | Channels exposed, usability unknown | **PENDING — environment unavailable** |
| Overlay integration 20% | **PENDING — environment unavailable** (native layer shell) | **PENDING — environment unavailable** (native layer shell) |
| Linux/Wayland 10% | **PENDING — environment unavailable** (no target session) | **PENDING — environment unavailable** (no target session) |
| Performance 10% | **PENDING — environment unavailable** (no target GPU) | **PENDING — environment unavailable** (no target GPU) |
| Development complexity 5% | Browser prototype exists; bridge **UNKNOWN — insufficient evidence** | Godot scaffold exists; bridge **UNKNOWN — insufficient evidence** |
| Packaging/maintenance 5% | **UNKNOWN — insufficient evidence** (production not tested) | **UNKNOWN — insufficient evidence** (production not tested) |

These percentages are decision priorities, **not a numerical score**. **Critical blockers:** neither renderer has demonstrated the native transparent Wayland overlay path; Godot has not imported any real candidate; both lack demonstrated idle animation; the original licensable primary asset is absent. A weighted total cannot override those blockers. **KEEP PENDING** is the only defensible outcome. There is no evidence both renderers fail, so do **not** research a third option in this cycle.

## 12. Exactly one next milestone

**FF-02B target-machine evidence handoff:** run the **existing** Three and Godot import probes against the **same ignored local asset copies** on the owner's actual Arch/Hyprland/NVIDIA session; record versions, Godot importer logs/visuals, Three texture-path observations, idle clip evidence (or explicit absence), native overlay/`Ctrl+C` observations and a short model-only GPU sanity measurement. Return **sanitized logs and numerical observations only**; never upload, serve or commit character binaries/screenshots without redistribution rights. Then revisit ADR-0002. This is one execution gate, **not** a renderer selection or a new feature roadmap.
