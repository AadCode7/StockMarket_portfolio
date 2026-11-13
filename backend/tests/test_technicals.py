from datetime import date, datetime, timezone, timedelta
from app.analytics.technicals import calculate_technicals
from app.schemas import PriceBar

def make_bars(count: int = 260):
    base = date(2024, 1, 1)
    return [
        PriceBar(
            symbol="TEST", exchange="NSE", trading_date=base + timedelta(days=i),
            open=100 + i * 0.1, high=101 + i * 0.1, low=99 + i * 0.1,
            close=100 + i * 0.1, adjusted_close=100 + i * 0.1,
            volume=1000 + i, provider="test",
            retrieved_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        for i in range(count)
    ]

def test_technical_indicators_return_expected_structure():
    result = calculate_technicals(make_bars())
    assert result["symbol"] == "TEST"
    assert result["observations"] == 260
    assert result["sma"]["20"] is not None
    assert result["rsi_14"] is not None
    assert result["macd"] is not None
    assert result["annualised_volatility_20d"] is not None

def test_technical_indicators_reject_empty_history():
    try:
        calculate_technicals([])
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "At least one" in str(exc)
