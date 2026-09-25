from dataclasses import dataclass
from contracts.schema import Activity


@dataclass
class FlyState:
    activity: Activity=Activity.IDLE
    energy: float=1.0
