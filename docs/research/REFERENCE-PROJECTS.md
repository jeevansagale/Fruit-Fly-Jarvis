# Reference projects — FACT / INFERENCE / DECISION

## TuragaLab/flybody
- FACT: detailed fly body + MuJoCo locomotion/RL envs; separates simulation,
  body, controller. Apache-2.0 code.
- INFERENCE: separation of body model from controller maps to our
  character-runtime/renderer split.
- DECISION: inspiration only; no dependency (wrong species, wrong stack).

## cobanov/awesome-fly
- FACT: curated CC0 index of connectome projects, not a library.
- DECISION: provenance checklist idea only.

## DenisSergeevitch/desktop-fly
- FACT: macOS Swift desktop pet (procedural body) + Electron/Three port; MIT
  code, CC-licensed data (do not vendor).
- INFERENCE: small state-driven desktop presence works without heavy engines.
- DECISION: supports our mock-first/dev-mode approach; no code reuse.

## snedea/flybrain
- FACT: browser LIF connectome sim in a worker, decoupled sim/rendering; MIT.
- INFERENCE: decoupling simulation tick from render loop is the right shape
  for brain→avatar IPC.
- DECISION: adopted as localhost-HTTP command poll pattern.

## Cross-cutting
- FACT: none is a Wayland layer-shell humanoid importer or local-first
  assistant runtime.
- DECISION: Godot native runtime (proven Furina import on target) over new
  browser-embedding work; Three.js kept as probe.
