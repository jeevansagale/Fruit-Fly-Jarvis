# FF-01 Test Report

Status: **PARTIAL — target-machine launch observed 2026-09-25; visuals
partially recorded, interaction items still PENDING**. GTK 4.22.5, Rust
1.92.x-era toolchain (1.98.1 reported), Arch + Wayland (`wayland-1`) +
Hyprland + NVIDIA. Overlay built after the `let mut signals` fix and
launched in foreground.

Code audit: the SIGINT listener in `apps/overlay-linux/src/main.rs` calls
`std::process::exit(0)`. Exiting the process is not the same as graceful GTK/renderer cleanup. Verify `Ctrl+C` from the launching terminal on the actual machine; if the requirement is graceful shutdown, revise this handler in a separate FF-01 change after reproducing the issue.

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
| Launch without crash | PASS — tested | Foreground launch rendered a frame (screenshot) |
| Debug marker position | PASS — tested | Red disc with two eyes at ~82%/72% viewport, matches `main.rs` draw func |
| Transparent surface | FAIL — tested | Surface background is opaque black, not transparent |
| Overlay layer | PENDING | |
| Not tiled | PENDING | |
| Keyboard focus unaffected | PENDING | |
| Background pointer passthrough possible | PENDING | |
| Avatar hit region possible | PENDING | |
| Workspace switching | PENDING | |
| Multi-monitor | PENDING | single screenshot only |
| No application interference | PENDING | |
| 60 FPS idle target | PENDING | |
| Hide/show cleanly | PENDING | |
| Ctrl+C exits cleanly | PENDING | process-disappearance check not yet recorded |

## Exit behavior

`Ctrl+C` means **SIGINT from the terminal**. `Super+C` is a desktop/compositor shortcut and is not equivalent to Ctrl+C in a terminal, so it is not an expected exit command for this process.

## Evidence

Paste the exact terminal output from:

```bash
cargo run --release
```

Then note any visual/compositor behavior that differs from the checklist.
