from __future__ import annotations
import hashlib
import time
from decimal import ROUND_CEILING
from decimal import Decimal
from typing import Any
import pandas as pd
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_instrument_id
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BookOrder
from nautilus_trader.model.data import OrderBookDelta
from nautilus_trader.model.data import OrderBookDeltas
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.enums import AssetClass
from nautilus_trader.model.enums import BookAction
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import RecordFlag
from nautilus_trader.model.identifiers import Symbol
from nautilus_trader.model.identifiers import TradeId
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

def _yes_bid_order(instrument: BinaryOption, price: str, size: str) -> BookOrder:
    return BookOrder(side=OrderSide.BUY, price=instrument.make_price(float(price)), size=instrument.make_qty(float(size)), order_id=0)

def _no_bid_as_yes_ask_order(instrument: BinaryOption, price: str, size: str) -> BookOrder:
    yes_ask_price = 1.0 - float(price)
    return BookOrder(side=OrderSide.SELL, price=instrument.make_price(yes_ask_price), size=instrument.make_qty(float(size)), order_id=0)

def parse_kalshi_book_snapshot(instrument: BinaryOption, msg: dict[str, Any], sequence: int, ts_event: int, ts_init: int) -> OrderBookDeltas:
    deltas: list[OrderBookDelta] = [OrderBookDelta(instrument_id=instrument.id, action=BookAction.CLEAR, order=BookOrder(side=OrderSide.NO_ORDER_SIDE, price=instrument.make_price(0.0), size=instrument.make_qty(0.0), order_id=0), flags=0, sequence=sequence, ts_event=ts_event, ts_init=ts_init)]
    for price, size in msg.get('yes_dollars_fp') or []:
        deltas.append(OrderBookDelta(instrument_id=instrument.id, action=BookAction.ADD, order=_yes_bid_order(instrument, price, size), flags=0, sequence=sequence, ts_event=ts_event, ts_init=ts_init))
    for price, size in msg.get('no_dollars_fp') or []:
        deltas.append(OrderBookDelta(instrument_id=instrument.id, action=BookAction.ADD, order=_no_bid_as_yes_ask_order(instrument, price, size), flags=0, sequence=sequence, ts_event=ts_event, ts_init=ts_init))
    deltas[-1] = OrderBookDelta(instrument_id=instrument.id, action=deltas[-1].action, order=deltas[-1].order, flags=RecordFlag.F_LAST, sequence=sequence, ts_event=ts_event, ts_init=ts_init)
    return OrderBookDeltas(instrument.id, deltas)

def parse_kalshi_book_delta(instrument: BinaryOption, msg: dict[str, Any], sequence: int, ts_event: int, ts_init: int) -> OrderBookDeltas:
    side = msg.get('side')
    price = str(msg.get('price_dollars'))
    delta_size = float(msg.get('delta_fp') or msg.get('delta') or 0)
    if side == 'no':
        order = BookOrder(side=OrderSide.SELL, price=instrument.make_price(1.0 - float(price)), size=instrument.make_qty(abs(delta_size)), order_id=0)
    else:
        order = BookOrder(side=OrderSide.BUY, price=instrument.make_price(float(price)), size=instrument.make_qty(abs(delta_size)), order_id=0)
    action = BookAction.DELETE if order.size == 0 else BookAction.UPDATE
    delta = OrderBookDelta(instrument_id=instrument.id, action=action, order=order, flags=RecordFlag.F_LAST, sequence=sequence, ts_event=ts_event, ts_init=ts_init)
    return OrderBookDeltas(instrument.id, [delta])

def _kalshi_trade_id(ticker: str, msg: dict[str, Any], sequence: int) -> TradeId:
    existing = msg.get('trade_id')
    if existing:
        return TradeId(str(existing))
    digest = hashlib.blake2b(digest_size=8)
    digest.update(b'\x1f'.join((ticker.encode(), str(sequence).encode(), str(msg.get('yes_price_dollars') or msg.get('price_dollars')).encode(), str(msg.get('count_fp') or msg.get('count') or msg.get('size')).encode())))
    return TradeId(digest.hexdigest())

def parse_kalshi_trade(instrument: BinaryOption, msg: dict[str, Any], sequence: int, ts_event: int, ts_init: int) -> TradeTick:
    price = msg.get('yes_price_dollars') or msg.get('price_dollars')
    size = msg.get('count_fp') or msg.get('count') or msg.get('size') or 0
    taker_side = msg.get('taker_side')
    aggressor = AggressorSide.BUYER if taker_side == 'yes' else AggressorSide.SELLER if taker_side == 'no' else AggressorSide.NO_AGGRESSOR
    return TradeTick(instrument_id=instrument.id, price=instrument.make_price(float(price)), size=instrument.make_qty(float(size)), aggressor_side=aggressor, trade_id=_kalshi_trade_id(str(instrument.raw_symbol), msg, sequence), ts_event=ts_event, ts_init=ts_init)

KALSHI_FEE_RATE = Decimal('0.07')
_CENTICENT = Decimal('0.0001')

def calculate_kalshi_commission(quantity: Decimal, price: Decimal, fee_rate: Decimal=KALSHI_FEE_RATE) -> Decimal:
    fee = fee_rate * quantity * price * (Decimal(1) - price)
    return fee.quantize(_CENTICENT, rounding=ROUND_CEILING)
