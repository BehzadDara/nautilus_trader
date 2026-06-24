from enum import Enum
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import TimeInForce

class KalshiOrderSide(Enum):
    YES = 'yes'
    NO = 'no'

class KalshiOrderAction(Enum):
    BUY = 'buy'
    SELL = 'sell'

class KalshiOrderStatus(Enum):
    RESTING = 'resting'
    CANCELED = 'canceled'
    EXECUTED = 'executed'
    PENDING = 'pending'

def kalshi_action_from_order_side(order_side: OrderSide) -> KalshiOrderAction:
    if order_side == OrderSide.BUY:
        return KalshiOrderAction.BUY
    if order_side == OrderSide.SELL:
        return KalshiOrderAction.SELL
    raise ValueError(f'invalid order side: {order_side}')

def order_side_from_kalshi_action(action: str) -> OrderSide:
    if action == KalshiOrderAction.BUY.value:
        return OrderSide.BUY
    if action == KalshiOrderAction.SELL.value:
        return OrderSide.SELL
    raise ValueError(f'invalid kalshi action: {action}')

def kalshi_order_type(order_type: OrderType) -> str:
    if order_type == OrderType.LIMIT:
        return 'limit'
    if order_type == OrderType.MARKET:
        return 'market'
    raise ValueError(f'unsupported order type: {order_type}')

def kalshi_time_in_force(time_in_force: TimeInForce) -> str | None:
    if time_in_force == TimeInForce.GTC:
        return None
    if time_in_force == TimeInForce.IOC:
        return 'immediate_or_cancel'
    if time_in_force == TimeInForce.FOK:
        return 'fill_or_kill'
    raise ValueError(f'unsupported time in force: {time_in_force}')

def order_status_from_kalshi(status: str) -> OrderStatus:
    if status == KalshiOrderStatus.RESTING.value:
        return OrderStatus.ACCEPTED
    if status == KalshiOrderStatus.CANCELED.value:
        return OrderStatus.CANCELED
    if status == KalshiOrderStatus.EXECUTED.value:
        return OrderStatus.FILLED
    if status == KalshiOrderStatus.PENDING.value:
        return OrderStatus.SUBMITTED
    return OrderStatus.ACCEPTED
