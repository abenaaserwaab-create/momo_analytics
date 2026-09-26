"""Quick demo of the momo_analytics library. Run with: python demo.py"""

from momo_analytics import DailyLimitExceededError, MoMoTracker, Transaction

wallet = MoMoTracker(account_holder="Kofi Mensah", daily_limit=10000.0)

wallet.add_transaction(Transaction("TX101", "TRANSFER", 200.0, "0240000000"))
wallet.add_transaction(Transaction("TX102", "MERCHANT", 45.0, "Supermarket"))
wallet.add_transaction(Transaction("TX103", "AIRTIME", 10.0, "Self"))

print(f"\n📲 Account Holder: {wallet.account_holder}")

print("\n📊 Transactions Table (Pandas DataFrame):")
print(wallet.to_dataframe().to_string(index=False))

print("\n💰 Financial Summary:")
print(f"Total Spent:      GHS {wallet.get_total_spent():.2f}")
print(f"Total Fees Paid:  GHS {wallet.get_total_fees():.2f}")
print(f"Remaining Limit:  GHS {wallet.get_remaining_limit():.2f}")

print("\n📈 Spending by Type:")
print(wallet.spending_by_type().to_string())

# Try to breach the daily limit on purpose, to show the error is catchable.
try:
    wallet.add_transaction(Transaction("TX104", "CASH_OUT", 50000.0, "0240000000"))
except DailyLimitExceededError as e:
    print(f"\n🚫 Blocked as expected: {e}")

path = wallet.export_summary("momo_summary.json")
print(f"\n✅ Exported report to {path}!")
