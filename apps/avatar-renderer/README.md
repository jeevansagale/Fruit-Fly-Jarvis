# Avatar renderer — FF-02 comparator only

Renderer selection is **PENDING**. `probes/ff02/` is a browser-side Three.js FBX importer/inspection bench; `probes/godot-ff02/` is an isolated Godot scene-import comparator. Neither is Fruit-Fly's desktop renderer, OS adapter or overlay. No model assets belong in Git.

From the repository root:

```bash
npm ci --prefix apps/avatar-renderer/probes/ff02
python3 -m http.server 8765 --bind 127.0.0.1 --directory apps/avatar-renderer/probes/ff02
```

Open `http://127.0.0.1:8765/` in a browser on the **same machine as your model files**. Pick an `.fbx` from `characters/local/<candidate>/source/` and any PNGs from its `textures/` folder. The file picker reads files locally: the server only serves the static test page and Three.js, **not** models. Do not change the server root to the repository root or to the Godot project. Even if the importer prints bone/morph names, usable animation/expression/rig/texture rendering must be verified visually and on the target platform. The probe does not implement VRM/glTF import yet; no VRM file was available to test.

For Godot CLI and side-by-side acceptance steps see [FF-02 test record](../../docs/development/FF-02-MODEL-INVENTORY.md). [ADR-0002](../../docs/decisions/ADR-0002-renderer.md) remains undecided. Keep any copied Godot assets under ignored `probes/godot-ff02/local/` and importer cache under ignored `probes/godot-ff02/.godot/`.
