# Fruit-Fly Master Implementation Plan (living)

Goal: runnable local vertical slice — overlay + 3D avatar + character/behavior
runtime + structured events + policy-gated capabilities + mocks for
brain/voice/vision. No cloud, no unrestricted OS control.

## Renderer decision (evidence, not preference)

- Three.js (target Firefox): Furina visibly rendered, textures usable, 0 clips.
  Verdict: proven loader, but runtime needs a browser embedded in a
  layer-shell surface — an unsolved bridge (ADR-0002 blocker for both).
- Godot 4.7.2 (target, headless): FurinaV2.fbx imported with 1 mesh,
  5 materials, 240-bone Skeleton3D (Head/Neck/Eye_L/Eye_R present), 60 blend
  shapes, 0 clips, zero import errors.
- Decision: **Godot native avatar runtime**. Native window + documented
  transparency + single process + GDScript HTTP polling beats inventing a
  browser-to-layer-shell bridge. Three.js stays as comparison probe.
- IPC: **localhost HTTP** (Python stdlib server; Godot HTTPRequest poll).
  No new deps, debuggable with curl, trivially mockable.

## Phases

### 0. Recovery/audit — DONE
Tree audited; FF-01/FF-02C evidence intact; `character_runtime/` empty;
`project.godot` Godot-reformat churn noted for revert.

### 1. Core contracts + policy + behavior + brain intent
- Objective: typed message contracts, deterministic behavior SM, hardened
  allowlist policy, brain producing structured intent (fix `.allowed` crash).
- Files: `packages/contracts/messages.py`, `packages/behavior/engine.py`,
  `packages/capability_policy/policy.py` (arg schemas), `services/brain/main.py`,
  `tests/test_slice_core.py`.
- Tests: contract validation, SM transitions, policy allow/deny/confirm,
  intent shape. Acceptance: 100% new tests pass, no `shell.*` capability.

### 2. Character configs + runtime
- Objective: renderer-independent character runtime: load YAML, states
  (BOOT/LOADING/IDLE/LISTENING/THINKING/SPEAKING/ERROR), expression/look-at
  state, procedural idle fallback (breath/sway/blink params as data).
- Files: `characters/_template/character.yaml` (extended),
  `characters/furina.yaml`, `characters/goth-mommy.yaml`,
  `characters/columbina.yaml`, `packages/character_runtime/runtime.py`,
  tests.
- Acceptance: swap character by path, no renderer import in runtime package.

### 3. Godot avatar runtime
- Objective: `apps/avatar-renderer/runtime/` Godot app: loads staged model,
  transparent window, procedural idle (bone sway + blink morph), polls brain
  HTTP for animation/expression/look_at commands, reports health.
- Files: `project.godot`, `runtime.gd`, README. Tests: GDScript parse check
  via `godot --headless --check-only`? (fallback: script-load smoke).
- Acceptance: headless run loads scene without errors; commands change state
  in log. Visuals remain manual PENDING.

### 4. Orchestration + slice demo
- Objective: `Run.sh --dev` starts brain HTTP + mock event feed; `--check`
  runs full offline verification; structured logging everywhere.
- Files: `Run.sh`, `services/brain/server.py`, `scripts/dev_events.py`.
- Acceptance: `./Run.sh --check` green; `--dev` runs without external APIs.

### 5. Hardening/docs
- Security review (§28), voice/vision/memory thin interfaces + mocks,
  Hyprland typed adapter (query/switch, confirm-gated), docs deliverables,
  5 review passes, final status.

## Scope limits
No cloud STT/TTS/LLM; no vector memory; no autonomous computer control beyond
allowlisted, confirm-gated capabilities; no visual PASS without observation;
no asset commits/uploads; no history rewrite.

## Cycle log
(Cycles appended below.)

## Cycle 0 — audit + plan (done)
Planned: repo audit, renderer decision, living plan. Implemented: this file +
Godot-native decision (Furina: 240 bones/60 morphs/5 materials, headless,
zero errors; Three.js stays probe; localhost HTTP IPC). Tests: n/a.
Decision: proceed to core contracts.

## Cycle 1 — core contracts/policy/behavior/brain (done)
Planned: messages, SM, hardened policy, brain intent. Implemented:
packages/contracts/messages.py, packages/behavior/engine.py, policy rewrite
(arg schemas, confirm gates, empty-set fix), brain structured intent (crash
fixed). Tests: 35/35 PASS (18 new in test_slice_core.py), brain + smoke run.
Decision: proceed to character runtime.

