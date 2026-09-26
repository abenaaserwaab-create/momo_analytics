# momo_analytics

A small Python library for tracking and analyzing mobile money (MoMo) transactions —
running totals, tiered transaction fees, daily spending limits, and JSON export.

## Install

```bash
pip install -e .
```

## Quick start

```python
from momo_analytics import MoMoTracker, Transaction

wallet = MoMoTracker(account_holder="Kofi Mensah", daily_limit=10000.0)

wallet.add_transaction(Transaction("TX101", "TRANSFER", 200.0, "0240000000"))
wallet.add_transaction(Transaction("TX102", "MERCHANT", 45.0, "Supermarket"))

print(wallet.to_dataframe())
print("Total spent:", wallet.get_total_spent())
print("Total fees:", wallet.get_total_fees())

wallet.export_summary("momo_summary.json")
```

## Features

- **Validated transactions** — amounts must be positive, types are restricted to
  `TRANSFER`, `CASH_OUT`, `AIRTIME`, `MERCHANT` (case-insensitive on input).
- **Daily spending limits** — `add_transaction` raises `DailyLimitExceededError`
  (not a bare `ValueError`) if a transaction would exceed the limit; the
  transaction is not added.
- **Configurable fee schedule** — pass your own `fee_schedule` of
  `(upper_bound, fee)` tiers to `MoMoTracker` instead of using the built-in
  Ghanaian mobile money tiers.
- **Fast running totals** — `get_total_spent()` / `get_total_fees()` are O(1),
  not recomputed from scratch on every call.
- **Pandas-native** — `to_dataframe()` and `spending_by_type()` for analysis.
- **JSON export** — `export_summary()` writes an account summary to disk.

## Custom fee schedule example

```python
from momo_analytics import MoMoTracker

# Flat 1% fee up to 10,000, nothing beyond
custom_schedule = [(10000.0, 0.01), (float("inf"), 0.0)]
wallet = MoMoTracker("Ama", fee_schedule=custom_schedule)
```

## Running tests

```bash
pip install -e ".[dev]"
pytest
```
