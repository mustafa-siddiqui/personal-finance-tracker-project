"""System-level integration tests for the backend (no UI layer).

These tests exercise the full vertical slice of the backend:
    Ledger -> Validator -> JsonTransactionRepository -> on-disk JSON file
plus BalanceCalculator and Analyzer reading from the same repository.

The UI layer (F7) is intentionally bypassed. This module gives
F1/F2/F3/F4/F5/F6/F8 system-level coverage that is
runnable today, regardless of the UI's state.

Run with:
    pytest tests/test_system_backend.py -v
"""

from __future__ import annotations

import datetime
import json
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
from src.application.analyzer import Analyzer, MonthlySummary
from src.application.balance_calculator import BalanceCalculator
from src.application.ledger import Ledger
from src.domain.exceptions import (
    PersistenceError,
    TransactionNotFound,
    UnsupportedSchemaVersion,
    ValidationError,
)
from src.domain.transaction import TransactionType
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


@pytest.fixture
def data_path(tmp_path: Path) -> Path:
    """A per-test JSON file path that does not exist yet."""
    return tmp_path / "transactions.json"


@pytest.fixture
def validator() -> Validator:
    return Validator(allowed_categories=ALLOWED_CATEGORIES)


@pytest.fixture
def repo(data_path: Path) -> JsonTransactionRepository:
    r = JsonTransactionRepository(path=data_path)
    r.load()
    return r


@pytest.fixture
def ledger(repo: JsonTransactionRepository, validator: Validator) -> Ledger:
    return Ledger(repo=repo, validator=validator)


# ---------------------------------------------------------------------------
# UC-1 Record a transaction (F1, F5, F6)
# ---------------------------------------------------------------------------