## Cycle 2 — character configs + runtime (done)
Planned: extended schema, 3 characters, renderer-independent runtime with
procedural fallback. Implemented: extended _template, furina/goth-mommy/
columbina YAMLs, packages/character_runtime/runtime.py (states, expression,
clamped look-at, idle_pose data, personality directives). Fixed schema
mismatch (flat YAML per existing convention, not wrapped). Tests: 43/43 PASS
(8 new). Decision: Godot runtime next, needs pyyaml documented.

## Cycle 3 — Godot avatar runtime (done)
Planned: native runtime loading staged model, procedural idle, HTTP command
poll. Implemented: apps/avatar-renderer/runtime/ (project.godot with
transparent window + gl_compatibility, main.tscn, runtime.gd). Verified
headless on target: skeleton=true, head_bone=4, blink_targets=1, import with
0 error lines, 60s run with no ERROR. Visuals remain manual PENDING.
Decision: wire brain HTTP server + --dev demo next.

## Cycle 4 — orchestration + slice demo (done)
Planned: brain HTTP, mock events, Run.sh --dev/--check. Implemented:
services/brain/server.py (/health, /commands, /event, /intent),
packages/observability/log.py, scripts/dev_events.py, Run.sh --dev/--check.
Found+fixed: behavior RESPONDING missing from AVATAR_STATES (contract
rejected own state); test socket close warning. Verified: --dev full loop
brain→avatar commands applied in avatar log; 47/47 PASS.
Decision: thin peripheral interfaces + hardening/docs, then review passes.

## Cycle 5 — peripherals, hardening, docs, reviews (done)
Planned: voice/vision/memory mocks, Hyprland adapter, docs, 5 passes.
Implemented: packages/perception/providers.py, capability controller.py,
COMPUTER_CONTROL/STATUS/RENDERER-VALIDATION/README/research docs, ADR-0002
decision (Godot native, evidence-linked). Reviews: P1 layering clean, P2
runtime verified headless, P3 no dangerous patterns + localhost-only, P4
minimal HUD-by-design (no dashboard UI built), P5 fixed runtime gitignore
gap. Tests: 53/53 PASS, diff-check clean, no assets tracked.
Decision: slice complete pending human visuals; STOP per stop condition.

## Company cycle — 4-role review + implementation (done)
Planned: security/QA/design/research in parallel, implement findings.
Security: fixed loopback-bind enforcement, `since` 400, JSON 400, RLock
atomicity, log truncation, arg charset/length, controller honest verdicts,
GDScript URL/model guards + body cap. QA: fixed brain intent, Activity
dedup, look_at emission, gesture shape, Run.sh robustness + model glob,
dev sequence (both tool_finished required), smoke messages, server tests.
Design: theme: blocks in 4 YAMLs, probe goth tokens, window rename +
portrait/borderless/always-on-top, deferred overlay-disc rework.
Research: transparency triple applied (per-pixel + transparent_background),
voice stack (Piper daemon + faster-whisper tiny/base), VRM scratch-project
plan, take-less FBX confirmation experiment. Tests: 57/57 PASS.
Decision: slice hardened; visuals still human-gated.

## Company+research cycle — FlyWire public brain note (done)
User asked about the public fruit-fly brain. Verified: FlyWire whole adult
female brain, Nature 2024-10-02, 139,255 neurons / ~54.5M synapses, open via
Codex + Zenodo. Recorded docs/research/FLYWIRE-BRAIN-NOTE.md with
FACT/INFERENCE/DECISION: a wiring map is not a runnable assistant brain;
no data or code enters the runtime; bio-inspired memory/state ideas already
match our architecture. Tests: 57/57 PASS.

## Jarvis-motif cycle — live drive signal (done)
User asked to use the public fly brain toward Jarvis. Honest boundary kept:
connectome is a map, not a mind. Implemented packages/neuro/motif.py (LIF +
lateral-inhibition WTA over calm/alert/social, stepped per behavior event,
drive reported in /event + logs) with 6 tests; fixed my own test arithmetic
mid-cycle. Verified: 63/63 PASS, --dev shows social winning while the user
speaks and calm during speech. Jarvis still needs reasoning/voice/vision —
the drive is attention bias, not intelligence.

