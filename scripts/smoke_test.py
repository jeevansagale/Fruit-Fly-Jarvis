import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'packages'))
from behavior.state import FlyState
from capability_policy.policy import CapabilityPolicy
assert FlyState().activity.value=='idle', "FlyState must start idle"
assert CapabilityPolicy().validate('workspace.next',{})[0], "workspace.next must be allowed"
assert not CapabilityPolicy().validate('shell.exec',{})[0], "shell.exec must be denied"
print('Fruit-Fly smoke test: PASS')