class TestUC1RecordTransaction:
    def test_happy_path_expense_persists_to_disk(self, ledger, data_path):
        """1.1 — Recording a valid expense returns a Transaction and persists it."""
        txn = ledger.record(
            type="expense",
            amount="42.50",
            category="food",
            description="Groceries",
            date="2026-06-13",
        )
        assert isinstance(txn.id, UUID)
        assert txn.type == TransactionType.EXPENSE
        assert txn.amount == Decimal("42.50")

        on_disk = json.loads(data_path.read_text())
        assert on_disk["schema_version"] == 1
        assert len(on_disk["transactions"]) == 1
        assert on_disk["transactions"][0]["amount"] == "42.50"
        assert on_disk["transactions"][0]["type"] == "expense"

    def test_happy_path_income(self, ledger, data_path):
        """1.2 — Income transactions persist with correct type."""
        ledger.record(
            type="income",
            amount="2500.00",
            category="salary",
            description="April paycheck",
            date="2026-04-15",
        )
        on_disk = json.loads(data_path.read_text())
        assert on_disk["transactions"][0]["type"] == "income"
        assert on_disk["transactions"][0]["category"] == "salary"

    def test_large_value_precision(self, ledger, data_path):
        """1.3 — D1 large amounts round-trip exactly through string serialization."""
        ledger.record(
            type="expense",
            amount="999999999999.99",
            category="other",
            description="boundary",
            date="2026-04-30",
        )
        on_disk = json.loads(data_path.read_text())
        assert on_disk["transactions"][0]["amount"] == "999999999999.99"

    def test_smallest_legal_amount(self, ledger, data_path):
        """1.4 — Amount 0.01 is accepted and persisted exactly."""
        ledger.record(
            type="expense",
            amount="0.01",
            category="other",
            description="penny",
            date="2026-04-30",
        )
        on_disk = json.loads(data_path.read_text())
        assert on_disk["transactions"][0]["amount"] == "0.01"

    def test_negative_amount_rejected(self, ledger, data_path):
        """1.6 — Negative amounts raise ValidationError; nothing persisted."""
        with pytest.raises(ValidationError) as exc_info:
            ledger.record(
                type="expense",
                amount="-10.00",
                category="food",
                description="bad",
                date="2026-04-30",
            )
        assert exc_info.value.field == "amount"
        assert not data_path.exists()

    def test_zero_amount_rejected(self, ledger, data_path):
        """1.7 — Amount of exactly zero is rejected (boundary)."""
        with pytest.raises(ValidationError) as exc_info:
            ledger.record(
                type="expense",
                amount="0",
                category="food",
                description="zero",
                date="2026-04-30",
            )
        assert exc_info.value.field == "amount"

    def test_non_numeric_amount_rejected(self, ledger):
        """1.8 — Garbage amount strings are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ledger.record(
                type="expense",
                amount="abc",
                category="food",
                description="bad",
                date="2026-04-30",
            )
        assert exc_info.value.field == "amount"

    def test_disallowed_category_rejected(self, ledger):
        """1.9 — Categories outside the allowed set are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ledger.record(
                type="expense",
                amount="10.00",
                category="crypto",
                description="bad",
                date="2026-04-30",
            )
        assert exc_info.value.field == "category"

    def test_empty_description_rejected(self, ledger):
        """1.10 — Empty descriptions are rejected (boundary)."""
        with pytest.raises(ValidationError) as exc_info:
            ledger.record(
                type="expense",
                amount="10.00",
                category="food",
                description="",
                date="2026-04-30",
            )
        assert exc_info.value.field == "description"

    def test_malformed_date_rejected(self, ledger):
        """1.11 — Wrong date format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ledger.record(
                type="expense",
                amount="10.00",
                category="food",
                description="bad date",
                date="2026/04/30",
            )
        assert exc_info.value.field == "date"

    def test_invalid_type_rejected(self, ledger):
        """1.13 — type values outside {income, expense} are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ledger.record(
                type="transfer",
                amount="10.00",
                category="food",
                description="bad type",
                date="2026-04-30",
            )
        assert exc_info.value.field == "type"

    def test_uuids_unique_across_calls(self, ledger):
        """1.15 — Two consecutive record() calls produce different UUIDs."""
        a = ledger.record(
            type="expense",
            amount="10.00",
            category="food",
            description="A",
            date="2026-04-30",
        )
        b = ledger.record(
            type="expense",
            amount="10.00",
            category="food",
            description="B",
            date="2026-04-30",
        )
        assert a.id != b.id


# ---------------------------------------------------------------------------
# UC-2 View / list transactions (F2)
# ---------------------------------------------------------------------------


class TestUC2ListTransactions:
    def test_empty_store_lists_empty(self, repo):
        """2.1 — list_all() on a fresh repo returns an empty list."""
        assert repo.list_all() == []

    def test_populated_store_lists_all(self, ledger, repo):
        """2.2 — list_all() returns every recorded transaction."""
        for i in range(3):
            ledger.record(
                type="expense",
                amount="10.00",
                category="food",
                description=f"txn {i}",
                date="2026-04-30",
            )
        assert len(repo.list_all()) == 3

    def test_round_trip_field_fidelity(self, ledger, data_path, validator):
        """2.3 — Reloading a fresh repo from disk preserves every field."""
        ledger.record(
            type="expense",
            amount="42.50",
            category="food",
            description="Groceries",
            date="2026-04-27",
        )
        fresh = JsonTransactionRepository(path=data_path)
        fresh.load()
        reloaded = fresh.list_all()
        assert len(reloaded) == 1
        t = reloaded[0]
        assert t.type == TransactionType.EXPENSE
        assert t.amount == Decimal("42.50")
        assert t.category == "food"
        assert t.description == "Groceries"
        assert t.date == datetime.date(2026, 4, 27)


# ---------------------------------------------------------------------------
# UC-3 Calculate balance (F3)
# ---------------------------------------------------------------------------


