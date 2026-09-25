# FF-02 — Character Import / Model Inventory

Status: **SCAFFOLD READY — TARGET ASSET VALIDATION PENDING**

## Objective

Inventory the actual Furina, Columbina, and original Goth Mommy assets available locally before choosing Three.js or Godot as the 3D runtime.

The decision must be based on the assets actually used by Fruit-Fly, not on generic renderer feature lists.

## Put local assets here

```text
characters/local/
```

Do not commit proprietary character files unless redistribution rights are explicitly confirmed.

## Inventory command

```bash
python3 tools/model_inventory.py characters/local --output model-inventory.json
```

## Required evidence per candidate

| Capability | Evidence required |
|---|---|
| Model loads | Successful import with no fatal errors |
| Correct materials | Visual inspection |
| Textures | No missing-texture artifacts |
| Skeleton / humanoid rig | Importer/runtime inspection |
| Idle animation | Animation plays correctly |
| Additional animations | At least one non-idle animation tested if available |
| Facial expressions | Morph targets / expression system verified |
| Eye/look-at | Runtime test |
| Hair/clothing physics | Runtime test if the asset provides them |
| Animation switching | Two clips switched without pose corruption |
| Scale/orientation | Correct world-space placement |
| Performance | Idle FPS + frame-time observation |
| Packaging | Repeatable local build/run |

## Do not infer

The inventory script deliberately marks runtime properties as `unknown`. File extension alone does not prove animation, skeleton, morph-target, texture, or VRM expression support.

## Renderer gate

FF-03 (renderer decision) stays **PENDING** until at least one real candidate character has been imported and the evidence above has been recorded.
