# ADR-0003 — Character Asset Boundary

Status: **PROPOSED**

Character assets are treated as local, replaceable runtime inputs rather than source-controlled application code.

**2026-09-25 audit:** Two candidate ZIPs were already tracked at the repository root in the baseline commit, with no redistribution rights established by their archive contents. They have been removed from the index without deleting local originals, and new root ZIPs are ignored. **Old Git history still contains both archives; merely ignoring/untracking them does not make the repository safe to publish.** Resolve licensing and remove the affected history (or prepare a clean public history) *before* publishing/pushing this repository. Do not rewrite published history without coordinating with the owner. Local copies/staged extracts stay under ignored `characters/local/`.

## Rules

1. Store local/proprietary models under `characters/local/`.
2. Do not commit copyrighted or restricted assets without explicit redistribution rights.
3. Inventory assets before selecting the 3D renderer.
4. Keep character identity separate from runtime behavior and OS capabilities.
5. A character package may declare model format, personality, speech, and behavior policy, but the runtime owns execution.
6. Renderer-specific conversion is allowed only as a documented build/import step; preserve the original source asset locally.

## Rationale

Fruit-Fly is intended to support multiple character candidates without rewriting the assistant runtime. The model format and animation/expression capabilities are therefore an integration boundary, not an implementation detail of the personality or capability layers.