class TestUC3Balance:
    def test_empty_store_balance_is_zero(self, repo):
        """3.1 — Balance of an empty store is exactly Decimal('0')."""
        assert BalanceCalculator.calculate(repo.list_all()) == Decimal("0")

    def test_income_only(self, ledger, repo):
        """3.2 — Single income transaction yields its amount as the balance."""
        ledger.record(
            type="income",
            amount="2500.00",
            category="salary",
            description="paycheck",
            date="2026-04-15",
        )
        assert BalanceCalculator.calculate(repo.list_all()) == Decimal("2500.00")

    def test_expenses_only_negative(self, ledger, repo):
        """3.3 — Two expenses with no income yields a negative balance."""
        for amt, desc in [("42.50", "groceries"), ("100.00", "gas")]:
            ledger.record(
                type="expense",
                amount=amt,
                category="food",
                description=desc,
                date="2026-04-27",
            )
        assert BalanceCalculator.calculate(repo.list_all()) == Decimal("-142.50")

    def test_mixed_income_and_expenses(self, ledger, repo):
        """3.4 — Mixed income/expense yields income minus total expenses."""
        ledger.record(
            type="income",
            amount="1000.00",
            category="salary",
            description="pay",
            date="2026-04-15",
        )
        ledger.record(
            type="expense",
            amount="200.00",
            category="food",
            description="x",
            date="2026-04-20",
        )
        ledger.record(
            type="expense",
            amount="50.00",
            category="transportation",
            description="y",
            date="2026-04-21",
        )
        assert BalanceCalculator.calculate(repo.list_all()) == Decimal("750.00")

    def test_large_value_precision(self, ledger, repo):
        """3.5 — Large amounts retain full Decimal precision through balance math."""
        ledger.record(
            type="income",
            amount="999999999999.99",
            category="salary",
            description="big",
            date="2026-04-15",
        )
        assert BalanceCalculator.calculate(repo.list_all()) == Decimal(
            "999999999999.99"
        )


# ---------------------------------------------------------------------------
# UC-4 Delete a transaction (F4, F5)
# ---------------------------------------------------------------------------


class TestUC4DeleteTransaction:
    def test_delete_existing_transaction_persists(self, ledger, repo, data_path):
        """4.1 — Deleting an existing UUID removes it and persists the change."""
        txn = ledger.record(
            type="expense",
            amount="10.00",
            category="food",
            description="x",
            date="2026-04-30",
        )
        ledger.delete(txn.id)
        assert repo.list_all() == []
        on_disk = json.loads(data_path.read_text())
        assert on_disk["transactions"] == []

    def test_delete_unknown_uuid_raises(self, ledger):
        """4.2 — Deleting a UUID not in the store raises TransactionNotFound."""
        unknown = UUID("00000000-0000-0000-0000-000000000000")
        with pytest.raises(TransactionNotFound):
            ledger.delete(unknown)

    def test_delete_rejects_string_argument(self, ledger):
        """4.3 — Defensive isinstance check: passing a string raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ledger.delete("00000000-0000-0000-0000-000000000000")  # type: ignore[arg-type]
        assert exc_info.value.field == "id"


# ---------------------------------------------------------------------------
# UC-5 Persistence across restarts (F5)
# ---------------------------------------------------------------------------


class TestUC5Persistence:
    def test_round_trip_across_repo_instances(self, ledger, validator, data_path):
        """5.1 — A fresh repository instance loads exactly what was saved."""
        ledger.record(
            type="income",
            amount="100.00",
            category="salary",
            description="A",
            date="2026-04-15",
        )
        ledger.record(
            type="expense",
            amount="40.00",
            category="food",
            description="B",
            date="2026-04-16",
        )
        fresh = JsonTransactionRepository(path=data_path)
        fresh.load()
        assert len(fresh.list_all()) == 2

    def test_missing_file_loads_as_empty(self, data_path):
        """5.2 — A non-existent JSON file loads to an empty store, no error."""
        assert not data_path.exists()
        repo = JsonTransactionRepository(path=data_path)
        repo.load()
        assert repo.list_all() == []

    def test_corrupt_file_raises_persistence_error(self, data_path):
        """5.3 — Malformed JSON raises PersistenceError; existing file is not overwritten."""
        data_path.write_text("not json {{")
        repo = JsonTransactionRepository(path=data_path)
        with pytest.raises(PersistenceError):
            repo.load()
        # The garbage file is left as-is for the operator to inspect.
        assert data_path.read_text() == "not json {{"

    def test_unsupported_schema_version_raises(self, data_path):
        """5.4 — A schema_version the loader doesn't recognize raises UnsupportedSchemaVersion."""
        data_path.write_text(json.dumps({"schema_version": 999, "transactions": []}))
        repo = JsonTransactionRepository(path=data_path)
        with pytest.raises(UnsupportedSchemaVersion):
            repo.load()


