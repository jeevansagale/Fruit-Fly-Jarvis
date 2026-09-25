# ADR-0003 — Character Asset Boundary

Status: **PROPOSED**

Character assets are treated as local, replaceable runtime inputs rather than source-controlled application code.

## Rules

1. Store local/proprietary models under `characters/local/`.
2. Do not commit copyrighted or restricted assets without explicit redistribution rights.
3. Inventory assets before selecting the 3D renderer.
4. Keep character identity separate from runtime behavior and OS capabilities.
5. A character package may declare model format, personality, speech, and behavior policy, but the runtime owns execution.
6. Renderer-specific conversion is allowed only as a documented build/import step; preserve the original source asset locally.

## Rationale

Fruit-Fly is intended to support multiple character candidates without rewriting the assistant runtime. The model format and animation/expression capabilities are therefore an integration boundary, not an implementation detail of the personality or capability layers.
