"""Minimal brain-service smoke test; intentionally no LLM dependency."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages"))
from behavior.state import FlyState
from capability_policy.policy import CapabilityPolicy

def main():
    state = FlyState()
    policy = CapabilityPolicy()
    print(json.dumps({
        "status": "ok",
        "activity": state.activity.value,
        "policy_workspace_next": policy.validate("workspace.next", {}).allowed,
        "policy_shell": policy.validate("shell.exec", {}).allowed,
    }))

if __name__ == "__main__":
    main()
