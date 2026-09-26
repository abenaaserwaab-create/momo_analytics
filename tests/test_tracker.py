import pytest

from momo_analytics import (
    DailyLimitExceededError,
    InvalidTransactionError,
    MoMoTracker,
    Transaction,
    TransactionType,
)


# ----------------------------------------------------------------------
# Transaction validation
# ----------------------------------------------------------------------
def test_transaction_accepts_lowercase_type():
    tx = Transaction("TX01", "transfer", 10.0, "0240000000")
    assert tx.tx_type == TransactionType.TRANSFER


def test_transaction_rejects_zero_amount():
    with pytest.raises(InvalidTransactionError):
        Transaction("TX01", "TRANSFER", 0, "0240000000")


def test_transaction_rejects_negative_amount():
    with pytest.raises(InvalidTransactionError):
        Transaction("TX01", "TRANSFER", -50, "0240000000")


def test_transaction_rejects_empty_recipient():
    with pytest.raises(InvalidTransactionError):
        Transaction("TX01", "TRANSFER", 10.0, "")


def test_transaction_rejects_unknown_type():
    with pytest.raises(InvalidTransactionError):
        Transaction("TX01", "BITCOIN", 10.0, "0240000000")


# ----------------------------------------------------------------------
# Fee calculation (tier boundaries)
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "amount,expected_fee",
    [
        (25.0, 0.50),   # exact lower boundary
        (25.01, 1.00),  # just over
        (50.0, 1.00),
        (100.0, 1.50),
        (250.0, 2.50),
        (250.01, 4.00),
        (10000.0, 4.00),
    ],
)
def test_fee_tiers(amount, expected_fee):
    tracker = MoMoTracker("Ama")
    assert tracker.calculate_fee(amount) == expected_fee


# ----------------------------------------------------------------------
# Daily limit enforcement
# ----------------------------------------------------------------------
def test_limit_blocks_over_limit_transaction():
    tracker = MoMoTracker("Kofi", daily_limit=100.0)
    tx = Transaction("TX01", "TRANSFER", 150.0, "0240000000")
    with pytest.raises(DailyLimitExceededError):
        tracker.add_transaction(tx)


def test_limit_allows_exact_boundary():
    tracker = MoMoTracker("Kofi", daily_limit=100.0)
    tracker.add_transaction(Transaction("TX01", "TRANSFER", 100.0, "0240000000"))
    assert tracker.get_total_spent() == 100.0


def test_rejected_transaction_is_not_added():
    tracker = MoMoTracker("Kofi", daily_limit=100.0)
    with pytest.raises(DailyLimitExceededError):
        tracker.add_transaction(Transaction("TX01", "TRANSFER", 150.0, "0240000000"))
    assert len(tracker) == 0


# ----------------------------------------------------------------------
# Totals and reporting
# ----------------------------------------------------------------------
def test_totals_start_at_zero():
    tracker = MoMoTracker("Ama")
    assert tracker.get_total_spent() == 0.0
    assert tracker.get_total_fees() == 0.0


def test_running_totals_after_multiple_transactions():
    tracker = MoMoTracker("Kofi Mensah")
    tracker.add_transaction(Transaction("TX101", "TRANSFER", 200.0, "0240000000"))
    tracker.add_transaction(Transaction("TX102", "MERCHANT", 45.0, "Supermarket"))
    tracker.add_transaction(Transaction("TX103", "AIRTIME", 10.0, "Self"))

    assert tracker.get_total_spent() == 255.0
    assert tracker.get_total_fees() == pytest.approx(4.00)  # 2.50 + 1.00 + 0.50
    assert len(tracker) == 3


def test_remaining_limit():
    tracker = MoMoTracker("Ama", daily_limit=1000.0)
    tracker.add_transaction(Transaction("TX01", "TRANSFER", 400.0, "0240000000"))
    assert tracker.get_remaining_limit() == 600.0


def test_to_dataframe_shape():
    tracker = MoMoTracker("Ama")
    tracker.add_transaction(Transaction("TX01", "TRANSFER", 100.0, "0240000000"))
    df = tracker.to_dataframe()
    assert len(df) == 1
    assert "Amount (GHS)" in df.columns


def test_export_summary(tmp_path):
    tracker = MoMoTracker("Ama", daily_limit=1000.0)
    tracker.add_transaction(Transaction("TX01", "TRANSFER", 100.0, "0240000000"))

    out_file = tmp_path / "summary.json"
    tracker.export_summary(out_file)

    assert out_file.exists()
    import json
    data = json.loads(out_file.read_text())
    assert data["account_holder"] == "Ama"
    assert data["total_spent"] == 100.0
    assert data["total_transactions"] == 1
