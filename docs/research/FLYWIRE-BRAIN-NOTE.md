# Public fruit-fly brain (FlyWire) — what it is and is not for Fruit-Fly

## FACT
- The FlyWire consortium published the first whole-adult-brain wiring diagram
  of *Drosophila melanogaster* (female) in Nature, 2024-10-02 (Dorkenwald et
  al., doi:10.1038/s41586-024-07558-y; companion cell-type atlas Schlegel et
  al., doi:10.1038/s41586-024-07686-5).
- Scale: 139,255 neurons, ~54.5M chemical synapses (~15.1M weighted edges),
  8,453 annotated cell types, 78-neuropil projectome.
- Open data: Codex portal (codex.flywire.ai), Zenodo connectivity tables
  (full synapse table ~9.5 GB), annotation TSVs on GitHub
  (flyconnectome/flywire_annotations).
- It is a structural map (who connects to whom, with neurotransmitter
  predictions). It is not a runnable mind: no dynamics, no learning rule, no
  sensory grounding, no goals.

## INFERENCE
- We cannot and should not run a 140k-neuron simulation as Fruit-Fly's
  assistant brain: even reduced LIF sims (cf. snedea/flybrain in-browser
  demo) produce emergent spikes, not instruction-following, tool use, or
  dialogue. The desktop companion needs deliberative reasoning; the
  connectome offers none directly.
- What transfers is architectural inspiration, already aligned with our
  design: mushroom-body-like associative memory (sparse associative store,
  not vectors-first), central-complex-like state integration (our behavior
  engine's IDLE/LISTENING/... states), and strict sensory→decision→motor
  separation (our perception→brain→capability→renderer pipeline).
- Data scale forbids vendoring: do not download the 9.5 GB table or any EM
  data into this repo.

## DECISION
- No connectome data or code enters the runtime. What entered instead (2026):
  `packages/neuro/motif.py` — a tiny LIF pool with lateral-inhibition
  winner-take-all over calm/alert/social drives, stepped per behavior event
  and reported in every `/event` response. It is a functional motif inspired
  by competitive insect circuitry, explicitly not a simulation of fly neurons.
- If a future milestone wants bio-plausible dynamics (e.g., a curiosity demo
  driving idle behavior from a tiny extracted circuit motif), that is a
  separate spike requiring its own plan — not part of the assistant brain.
- The name "Fruit-Fly" remains an identity nod, not a technical claim.
