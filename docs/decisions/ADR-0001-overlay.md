# ADR-0001 — Native Wayland Overlay

Status: **SPIKE IMPLEMENTED; TARGET VALIDATION PENDING**

Fruit-Fly prototypes the Linux compositor boundary with GTK4 + gtk4-layer-shell. The 3D renderer remains replaceable until FF-01 and character import testing provide evidence.

The spike has an explicit SIGINT shutdown path so `Ctrl+C` from the launching terminal terminates it deterministically.
