# System Design

```text
Perception → Event/State Bus → Behavior / AI → Capability Policy → OS Adapter → Character Runtime → Wayland Overlay
```

The LLM is a planner/conversation component, never an unrestricted shell process. Character identity, personality, runtime state and renderer are separate concerns.

Initial target is Arch + Hyprland. The compositor boundary is native layer-shell; the renderer remains replaceable until FF-01 and character import testing provide evidence.
