import json
import os
import sys
from pathlib import Path

_REPO = str(Path(__file__).resolve().parents[4])
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != _REPO]

import pytest

_RESOURCES = Path(__file__).parent / "resources"

def load_fixture(name: str):
    with open(_RESOURCES / name) as f:
        return json.load(f)

@pytest.fixture
def http_market():
    return load_fixture("http_market.json")

@pytest.fixture
def http_order():
    return load_fixture("http_order.json")

@pytest.fixture
def http_fill():
    return load_fixture("http_fill.json")

@pytest.fixture
def http_position():
    return load_fixture("http_position.json")

@pytest.fixture
def ws_orderbook_snapshot():
    return load_fixture("ws_orderbook_snapshot.json")

@pytest.fixture
def ws_orderbook_delta():
    return load_fixture("ws_orderbook_delta.json")

@pytest.fixture
def http_orderbook():
    return load_fixture("http_orderbook.json")

@pytest.fixture
def http_trade():
    return load_fixture("http_trade.json")

@pytest.fixture
def http_candlestick():
    return load_fixture("http_candlestick.json")
