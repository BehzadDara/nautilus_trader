from enum import Enum

class KalshiOrderSide(Enum):
    YES = 'yes'
    NO = 'no'

class KalshiOrderStatus(Enum):
    RESTING = 'resting'
    CANCELED = 'canceled'
    EXECUTED = 'executed'
