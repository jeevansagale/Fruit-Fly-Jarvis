# Character Package Format

A character is a data package, not hard-coded application logic.

```yaml
id: original-goth-mommy
display_name: "Goth Mommy"
model:
  format: vrm
  path: local/model.vrm
personality:
  confidence: 0.9
  teasing: 0.8
  patience: 0.35
  affection: 0.55
  protectiveness: 0.85
speech:
  verbosity: low
  directness: high
  humor: dry
behavior:
  proactive_level: low
  interruption_policy: conservative
```

The engine must tolerate missing optional animation/expression capabilities and use fallbacks.
