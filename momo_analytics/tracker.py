"""The core tracking and analytics engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import pandas as pd

from .exceptions import DailyLimitExceededError
from .models import Transaction

# (upper_bound_inclusive, fee) tiers. The last tier's bound is ignored;
# it just needs to be higher than any realistic amount.
DEFAULT_FEE_SCHEDULE: Tuple[Tuple[float, float], ...] = (
    (25.0, 0.50),
    (50.0, 1.00),
    (100.0, 1.50),
    (250.0, 2.50),
    (float("inf"), 4.00),
)


class MoMoTracker:
    """Tracks mobile money transactions for one account and reports on them.

    Args:
        account_holder: Display name of the account owner.
        daily_limit: Maximum total amount (in `currency`) that can be spent
            per instance of this tracker. Defaults to 10,000.
        fee_schedule: A sequence of (upper_bound, fee) tuples, sorted
            ascending, describing transaction fee tiers. Defaults to a
            standard Ghanaian mobile money schedule.
        currency: Currency code used in printed output. Defaults to "GHS".
    """

    def __init__(
        self,
        account_holder: str,
        daily_limit: float = 10000.0,
        fee_schedule: Sequence[Tuple[float, float]] | None = None,
        currency: str = "GHS",
    ):
        self.account_holder = account_holder
        self.daily_limit = daily_limit
        self.currency = currency
        self.fee_schedule = tuple(fee_schedule) if fee_schedule else DEFAULT_FEE_SCHEDULE

        self._transactions: List[Transaction] = []
        self._total_spent: float = 0.0
        self._total_fees: float = 0.0

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------
    def calculate_fee(self, amount: float) -> float:
        """Return the fee owed for a transaction of the given amount."""
        for upper_bound, fee in self.fee_schedule:
            if amount <= upper_bound:
                return fee
        return self.fee_schedule[-1][1]

    def add_transaction(self, tx: Transaction) -> None:
        """Add a transaction, enforcing the daily limit.

        Raises:
            DailyLimitExceededError: If adding this transaction would push
                the running total over `daily_limit`. The transaction is
                not added in that case.
        """
        if (self._total_spent + tx.amount) > self.daily_limit:
            raise DailyLimitExceededError(tx.amount, self._total_spent, self.daily_limit)

        self._transactions.append(tx)
        self._total_spent += tx.amount
        self._total_fees += self.calculate_fee(tx.amount)

    def add_transactions(self, transactions: Iterable[Transaction]) -> None:
        """Add several transactions in order, stopping at the first that fails."""
        for tx in transactions:
            self.add_transaction(tx)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    @property
    def transactions(self) -> Tuple[Transaction, ...]:
        """Read-only view of the transactions added so far."""
        return tuple(self._transactions)

    def to_dataframe(self) -> pd.DataFrame:
        """Return all transactions as a pandas DataFrame, one row each."""
        data = [
            {
                "Tx ID": tx.tx_id,
                "Type": tx.tx_type.value,
                f"Amount ({self.currency})": tx.amount,
                f"Fee ({self.currency})": self.calculate_fee(tx.amount),
                "Recipient": tx.recipient,
                "Timestamp": tx.timestamp,
            }
            for tx in self._transactions
        ]
        columns = ["Tx ID", "Type", f"Amount ({self.currency})",
                   f"Fee ({self.currency})", "Recipient", "Timestamp"]
        return pd.DataFrame(data, columns=columns)

    def get_total_spent(self) -> float:
        """Total amount spent across all transactions (excludes fees)."""
        return self._total_spent

    def get_total_fees(self) -> float:
        """Total fees paid across all transactions."""
        return self._total_fees

    def get_remaining_limit(self) -> float:
        """How much more can be spent today before hitting the daily limit."""
        return max(0.0, self.daily_limit - self._total_spent)

    def spending_by_type(self) -> pd.Series:
        """Total amount spent, grouped by transaction type."""
        if not self._transactions:
            return pd.Series(dtype=float)
        df = self.to_dataframe()
        return df.groupby("Type")[f"Amount ({self.currency})"].sum()

    def export_summary(self, filepath: str | Path = "momo_summary.json") -> Path:
        """Write a JSON summary of the account to disk and return its path."""
        path = Path(filepath)
        data = {
            "account_holder": self.account_holder,
            "currency": self.currency,
            "daily_limit": self.daily_limit,
            "total_spent": self.get_total_spent(),
            "total_fees": self.get_total_fees(),
            "remaining_limit": self.get_remaining_limit(),
            "total_transactions": len(self._transactions),
        }
        path.write_text(json.dumps(data, indent=4))
        return path

    def __len__(self) -> int:
        return len(self._transactions)

    def __repr__(self) -> str:
        return (
            f"MoMoTracker(account_holder={self.account_holder!r}, "
            f"transactions={len(self._transactions)}, "
            f"total_spent={self._total_spent:.2f})"
        )
