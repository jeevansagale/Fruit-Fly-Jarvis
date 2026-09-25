"""Minimal brain-service smoke: state + structured intent + policy verdict."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages"))
from behavior.state import FlyState
from capability_policy.policy import CapabilityPolicy
from contracts.messages import build_intent


def main():
    state = FlyState()
    policy = CapabilityPolicy()
    intent = build_intent("app.launch", {"app": "firefox", "confirmed": True})
    allowed, reason = policy.validate(intent["intent"], intent["parameters"])
    print(json.dumps({
        "status": "ok",
        "activity": state.activity.value,
        "intent": intent,
        "intent_allowed": [allowed, reason],
    }))


if __name__ == "__main__":
    main()
