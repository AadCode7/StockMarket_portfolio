from datetime import date, datetime, timezone, timedelta
import math
from app.ml.benchmark import benchmark_forward_returns
from app.schemas import PriceBar

def synthetic_bars(count=1100):
    start = date(2020, 1, 1)
    rows = []
    price = 100.0
    for index in range(count):
        # Deterministic, gently trending synthetic data for repeatable tests.
        price *= 1 + 0.0003 + math.sin(index / 13) * 0.002
        rows.append(PriceBar(
            symbol="TEST", exchange="NSE", trading_date=start + timedelta(days=index),
            open=price * 0.999, high=price * 1.01, low=price * 0.99, close=price,
            adjusted_close=price, volume=100000 + index * 10, provider="synthetic",
            retrieved_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        ))
    return rows

def test_walk_forward_benchmark_returns_multiple_model_scores():
    result = benchmark_forward_returns(synthetic_bars(), horizon_days=5)
    assert result["selected_model"] in {
        "ridge", "random_forest", "extra_trees", "hist_gradient_boosting", "zero_return_baseline"
    }
    assert len(result["model_scores"]) == 4
    assert result["validation"]["purge_gap_trading_days"] == 5
    assert math.isfinite(result["predicted_forward_return"])

def test_benchmark_rejects_insufficient_data():
    try:
        benchmark_forward_returns(synthetic_bars(350), horizon_days=60)
        assert False, "Expected a minimum-data error"
    except ValueError as exc:
        assert "Not enough clean observations" in str(exc)
