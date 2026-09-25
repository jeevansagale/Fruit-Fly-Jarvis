# FF-02B — Environment and asset provenance

Date: **2026-09-25**. Audit began **10:50:59 UTC**. The environment below is the **Arena sandbox**, **not** the owner's Arch/Hyprland/NVIDIA machine. Do not transfer any PASS from this sandbox to the target-machine acceptance checklist. No OS packages, new models, conversions, or extensions were installed during this cycle.

## Actual environment (observed commands)

| Check | Exact command | Observed output / status |
|---|---|---|
| Kernel/architecture | `uname -a` | `Linux e2b.local 6.1.158+ #1 SMP PREEMPT_DYNAMIC Mon May 11 18:48:24 UTC 2026 x86_64 GNU/Linux` — **PASS — tested** (environment identified) |
| Distribution | `cat /etc/os-release` | `PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"`, `VERSION_ID="12"` — **PASS — tested** (not Arch) |
| Hyprland | `hyprctl version` | `hyprctl: unavailable` — **PENDING — environment unavailable** |
| Session | `echo "$XDG_SESSION_TYPE"`, `echo "$WAYLAND_DISPLAY"`, `echo "$XDG_CURRENT_DESKTOP"`, `echo "$XDG_SESSION_DESKTOP"` | All four variables **unset**; no Wayland/Hyprland desktop session — **PENDING — environment unavailable** |
| NVIDIA / driver / CUDA | `nvidia-smi` | Command unavailable; no `/dev/nvidia*` device exposed. Driver and CUDA versions **UNKNOWN — insufficient evidence**; target GPU test **PENDING — environment unavailable** |
| Vulkan | `vulkaninfo --summary` | Command unavailable; `/dev/dri` absent — **PENDING — environment unavailable** |
| Godot | `godot --version` | Command unavailable; **PENDING — environment unavailable**. Do not infer an installed version from online documentation. |
| Chromium | `chromium --version` | No system Chromium binary. A **temporary**, sandbox-only `/tmp/chromium` reports **`Chromium 153.0.8010.0`** when run with its matching temporary libraries. This is **not** the target browser/version. |
| Three.js | `node -p 'require("./apps/avatar-renderer/probes/ff02/node_modules/three/package.json").version'` | **`0.186.1`** (existing FF-02 probe dependency); browser reports `FBXLoader r186`. |
| Node / npm / pnpm | `node --version`; `npm --version`; `pnpm --version` | **v22.22.3**; **10.9.8**; pnpm unavailable. |
| Rust / Cargo | `rustc --version`; `cargo --version` | Both commands unavailable; FF-01 cannot be run here. |
| GTK4 / gtk4-layer-shell | `pkg-config --modversion gtk4 gtk4-layer-shell` | `pkg-config` unavailable; library versions **UNKNOWN — insufficient evidence**. No GTK overlay execution here. |
| Sandbox CPU/memory | `lscpu`; `free -h` | **2 vCPUs** (Intel Xeon @ 2.60 GHz as reported), **3.8 GiB RAM**. Not target-hardware performance data. |

**Blocker:** the required combination `Arch + Wayland + Hyprland + NVIDIA + Godot + Rust/GTK` is not accessible from this checkout. Repeating software-Chromium renders or installing Godot into this sandbox would not validate its Wayland overlay or NVIDIA costs. Godot/overlay/GPU/SIGINT target tests are therefore **PENDING — environment unavailable**; no substitute machine is claimed.

## Original assets found (read-only audit)

Existing original ZIPs are at repository root on this machine; extracted **working copies** already exist under ignored `characters/local/`. The FBX originals and their hashes match the previous FF-02 record. This cycle only read files; it did **not** rewrite, convert, or copy originals into the served web directory. Each candidate has one FBX and the PNGs listed below. Directory inspection found **no separate animation files or material sidecars** (`.vrma`, `.bvh`, additional `.fbx`, `.mtl`, `.material`, `.tres`, `.mat`, etc.) in either candidate directory or the original ZIP member lists. That does **not** prove the FBXs have no embedded animation/material information.

| Candidate | Local extracted working copy (ZIP kept unchanged) | Size (bytes) | SHA-256 | Associated files | Format |
|---|---|---:|---|---|---|
| Furina | `characters/local/furina/source/FurinaV2.fbx` | 10,273,996 | `e1349749e0c234d777404500ab17287f33a2726a05cd72f0f4711ed18bc879b4` | `textures/体.png` (2,704,092 B), `颜.png` (706,073 B), `髮.png` (1,689,215 B), `髮2.png` (689,369 B) | FBX binary v7400 (header observation) |
| Columbina | `characters/local/columbina/source/NPC_Avatar_Girl_Catalyst_Columbina.fbx` | 2,817,136 | `b9c0168a83f52bbcfbf1dc6f73829c52f1f6822a761af2140341fddb21b296b9` | `textures/Avatar_Girl_Catalyst_Columbina_Tex_Body_Di.png` (971,613 B), `Dress_D.png` (954,184 B), `Face_Di.png` (143,629 B), `Hair_Di.png` (749,393 B), `Veil_Di.png` (120,082 B), `Eff_Noise_28.png` (77,271 B); full first five filenames share the `Avatar_Girl_Catalyst_Columbina_Tex_` prefix. | FBX binary v7300 (header observation) |
| Original Goth Mommy | **NOT PRESENT** under `characters/local/`, the root, or supplied archives | — | — | None found | **BLOCKED — asset absent** |

Directory paths and ZIP member names are metadata, not a redistribution license. Original ZIPs remain local and ignored; do **not** upload them or the generated `characters/local/ff02-*.png` screenshots. `characters/local/inventory.json` and screenshots are ignored prior-run evidence, not new source assets. Source ownership and redistribution rights remain **UNKNOWN — insufficient evidence**.

### Hash verification and no-conversion record

- Asset metadata obtained from read-only `stat`, `hashlib.sha256`, `zipfile.infolist()` and FBX header bytes; FBX hashes agree with [FF-02 inventory](FF-02-MODEL-INVENTORY.md).
- No conversion was performed: `original/working-copy/converted` lineage is **not applicable** in FF-02B. Do not create a converted file without recording source hash, conversion tool/version/command and output hash in a future run.
- On the owner's target machine, run the same inventory command against **local ignored copies**: `python3 tools/model_inventory.py characters/local --output characters/local/inventory.json`. Retain full directory listings and sidecar SHA-256s privately.

## Asset history/security audit

`git status --short --branch` was clean at cycle start on `arena/01a0d818-fruit-fly-jarvis` (`bb20610`); `git ls-files '*.zip' characters/local` returned nothing. `git log --all --stat -- columbina-rigged-free.zip genshin-impact-furina.zip` shows **9a0c3ce** introduced both binary ZIPs (5,834,552 and 16,063,315 bytes) and **bb20610** deleted them from the tracked tree. `git ls-tree` at the baseline confirms their presence; current root ZIPs are ignored but remain on this machine. **Current-tree removal is not history removal.**

Recommended separate publication procedure, **not executed here**: have the owner establish rights; if redistribution is restricted, coordinate a clean-history repository or a reviewed mirror-clone `git-filter-repo` plan for all refs/tags, GitHub cached copies/forks and collaborator reclones. Do **not** rewrite history, force-push, or assume this PR by itself makes a public repository asset-free. Protect access/coordinate with the owner if exposure is sensitive.

The unrelated existing brain-service `.allowed`/tuple issue is tracked as **FF-BRAIN-001**, out of scope; no brain code was modified.
