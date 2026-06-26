from decimal import Decimal
from nautilus_trader.adapters.kalshi.common.parsing import calculate_kalshi_commission

def test_commission_matches_real_fill():
    assert calculate_kalshi_commission(Decimal("6.26"), Decimal("0.14")) == Decimal("0.0528")

def test_commission_canonical_example():
    assert calculate_kalshi_commission(Decimal("100"), Decimal("0.50")) == Decimal("1.7500")

def test_commission_rounds_up_to_centicent():
    fee = calculate_kalshi_commission(Decimal("1"), Decimal("0.16"))
    assert fee == fee.quantize(Decimal("0.0001"))
    assert fee > 0

def test_commission_symmetric_around_half():
    a = calculate_kalshi_commission(Decimal("100"), Decimal("0.30"))
    b = calculate_kalshi_commission(Decimal("100"), Decimal("0.70"))
    assert a == b
