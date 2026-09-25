# System Design

```text
Perception → Event/State Bus → Behavior / AI → Capability Policy → OS Adapter → Character Runtime → Wayland Overlay
```

The LLM is a planner/conversation component, never an unrestricted shell process. Character identity, personality, runtime state and renderer are separate concerns.

Initial target is Arch + Hyprland. The compositor boundary is native layer-shell; the renderer remains replaceable until FF-01 and character import testing provide evidence.

## Implementation audit (2026-09-25; conceptual slots are not implementations)

- `apps/overlay-linux/`: a Rust/GTK4 layer-shell **debug marker**, not an avatar renderer. FF-01 compositor acceptance and clean SIGINT teardown still need the owner's real Wayland machine.
- `apps/avatar-renderer/`: only the isolated FF-02 importer comparisons; **no chosen production renderer or native overlay handoff**.
- `packages/contracts/`: small dataclass/enum sketches. `packages/behavior/` duplicates `Activity`; there is no implemented state machine or personality engine. `packages/character_runtime/` does not yet exist.
- `packages/capability_policy/`: string allowlist stub only; **no typed argument checks, authoritative confirmation enforcement or OS adapters**. Passing an empty allowlist currently falls back to the default list. Computer control must remain disabled; do not connect an LLM to this stub.
- `services/brain/main.py` uses `.allowed` on `policy.validate(...)`, but `validate` returns a tuple; the brain smoke command currently **fails**. `scripts/smoke_test.py` tests only basic allowlist outcomes. The vision/voice/memory service slots in the plan have **no code in this checkout**.
- `tools/model_inventory.py` records metadata only; FF-02 real-import results and the asset licensing/history issue are documented in [FF-02](../development/FF-02-MODEL-INVENTORY.md). The primary original character asset is still absent.

These findings are deferred work, **not** a reason to build an AI or computer-control pipeline before avatar validation. `LLM ≠ OS access` remains an invariant; any future execution needs typed arguments, source-independent policy, confirmation and tests before an adapter can run.
