from __future__ import annotations
import asyncio
from decimal import Decimal
from typing import Any
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.adapters.kalshi.common.enums import kalshi_side_from_order_side
from nautilus_trader.adapters.kalshi.common.enums import kalshi_time_in_force
from nautilus_trader.adapters.kalshi.common.enums import order_side_from_kalshi_side
from nautilus_trader.adapters.kalshi.common.enums import order_status_from_kalshi
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_instrument_id
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_ticker
from nautilus_trader.adapters.kalshi.config import KalshiExecClientConfig
from nautilus_trader.adapters.kalshi.http.errors import KalshiHttpError
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.core.uuid import UUID4
from nautilus_trader.execution.messages import BatchCancelOrders
from nautilus_trader.execution.messages import CancelAllOrders
from nautilus_trader.execution.messages import CancelOrder
from nautilus_trader.execution.messages import GenerateFillReports
from nautilus_trader.execution.messages import GenerateOrderStatusReport
from nautilus_trader.execution.messages import GenerateOrderStatusReports
from nautilus_trader.execution.messages import GeneratePositionStatusReports
from nautilus_trader.execution.messages import ModifyOrder
from nautilus_trader.execution.messages import SubmitOrder
from nautilus_trader.execution.messages import SubmitOrderList
from nautilus_trader.execution.reports import FillReport
from nautilus_trader.execution.reports import OrderStatusReport
from nautilus_trader.execution.reports import PositionStatusReport
from nautilus_trader.live.execution_client import LiveExecutionClient
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import LiquiditySide
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import PositionSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import AccountId
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import ClientOrderId
from nautilus_trader.model.identifiers import TradeId
from nautilus_trader.model.identifiers import VenueOrderId
from nautilus_trader.model.objects import AccountBalance
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
from nautilus_trader.model.orders import Order

