from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

ZERO = Decimal("0")
EPSILON = Decimal("0.00000001")

class PortfolioAccountingError(ValueError):
    pass

def _executed_at(row: dict[str, Any]) -> datetime:
    value = row["executed_at"]
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

def aggregate_transactions(transactions: list[dict[str, Any]]) -> dict[str, dict[str, Decimal]]:
    """Apply a chronological weighted-average-cost ledger using decimal arithmetic.

    DIVIDEND and FEE amounts are stored in the price field. BUY charges enter
    cost basis; SELL charges reduce realised P&L.
    """
    state: dict[str, dict[str, Decimal]] = defaultdict(lambda: {
        "quantity": ZERO, "cost": ZERO, "realized_pnl": ZERO,
        "dividends": ZERO, "fees": ZERO,
    })
    try:
        ordered = sorted(transactions, key=_executed_at)
        for tx in ordered:
            item = state[tx["instrument_id"]]
            kind = tx["transaction_type"]
            quantity = Decimal(str(tx.get("quantity", 0)))
            price = Decimal(str(tx.get("price", 0)))
            charges = Decimal(str(tx.get("charges", 0)))
            if min(quantity, price, charges) < ZERO:
                raise PortfolioAccountingError("Transaction quantities, prices and charges cannot be negative")
            if kind == "BUY":
                item["quantity"] += quantity
                item["cost"] += quantity * price + charges
            elif kind == "SELL":
                if quantity > item["quantity"] + EPSILON:
                    raise PortfolioAccountingError(
                        f"Sell quantity exceeds available holdings for instrument {tx['instrument_id']}"
                    )
                average_cost = item["cost"] / item["quantity"] if item["quantity"] else ZERO
                item["realized_pnl"] += quantity * (price - average_cost) - charges
                item["quantity"] -= quantity
                item["cost"] -= quantity * average_cost
                if item["quantity"] <= EPSILON:
                    item["quantity"] = ZERO
                    item["cost"] = ZERO
            elif kind == "DIVIDEND":
                item["dividends"] += price - charges
            elif kind == "FEE":
                item["fees"] += price + charges
    except PortfolioAccountingError:
        raise
    except (InvalidOperation, TypeError, KeyError, ValueError) as exc:
        raise PortfolioAccountingError("Invalid transaction data in portfolio ledger") from exc
    return dict(state)
