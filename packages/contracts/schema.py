from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class Activity(str, Enum):
    IDLE='idle'; LISTENING='listening'; THINKING='thinking'; SPEAKING='speaking'; EXECUTING='executing'; REACTING='reacting'; SLEEPING='sleeping'; ERROR='error'
class Emotion(str, Enum):
    NEUTRAL='neutral'; AMUSED='amused'; ANNOYED='annoyed'; CONCERNED='concerned'; AFFECTIONATE='affectionate'; CURIOUS='curious'; SURPRISED='surprised'
@dataclass
class CharacterState:
    activity: Activity=Activity.IDLE
    emotion: Emotion=Emotion.NEUTRAL
    look_x: float=0.0; look_y: float=0.0; audio_level: float=0.0
    expression: str='neutral'; motion: str='idle'; attention_target: str='none'
@dataclass
class Intent:
    action: str
    arguments: dict[str, Any]=field(default_factory=dict)
    source: str='unknown'; confidence: float=1.0; requires_confirmation: bool=False
