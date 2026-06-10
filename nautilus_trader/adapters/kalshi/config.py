from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProviderConfig
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.config import PositiveFloat
from nautilus_trader.config import PositiveInt
from nautilus_trader.model.identifiers import Venue

class KalshiDataClientConfig(LiveDataClientConfig, frozen=True):
    instrument_provider: KalshiInstrumentProviderConfig | None = None
    venue: Venue = KALSHI_VENUE
    api_key_id: str | None = None
    private_key_pem: str | None = None
    base_url_http: str | None = None
    base_url_ws: str | None = None
    ws_connection_delay_secs: PositiveFloat = 0.1
    update_instruments_interval_mins: PositiveInt | None = 60

class KalshiExecClientConfig(LiveExecClientConfig, frozen=True):
    instrument_provider: KalshiInstrumentProviderConfig | None = None
    venue: Venue = KALSHI_VENUE
    api_key_id: str | None = None
    private_key_pem: str | None = None
    base_url_http: str | None = None
    base_url_ws: str | None = None
    max_retries: PositiveInt | None = None
    retry_delay_initial_ms: PositiveInt | None = None
    retry_delay_max_ms: PositiveInt | None = None
