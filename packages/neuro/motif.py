"""Tiny spiking motif inspired by insect competitive circuits.

A leaky integrate-and-fire (LIF) pool with lateral inhibition implements
winner-take-all drive selection: competing salience inputs (calm / alert /
social) compete, one wins, the winner biases avatar attention. This is a
functional motif, not a simulation of any specific fly neuron — the FlyWire
connectome is a wiring map, not runnable code (see
docs/research/FLYWIRE-BRAIN-NOTE.md).
"""
from __future__ import annotations


class LIFNeuron:
    def __init__(self, threshold: float = 1.0, decay: float = 0.9, reset: float = 0.0):
        if not 0.0 < decay < 1.0:
            raise ValueError("decay must be within (0, 1)")
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        self.threshold = threshold
        self.decay = decay
        self.reset = reset
        self.voltage = 0.0

    def step(self, current: float, dt: float = 1.0) -> bool:
        self.voltage = self.voltage * self.decay + current * dt
        if self.voltage >= self.threshold:
            self.voltage = self.reset
            return True
        return False


class DriveNetwork:
    """N LIF drives with all-to-all lateral inhibition. step() returns the
    winning drive name, or None if nothing crossed threshold."""

    def __init__(self, drives: tuple[str, ...] = ("calm", "alert", "social"),
                 inhibition: float = 0.4):
        if len(drives) < 2:
            raise ValueError("need at least two drives to compete")
        self.drives = list(drives)
        self.neurons = [LIFNeuron() for _ in drives]
        self.inhibition = inhibition

    def step(self, salience: dict[str, float]) -> str | None:
        spikes = []
        for name, neuron in zip(self.drives, self.neurons):
            fired = neuron.step(float(salience.get(name, 0.0)))
            spikes.append(fired)
        if any(spikes):
            for name, neuron, fired in zip(self.drives, self.neurons, spikes):
                if not fired:
                    neuron.voltage = max(0.0, neuron.voltage - self.inhibition)
        winners = [n for n, s in zip(self.drives, spikes) if s]
        if len(winners) == 1:
            return winners[0]
        return None

    def reset(self) -> None:
        for neuron in self.neurons:
            neuron.voltage = 0.0


EVENT_SALIENCE = {
    "user_started_speaking": {"calm": 0.1, "alert": 0.4, "social": 0.9},
    "user_stopped_speaking": {"calm": 0.4, "alert": 0.5, "social": 0.3},
    "brain_thinking": {"calm": 0.5, "alert": 0.4, "social": 0.1},
    "brain_response": {"calm": 0.3, "alert": 0.3, "social": 0.7},
    "tool_started": {"calm": 0.2, "alert": 0.6, "social": 0.2},
    "tool_finished": {"calm": 0.8, "alert": 0.2, "social": 0.2},
    "system_error": {"calm": 0.0, "alert": 1.0, "social": 0.0},
}


def salience_for(event: str) -> dict[str, float]:
    return dict(EVENT_SALIENCE.get(event, {"calm": 0.5, "alert": 0.2, "social": 0.2}))
