import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'packages'))
from behavior.state import FlyState
from capability_policy.policy import CapabilityPolicy
assert FlyState().activity.value=='idle'
assert CapabilityPolicy().validate('workspace.next',{})[0]
assert not CapabilityPolicy().validate('shell.exec',{})[0]
print('Fruit-Fly smoke test: PASS')
