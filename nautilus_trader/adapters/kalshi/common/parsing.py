from __future__ import annotations
import time
from decimal import Decimal
from typing import Any
import pandas as pd
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_instrument_id
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AssetClass
from nautilus_trader.model.identifiers import Symbol
from nautilus_trader.model.instruments import BinaryOption
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity

def _price_increment(market: dict[str, Any]) -> Price:
    price_ranges = market.get('price_ranges') or []
    if price_ranges and price_ranges[0].get('step'):
        return Price.from_str(str(price_ranges[0]['step']))
    return Price.from_str('0.01')

def parse_kalshi_instrument(market: dict[str, Any], ts_init: int | None=None) -> BinaryOption:
    ticker = str(market['ticker'])
    instrument_id = get_kalshi_instrument_id(ticker)
    raw_symbol = Symbol(ticker)
    description = market.get('title') or ticker
    outcome = market.get('yes_sub_title') or 'Yes'
    price_increment = _price_increment(market)
    size_increment = Quantity.from_str('1')
    open_time = market.get('open_time')
    activation_ns = pd.Timestamp(open_time).value if open_time else 0
    expiration_time = market.get('expiration_time') or market.get('close_time')
    if expiration_time:
        expiration_ns = pd.Timestamp(expiration_time).value
    else:
        expiration_ns = (pd.Timestamp.now(tz='UTC') + pd.DateOffset(years=10)).value
    ts_init = ts_init if ts_init is not None else time.time_ns()
    return BinaryOption(instrument_id=instrument_id, raw_symbol=raw_symbol, outcome=outcome, description=description, asset_class=AssetClass.ALTERNATIVE, currency=USD, price_increment=price_increment, price_precision=price_increment.precision, size_increment=size_increment, size_precision=size_increment.precision, activation_ns=activation_ns, expiration_ns=expiration_ns, max_quantity=None, min_quantity=None, maker_fee=Decimal(0), taker_fee=Decimal(0), ts_event=ts_init, ts_init=ts_init, info=market)
