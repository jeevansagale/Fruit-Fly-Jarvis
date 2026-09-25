# Computer Control Security (implemented)

Pipeline: intent (brain/mock) → `CapabilityPolicy.validate` → typed
`ComputerController` adapter → result. There is no shell/python/file-delete
capability and no path from model text to subprocess.

- Allowlist + typed args: `packages/capability_policy/policy.py`
- Execution gate: `packages/capability_policy/controller.py` (denied intents
  never reach an adapter — tested)
- Hyprland adapter: query + workspace switch only; names validated (non-empty,
  ≤32 chars); switch is policy-gated, launch/close/URL actions need
  `confirmed: true`
- URL schemes restricted to http/https; volume clamped to 0–100
- Brain HTTP binds 127.0.0.1 only; no auth yet (local-only, documented gap)
- Logs carry subsystem/level only; no conversation or secret dumps

Kill switch: stop the brain service (`Ctrl+C` on `./Run.sh --dev` kills all
child processes via trap). Audit: poll `/commands` for the ordered record.