class KalshiExecutionClient(LiveExecutionClient):

    def __init__(self, loop: asyncio.AbstractEventLoop, client: Any, msgbus: Any, cache: Any, clock: Any, instrument_provider: KalshiInstrumentProvider, config: KalshiExecClientConfig, name: str | None=None) -> None:
        super().__init__(loop=loop, client_id=ClientId(name or KALSHI_VENUE.value), venue=config.venue, oms_type=OmsType.NETTING, account_type=AccountType.CASH, base_currency=USD, instrument_provider=instrument_provider, msgbus=msgbus, cache=cache, clock=clock, config=config)
        self._http_client = client
        self._config = config
        self._account_id = AccountId(f'{(name or KALSHI_VENUE.value)}-001')

    async def _connect(self) -> None:
        self._set_account_id(self._account_id)
        await self._instrument_provider.initialize()
        await self._update_account_state()

    async def _disconnect(self) -> None:
        pass

    async def _update_account_state(self) -> None:
        response = await self._http_client.get('/portfolio/balance')
        total = Decimal(str(response.get('balance_dollars') or '0'))
        balance = AccountBalance(total=Money(total, USD), locked=Money(Decimal(0), USD), free=Money(total, USD))
        self.generate_account_state(balances=[balance], margins=[], reported=True, ts_event=self._clock.timestamp_ns())

    def _order_payload(self, order: Order) -> dict[str, Any]:
        payload: dict[str, Any] = {'ticker': get_kalshi_ticker(order.instrument_id), 'side': kalshi_side_from_order_side(order.side).value, 'count': f'{order.quantity.as_double():.2f}', 'time_in_force': kalshi_time_in_force(order.time_in_force), 'self_trade_prevention_type': 'taker_at_cross', 'client_order_id': order.client_order_id.value}
        if order.order_type == OrderType.LIMIT:
            payload['price'] = f'{float(order.price):.4f}'
        return payload

    def _resolve_venue_order_id(self, instrument_id: Any, client_order_id: ClientOrderId, venue_order_id: VenueOrderId | None) -> VenueOrderId | None:
        if venue_order_id is not None:
            return venue_order_id
        order = self._cache.order(client_order_id)
        return order.venue_order_id if order is not None and order.venue_order_id is not None else None

    async def _submit_order(self, command: SubmitOrder) -> None:
        order: Order = command.order
        if self._cache.instrument(command.instrument_id) is None:
            self.generate_order_rejected(command.strategy_id, command.instrument_id, order.client_order_id, f'no instrument for {command.instrument_id}', self._clock.timestamp_ns())
            return
        if order.order_type not in (OrderType.LIMIT, OrderType.MARKET):
            self.generate_order_rejected(command.strategy_id, command.instrument_id, order.client_order_id, f'unsupported order type {order.order_type}', self._clock.timestamp_ns())
            return
        self.generate_order_submitted(command.strategy_id, command.instrument_id, order.client_order_id, self._clock.timestamp_ns())
        try:
            response = await self._http_client.post('/portfolio/events/orders', payload=self._order_payload(order))
        except KalshiHttpError as e:
            self.generate_order_rejected(command.strategy_id, command.instrument_id, order.client_order_id, str(e), self._clock.timestamp_ns())
            return
        venue_order_id = response.get('order_id') if response else None
        if venue_order_id:
            self.generate_order_accepted(command.strategy_id, command.instrument_id, order.client_order_id, VenueOrderId(str(venue_order_id)), self._clock.timestamp_ns())

    async def _submit_order_list(self, command: SubmitOrderList) -> None:
        orders = command.order_list.orders
        for order in orders:
            self.generate_order_submitted(command.strategy_id, order.instrument_id, order.client_order_id, self._clock.timestamp_ns())
        payload = {'orders': [self._order_payload(order) for order in orders]}
        try:
            response = await self._http_client.post('/portfolio/events/orders/batched', payload=payload)
        except KalshiHttpError as e:
            for order in orders:
                self.generate_order_rejected(command.strategy_id, order.instrument_id, order.client_order_id, str(e), self._clock.timestamp_ns())
            return
        results = response.get('orders') or [] if response else []
        for order, result in zip(orders, results):
            error = result.get('error')
            if error:
                self.generate_order_rejected(command.strategy_id, order.instrument_id, order.client_order_id, str(error), self._clock.timestamp_ns())
            elif result.get('order_id'):
                self.generate_order_accepted(command.strategy_id, order.instrument_id, order.client_order_id, VenueOrderId(str(result['order_id'])), self._clock.timestamp_ns())

    async def _modify_order(self, command: ModifyOrder) -> None:
        venue_order_id = self._resolve_venue_order_id(command.instrument_id, command.client_order_id, command.venue_order_id)
        if venue_order_id is None:
            self.generate_order_modify_rejected(command.strategy_id, command.instrument_id, command.client_order_id, None, 'no venue order id', self._clock.timestamp_ns())
            return
        order = self._cache.order(command.client_order_id)
        if order is None:
            self.generate_order_modify_rejected(command.strategy_id, command.instrument_id, command.client_order_id, venue_order_id, 'order not in cache', self._clock.timestamp_ns())
            return
        price = command.price if command.price is not None else order.price
        count = command.quantity if command.quantity is not None else order.quantity
        payload = {'ticker': get_kalshi_ticker(command.instrument_id), 'side': kalshi_side_from_order_side(order.side).value, 'price': f'{float(price):.4f}', 'count': f'{count.as_double():.2f}'}
        try:
            await self._http_client.post(f'/portfolio/events/orders/{venue_order_id.value}/amend', payload=payload)
        except KalshiHttpError as e:
            self.generate_order_modify_rejected(command.strategy_id, command.instrument_id, command.client_order_id, venue_order_id, str(e), self._clock.timestamp_ns())
            return
        self.generate_order_updated(command.strategy_id, command.instrument_id, command.client_order_id, venue_order_id, count, price, None, self._clock.timestamp_ns())

    async def _cancel_order(self, command: CancelOrder) -> None:
        venue_order_id = self._resolve_venue_order_id(command.instrument_id, command.client_order_id, command.venue_order_id)
        if venue_order_id is None:
            self.generate_order_cancel_rejected(command.strategy_id, command.instrument_id, command.client_order_id, None, 'no venue order id', self._clock.timestamp_ns())
            return
        try:
            await self._http_client.delete(f'/portfolio/events/orders/{venue_order_id.value}')
        except KalshiHttpError as e:
            self.generate_order_cancel_rejected(command.strategy_id, command.instrument_id, command.client_order_id, venue_order_id, str(e), self._clock.timestamp_ns())
            return
        self.generate_order_canceled(command.strategy_id, command.instrument_id, command.client_order_id, venue_order_id, self._clock.timestamp_ns())

    async def _batch_cancel_orders(self, command: BatchCancelOrders) -> None:
        entries = []
        mapping = []
        for cancel in command.cancels:
            venue_order_id = self._resolve_venue_order_id(cancel.instrument_id, cancel.client_order_id, cancel.venue_order_id)
            if venue_order_id is None:
                self.generate_order_cancel_rejected(command.strategy_id, cancel.instrument_id, cancel.client_order_id, None, 'no venue order id', self._clock.timestamp_ns())
                continue
            entries.append({'order_id': venue_order_id.value})
            mapping.append((cancel, venue_order_id))
        if not entries:
            return
        try:
            await self._http_client.delete('/portfolio/events/orders/batched', payload={'orders': entries})
        except KalshiHttpError as e:
            for cancel, venue_order_id in mapping:
                self.generate_order_cancel_rejected(command.strategy_id, cancel.instrument_id, cancel.client_order_id, venue_order_id, str(e), self._clock.timestamp_ns())
            return
        for cancel, venue_order_id in mapping:
            self.generate_order_canceled(command.strategy_id, cancel.instrument_id, cancel.client_order_id, venue_order_id, self._clock.timestamp_ns())

    async def _cancel_all_orders(self, command: CancelAllOrders) -> None:
        open_orders = self._cache.orders_open(instrument_id=command.instrument_id)
        entries = []
        mapping = []
        for order in open_orders:
            if command.order_side is not None and command.order_side != OrderSide.NO_ORDER_SIDE and order.side != command.order_side:
                continue
            if order.venue_order_id is None:
                continue
            entries.append({'order_id': order.venue_order_id.value})
            mapping.append(order)
        if not entries:
            return
        try:
            await self._http_client.delete('/portfolio/events/orders/batched', payload={'orders': entries})
        except KalshiHttpError as e:
            self._log.error(f'Failed to cancel all orders: {e}')
            return
        for order in mapping:
            self.generate_order_canceled(command.strategy_id, order.instrument_id, order.client_order_id, order.venue_order_id, self._clock.timestamp_ns())

    async def generate_order_status_reports(self, command: GenerateOrderStatusReports) -> list[OrderStatusReport]:
        response = await self._http_client.get('/portfolio/orders', params={'limit': 1000})
        reports = []
        for order in response.get('orders') or []:
            report = self._parse_order_report(order)
            if report is not None:
                reports.append(report)
        return reports

    async def generate_order_status_report(self, command: GenerateOrderStatusReport) -> OrderStatusReport | None:
        if command.venue_order_id is None:
            return None
        try:
            response = await self._http_client.get(f'/portfolio/orders/{command.venue_order_id.value}')
        except KalshiHttpError:
            return None
        order = response.get('order')
        return self._parse_order_report(order) if order else None

    async def generate_fill_reports(self, command: GenerateFillReports) -> list[FillReport]:
        response = await self._http_client.get('/portfolio/fills', params={'limit': 1000})
        reports = []
        for fill in response.get('fills') or []:
            report = self._parse_fill_report(fill)
            if report is not None:
                reports.append(report)
        return reports

    async def generate_position_status_reports(self, command: GeneratePositionStatusReports) -> list[PositionStatusReport]:
        response = await self._http_client.get('/portfolio/positions', params={'limit': 1000})
        reports = []
        for position in response.get('market_positions') or []:
            report = self._parse_position_report(position)
            if report is not None:
                reports.append(report)
        return reports

    def _yes_price(self, data: dict[str, Any]) -> Price | None:
        if data.get('yes_price_dollars') is not None:
            return Price(float(data['yes_price_dollars']), 2)
        return None

    def _book_side(self, data: dict[str, Any]) -> OrderSide:
        return order_side_from_kalshi_side(data.get('book_side', 'bid'))

    def _parse_order_report(self, order: dict[str, Any]) -> OrderStatusReport | None:
        ticker = order.get('ticker')
        if not ticker:
            return None
        instrument_id = get_kalshi_instrument_id(ticker)
        price = self._yes_price(order)
        count = float(order.get('initial_count_fp') or 0)
        filled = float(order.get('fill_count_fp') or 0)
        now = self._clock.timestamp_ns()
        return OrderStatusReport(account_id=self._account_id, instrument_id=instrument_id, venue_order_id=VenueOrderId(str(order['order_id'])), order_side=self._book_side(order), order_type=OrderType.LIMIT if order.get('type') == 'limit' else OrderType.MARKET, time_in_force=TimeInForce.GTC, order_status=order_status_from_kalshi(order.get('status', 'resting')), quantity=Quantity(count, 2), filled_qty=Quantity(filled, 2), report_id=UUID4(), ts_accepted=now, ts_last=now, ts_init=now, client_order_id=ClientOrderId(order['client_order_id']) if order.get('client_order_id') else None, price=price)

    def _parse_fill_report(self, fill: dict[str, Any]) -> FillReport | None:
        ticker = fill.get('ticker')
        if not ticker:
            return None
        instrument_id = get_kalshi_instrument_id(ticker)
        last_px = self._yes_price(fill) or Price(0.0, 2)
        now = self._clock.timestamp_ns()
        return FillReport(account_id=self._account_id, instrument_id=instrument_id, venue_order_id=VenueOrderId(str(fill['order_id'])), trade_id=TradeId(str(fill.get('trade_id') or fill.get('fill_id'))), order_side=self._book_side(fill), last_qty=Quantity(float(fill.get('count_fp') or 0), 2), last_px=last_px, commission=Money(Decimal(str(fill.get('fee_cost') or 0)), USD), liquidity_side=LiquiditySide.TAKER if fill.get('is_taker') else LiquiditySide.MAKER, report_id=UUID4(), ts_event=now, ts_init=now)

    def _parse_position_report(self, position: dict[str, Any]) -> PositionStatusReport | None:
        ticker = position.get('ticker')
        if not ticker:
            return None
        net = float(position.get('position_fp') or 0)
        if net == 0:
            return None
        instrument_id = get_kalshi_instrument_id(ticker)
        side = PositionSide.LONG if net > 0 else PositionSide.SHORT
        now = self._clock.timestamp_ns()
        return PositionStatusReport(account_id=self._account_id, instrument_id=instrument_id, position_side=side, quantity=Quantity(abs(net), 2), report_id=UUID4(), ts_last=now, ts_init=now)
