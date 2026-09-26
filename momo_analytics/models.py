"""Data models for momo_analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .exceptions import InvalidTransactionError


class TransactionType(str, Enum):
    """The kinds of mobile money transaction this library understands."""

    TRANSFER = "TRANSFER"
    CASH_OUT = "CASH_OUT"
    AIRTIME = "AIRTIME"
    MERCHANT = "MERCHANT"


@dataclass
class Transaction:
    """A single mobile money transaction.

    Args:
        tx_id: A unique identifier for the transaction (e.g. "TX101").
        tx_type: One of the TransactionType values. A plain string such as
            "transfer" is accepted and normalized automatically.
        amount: The transaction amount. Must be greater than zero.
        recipient: Who or what received the money (a phone number, a
            merchant name, or "Self" for airtime top-ups).
        timestamp: When the transaction occurred. Defaults to now.

    Raises:
        InvalidTransactionError: If amount is not positive, tx_id or
            recipient is empty, or tx_type isn't a recognized type.
    """

    tx_id: str
    tx_type: TransactionType
    amount: float
    recipient: str
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not self.tx_id or not str(self.tx_id).strip():
            raise InvalidTransactionError("Transaction ID cannot be empty.")

        if not self.recipient or not str(self.recipient).strip():
            raise InvalidTransactionError("Recipient cannot be empty.")

        if isinstance(self.tx_type, str):
            try:
                self.tx_type = TransactionType(self.tx_type.upper())
            except ValueError as exc:
                valid = ", ".join(t.value for t in TransactionType)
                raise InvalidTransactionError(
                    f"Unknown transaction type {self.tx_type!r}. "
                    f"Expected one of: {valid}."
                ) from exc

        if self.amount <= 0:
            raise InvalidTransactionError(
                f"Amount must be greater than zero, got {self.amount}."
            )
