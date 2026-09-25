from dataclasses import dataclass
from enum import Enum
class Activity(str,Enum): IDLE='idle'; LISTENING='listening'; THINKING='thinking'; SPEAKING='speaking'; EXECUTING='executing'; REACTING='reacting'; SLEEPING='sleeping'; ERROR='error'
@dataclass
class FlyState:
    activity: Activity=Activity.IDLE
    energy: float=1.0
