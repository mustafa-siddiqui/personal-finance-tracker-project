"""Personal Finance Tracker — application entry point.

Currently a smoke test that exercises F1 (record) and F5 (persist) end-to-end
against a real JSON file. As more features are implemented, this file will
grow into the full application wiring (UI, full Ledger, BalanceCalculator,
Analyzer).

Run from the project root with the virtual environment activated:

    python main.py
"""

from __future__ import annotations

from pathlib import Path

from src.application.ledger import Ledger
from src.domain.validator import Validator
from src.repository.json_transaction_repository import JsonTransactionRepository

ALLOWED_CATEGORIES = [
    "salary",
    "freelance",
    "food",
    "transportation",
    "housing",
    "utilities",
    "entertainment",
    "healthcare",
    "education",
    "other",
]

DATA_PATH = Path("data") / "transactions.json"


def main() -> None:
    # Start fresh so the smoke test is reproducible
    if DATA_PATH.exists():
        DATA_PATH.unlink()

    print(f"=== Smoke test — writing to {DATA_PATH} ===\n")

    validator = Validator(allowed_categories=ALLOWED_CATEGORIES)
    repo = JsonTransactionRepository(path=DATA_PATH)
    repo.load()  # No-op on missing file (returns empty store)
    ledger = Ledger(repo=repo, validator=validator)

    # Record three transactions
    ledger.record(
        type="income",
        amount="2500.00",
        category="salary",
        description="April paycheck",
        date="2026-04-15",
    )
    ledger.record(
        type="expense",
        amount="42.50",
        category="food",
        description="Groceries",
        date="2026-04-27",
    )
    ledger.record(
        type="expense",
        amount="999999999999.99",
        category="other",
        description="Boundary-value test",
        date="2026-04-30",
    )

    print(f"Wrote {len(repo.list_all())} transactions to disk.\n")

    # Re-load from disk in a fresh repository instance to prove round-trip works
    fresh_repo = JsonTransactionRepository(path=DATA_PATH)
    fresh_repo.load()
    print(f"=== Loaded {len(fresh_repo.list_all())} transactions from disk ===\n")
    for txn in fresh_repo.list_all():
        print(
            f"  {txn.date} {txn.type.value:<7} {txn.amount:>20} "
            f"{txn.category:<15} {txn.description}"
        )

    print("\n=== Validation failure path ===\n")
    try:
        ledger.record(
            type="expense",
            amount="-10",
            category="food",
            description="Negative amount",
            date="2026-04-30",
        )
    except Exception as e:
        print(f"  Caught {type(e).__name__}: {e}")

    print("\nSmoke test complete.")


if __name__ == "__main__":
    main()
