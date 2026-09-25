# FF-01 Test Report

Status: **TARGET-MACHINE VALIDATION IN PROGRESS**

Run this on the actual Arch + Hyprland session. Record versions and mark every acceptance item PASS/FAIL.

## Environment

```text
Hyprland:
GTK4:
gtk4-layer-shell:
Kernel:
GPU:
Wayland compositor:
Monitor(s):

Renderer/backend observed:
```

## Functional tests

| Test | Result | Notes |
|---|---|---|
| Transparent surface | PENDING | |
| Overlay layer | PENDING | |
| Not tiled | PENDING | |
| Keyboard focus unaffected | PENDING | |
| Background pointer passthrough possible | PENDING | |
| Avatar hit region possible | PENDING | |
| Workspace switching | PENDING | |
| Multi-monitor | PENDING | |
| No application interference | PENDING | |
| 60 FPS idle target | PENDING | |
| Hide/show cleanly | PENDING | |
| Ctrl+C exits cleanly | PENDING | |

## Exit behavior

`Ctrl+C` means **SIGINT from the terminal**. `Super+C` is a desktop/compositor shortcut and is not equivalent to Ctrl+C in a terminal, so it is not an expected exit command for this process.

## Evidence

Paste the exact terminal output from:

```bash
cargo run --release
```

Then note any visual/compositor behavior that differs from the checklist.
