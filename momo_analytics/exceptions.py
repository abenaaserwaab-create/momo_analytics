"""Custom exceptions for momo_analytics.

Using specific exception types (instead of bare ValueError) lets calling
code distinguish "this transaction was malformed" from "this transaction
was valid but would blow the daily limit" without string-matching error
messages.
"""


class MoMoError(Exception):
    """Base class for all momo_analytics errors."""


class InvalidTransactionError(MoMoError):
    """Raised when a Transaction is constructed with invalid data."""


class DailyLimitExceededError(MoMoError):
    """Raised when adding a transaction would exceed the account's daily limit."""

    def __init__(self, attempted_amount: float, current_total: float, daily_limit: float):
        self.attempted_amount = attempted_amount
        self.current_total = current_total
        self.daily_limit = daily_limit
        super().__init__(
            f"Adding GHS {attempted_amount:.2f} would bring today's total to "
            f"GHS {current_total + attempted_amount:.2f}, exceeding the daily "
            f"limit of GHS {daily_limit:.2f}."
        )
