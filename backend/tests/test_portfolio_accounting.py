import pytest
from app.portfolio.accounting import PortfolioAccountingError, aggregate_transactions

def test_weighted_average_cost_and_realised_pnl():
    rows = [
        {"instrument_id": "a", "transaction_type": "BUY", "quantity": 10, "price": 100, "charges": 10, "executed_at": "2024-01-01T10:00:00+05:30"},
        {"instrument_id": "a", "transaction_type": "BUY", "quantity": 10, "price": 120, "charges": 10, "executed_at": "2024-01-02T10:00:00+05:30"},
        {"instrument_id": "a", "transaction_type": "SELL", "quantity": 5, "price": 150, "charges": 5, "executed_at": "2024-01-03T10:00:00+05:30"},
    ]
    state = aggregate_transactions(rows)["a"]
    assert float(state["quantity"]) == 15
    assert float(state["cost"]) == 1665
    assert round(float(state["realized_pnl"]), 2) == 190

def test_overselling_is_rejected():
    rows = [{"instrument_id": "a", "transaction_type": "SELL", "quantity": 1, "price": 100, "charges": 0, "executed_at": "2024-01-01T10:00:00+05:30"}]
    with pytest.raises(PortfolioAccountingError):
        aggregate_transactions(rows)

def test_dividend_and_fee_are_tracked_separately():
    rows = [
        {"instrument_id": "a", "transaction_type": "DIVIDEND", "quantity": 0, "price": 50, "charges": 2, "executed_at": "2024-01-01T10:00:00+05:30"},
        {"instrument_id": "a", "transaction_type": "FEE", "quantity": 0, "price": 10, "charges": 1, "executed_at": "2024-01-02T10:00:00+05:30"},
    ]
    state = aggregate_transactions(rows)["a"]
    assert float(state["dividends"]) == 48
    assert float(state["fees"]) == 11