# ---------------------------------------------------------------------------
# UC-8 Analytics (F8)
# ---------------------------------------------------------------------------


class TestUC8Analytics:
    def test_category_totals_aggregates_correctly(self, ledger, repo):
        """8.1 — category_totals groups expenses by category and sums them."""
        for amt, cat in [
            ("40.00", "food"),
            ("60.00", "food"),
            ("25.00", "transportation"),
        ]:
            ledger.record(
                type="expense",
                amount=amt,
                category=cat,
                description="x",
                date="2026-04-15",
            )
        analyzer = Analyzer(repo=repo)
        totals = analyzer.category_totals(TransactionType.EXPENSE)
        assert totals == {"food": Decimal("100.00"), "transportation": Decimal("25.00")}

    def test_highest_spending_category(self, ledger, repo):
        """8.2 — highest_spending_category returns the category with the max total."""
        for amt, cat in [
            ("40.00", "food"),
            ("60.00", "food"),
            ("25.00", "transportation"),
        ]:
            ledger.record(
                type="expense",
                amount=amt,
                category=cat,
                description="x",
                date="2026-04-15",
            )
        analyzer = Analyzer(repo=repo)
        top = analyzer.highest_spending_category()
        assert top is not None
        assert top.category == "food"
        assert top.total == Decimal("100.00")

    def test_highest_spending_empty_returns_none(self, repo):
        """8.3 — highest_spending_category returns None when there are no expenses."""
        analyzer = Analyzer(repo=repo)
        assert analyzer.highest_spending_category() is None

    def test_monthly_summary_populated(self, ledger, repo):
        """8.4 — monthly_summary returns income, expense, and net for the requested month."""
        ledger.record(
            type="income",
            amount="1000.00",
            category="salary",
            description="pay",
            date="2026-04-15",
        )
        ledger.record(
            type="expense",
            amount="200.00",
            category="food",
            description="groc",
            date="2026-04-20",
        )
        analyzer = Analyzer(repo=repo)
        summary = analyzer.monthly_summary(2026, 4)
        assert summary == MonthlySummary(
            year=2026,
            month=4,
            total_income=Decimal("1000.00"),
            total_expenses=Decimal("200.00"),
            net=Decimal("800.00"),
        )

    def test_monthly_summary_empty_month_zeroed(self, repo):
        """8.5 — Querying a month with no data returns a zeroed MonthlySummary, no error."""
        analyzer = Analyzer(repo=repo)
        summary = analyzer.monthly_summary(2026, 1)
        assert summary.total_income == Decimal("0")
        assert summary.total_expenses == Decimal("0")
        assert summary.net == Decimal("0")

    def test_monthly_trends_chronological(self, ledger, repo):
        """8.6 — monthly_trends returns one entry per month in chronological order."""
        for date_str in ["2026-04-15", "2026-05-15", "2026-06-15"]:
            ledger.record(
                type="income",
                amount="100.00",
                category="salary",
                description="x",
                date=date_str,
            )
        analyzer = Analyzer(repo=repo)
        trends = analyzer.monthly_trends()
        assert [(t.year, t.month) for t in trends] == [(2026, 4), (2026, 5), (2026, 6)]
