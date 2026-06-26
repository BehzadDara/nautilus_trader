from __future__ import annotations
from decimal import Decimal
from nautilus_trader.adapters.kalshi.common.parsing import KALSHI_FEE_RATE
from nautilus_trader.adapters.kalshi.common.parsing import calculate_kalshi_commission
from nautilus_trader.backtest.config import FeeModelConfig
from nautilus_trader.backtest.models import FeeModel
from nautilus_trader.model.enums import LiquiditySide
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders import Order

class KalshiFeeModelConfig(FeeModelConfig, frozen=True):
    fee_rate: str = str(KALSHI_FEE_RATE)

class KalshiFeeModel(FeeModel):

    def __init__(self, config: KalshiFeeModelConfig | None=None) -> None:
        super().__init__()
        self._fee_rate = Decimal(config.fee_rate) if config is not None else KALSHI_FEE_RATE

    def get_commission(self, order: Order, fill_qty: Quantity, fill_px: Price, instrument: Instrument) -> Money:
        if order.liquidity_side == LiquiditySide.MAKER:
            return Money(Decimal(0), instrument.quote_currency)
        commission = calculate_kalshi_commission(Decimal(str(fill_qty)), Decimal(str(fill_px)), self._fee_rate)
        return Money(commission, instrument.quote_currency)