## Hand-gesture cycle (done, live path user-gated)
User asked for hand control of tabs/windows/scroll. Implemented
packages/vision/hands.py (MediaPipe HandLandmarker Tasks API, 640x480,
static poses + swipe tracker with cooldowns, contract-shaped events,
gesture→intent map) + Media/Scroll adapters (playerctl, ydotool) +
scroll.page capability + scripts/vision_check.py. Installed mediapipe 1.0.1
+ opencv via pip --user (PEP 668 workaround documented). Fixed along the
way: legacy solutions API gone in 1.0, BaseOptions import path, my own
dropped constants + test math. Tests: 74/74 PASS (11 new). Blocker: native
TFLite init SIGKILLed inside the agent sandbox (thread caps + GPU-disable
tried); classifier/policy/adapter layers fully tested, live camera needs
one user run of vision_check.py in a real terminal.

## Vision native-runtime blocker (diagnosed, worked around)
User ran --vision in their own terminal: same SIGKILL. Ruled out: OOM
(no record, 17GB free), ulimits (unlimited), cgroup caps (max), corrupt
model (zip intact, 7.8MB), RWX-mmap EDR kill (test passes), thread counts,
GPU-disable flag. No strace available; TFLite dies silently inside
create_from_options on this machine. Implemented: vision_check pre-flights
native init in a subprocess and reports clean BLOCKED exit 2 instead of a
bare 'Killed'. Classifier/policy/adapters stay 74/74 green. Next experiment:
ONNX Runtime port of the landmark pipeline, or ai-edge-litert.

## ONNX port (done, live run user-gated)
MediaPipe native SIGKILL undiagnosable (no strace, no logs). Ported to
PINTO0309 hand_landmark_sparse ONNX (single-shot 21 landmarks, RGB/224//255
convention verified from upstream demo) via onnxruntime CPU (2 threads).
HandTracker auto-selects onnx, mediapipe kept as fallback. Verified: init
clean, 20 frames stable (~0.4s/frame, no false positives on empty room).
Tests stay green; camera-with-hand run needs the user in frame.

## Gesture control loop (done, user-gated live run)
User showed detection works (palm/fist/swipe_right classified) but nothing
moved: vision_check only printed mappings, never executed. Added --control
mode executing mapped intents through ComputerController (policy first),
2.5s per-gesture cooldowns, Ctrl+C stops; Run.sh --vision passes args.
Verified hyprctl JSON path live; did not switch the user's workspace from
here. Tests: 75/75 PASS.

## Detection tuning + learning cycle (done)
Camera healthy per v4l2 (defaults, auto-exposure). Arch Wiki guidance
folded into user instructions (lighting, v4l2-ctl exposure/brightness,
v4l2ucp). Added --debug score/brightness telemetry, swipe dx/cooldown
parameters, and online calibration: opposite-gesture undos tighten swipe
travel (persisted in ignored configs/local/), steady use relaxes it.
Tests: 77/77 PASS.

## Gesture-syntax + Furina persona cycle (done)
User hit Hyprland 0.56 rejecting bare `next`/`prev` words (Lua-flavored
dispatcher error): relative switches now use stable `+1`/`-1` via dedicated
move_workspace() bypassing the name regex; tested argv asserted. Persona:
furina.yaml enriched (retired-archon showboat, voice lines, guardrails);
brain loads FRUIT_FLY_CHARACTER (default furina) and serves persona card in
/health + every /event. Fixed my own YAML quoting breakage mid-cycle.
Tests: 78/78 PASS. Live swipe-switch still needs one user run.

## hyprland-lua + tracking cycle (done)
Research solved the hl.dispatch mystery: Hyprland >=0.55 Lua-config mode
parses legacy `dispatch workspace X` as Lua and rejects it (upstream
discussion #14255; end4 keybinds use hl.dsp.focus). Verified working
channel via exec_cmd("true"). Implemented auto-fallback (legacy first,
Lua focus() on hl.dispatch marker, cached) with tests. Tracking upgrade
for swipe reliability: ROI crop tracking around last bbox (full-frame
re-detect after 3 misses), EMA landmark smoothing, swipe window 0.6->1.5s
for ~2.4fps cameras. Tests: 81/81 PASS. ROI crop path unit-tested only
(no hand in frame here); user live run decides.
