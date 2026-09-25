# Runtime-stack research notes (2026-09-25, with sources in subagent report)

## Godot transparency on Wayland/NVIDIA — APPLIED
FACT: flag triple `transparent` + `per_pixel_transparency/allowed` +
`transparent_background`, gl_compatibility for NVIDIA (Vulkan transparency
broken on NVIDIA drivers). Applied to `apps/avatar-renderer/runtime/`.
Open question (manual): default vs `--display-server wayland` driver +
resize-flicker check; mouse-passthrough polygon still missing for true
overlay companion.

## VRM in Godot — NEXT EXPERIMENT (scratch project, not runtime)
FACT: godot-vrm (GitHub master, not stale store copy) or AzPepoze fork gives
humanoid retarget, spring bones, expression tracks; VRMA clip exchange still
stub. Try: import free VRoid sample, verify spring sway, one expression,
one retargeted clip — then decide on VRM as avatar format.

## Local voice — NEXT EXPERIMENT (timing only, no service code yet)
FACT: Piper TTS via AUR (+voice packs, daemonize to hide load cost, strip
newlines) and faster-whisper tiny/base-int8 (Wyoming server shape fits our
daemon pattern). Try: cold/warm Piper synth + tiny/base transcription of a
30 s sample; pick STT tier on wall-clock/RAM.

## FBX clips — CONFIRMATION EXPERIMENT
FACT: Three.js and Godot read the same AnimStacks; 0 clips in both means a
take-less static mesh, not an importer gap. Confirm once via take-list
inspection (ufbx/fbx2gltf info or Blender), then retire the question.
