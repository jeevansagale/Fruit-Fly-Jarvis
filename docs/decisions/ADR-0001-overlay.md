# ADR-0001 — Native Wayland Overlay

Status: **SPIKE IMPLEMENTED; TARGET VALIDATION PENDING**

Fruit-Fly prototypes the Linux compositor boundary with GTK4 + gtk4-layer-shell. The 3D renderer remains replaceable until FF-01 and character import testing provide evidence.

The spike installs a SIGINT handler, but it currently calls `std::process::exit(0)` from a signal-listener thread. That is **not a verified graceful GTK teardown**; successful `Ctrl+C` exit, pointer passthrough and all compositor criteria are still **PENDING** on Arch + Hyprland. `Super+C` is a desktop shortcut, not terminal SIGINT.
