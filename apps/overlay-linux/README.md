# FF-01 Linux Overlay Spike

Target: Arch Linux + Hyprland + Wayland.

## Build

```bash
sudo pacman -S --needed rust gtk4 gtk4-layer-shell
cargo run --release
```

## Exit controls

- **Ctrl+C** in the terminal: sends SIGINT and exits the process.
- **Super+C is not a terminal interrupt** and is not expected to stop the process.
- If the overlay has no keyboard focus, desktop hotkeys should not be hijacked by the prototype.
- Closing the terminal is a fallback during the spike, but should not be needed.

## Acceptance test

- [ ] transparent surface
- [ ] overlay layer
- [ ] not tiled
- [ ] keyboard focus unaffected
- [ ] background pointer passthrough possible
- [ ] avatar hit region possible
- [ ] workspace switching works
- [ ] multi-monitor placement works
- [ ] no application interference
- [ ] 60 FPS idle target
- [ ] hide/show cleanly
- [ ] Ctrl+C exits cleanly
