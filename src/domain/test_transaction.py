"""Unit tests for Transaction and TransactionType."""

from __future__ import annotations

import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.transaction import Transaction, TransactionType


class TestTransactionType:
    def test_income_value(self) -> None:
        """INCOME enum member serializes to the string 'income' (matches JSON schema)."""
        assert TransactionType.INCOME.value == "income"

    def test_expense_value(self) -> None:
        """EXPENSE enum member serializes to the string 'expense' (matches JSON schema)."""
        assert TransactionType.EXPENSE.value == "expense"

    def test_only_two_members(self) -> None:
        """The enum has exactly two members; no third state should ever exist."""
        assert len(TransactionType) == 2


class TestTransactionConstruction:
    def test_all_fields_assigned(self) -> None:
        """All six constructor arguments are exposed unchanged as instance attributes."""
        txn_id = uuid4()
        txn = Transaction(
            id=txn_id,
            type=TransactionType.EXPENSE,
            amount=Decimal("42.50"),
            category="food",
            description="Groceries",
            date=datetime.date(2026, 4, 27),
        )
        assert txn.id == txn_id
        assert txn.type == TransactionType.EXPENSE
        assert txn.amount == Decimal("42.50")
        assert txn.category == "food"
        assert txn.description == "Groceries"
        assert txn.date == datetime.date(2026, 4, 27)

    def test_income_construction(self) -> None:
        """Income transactions can be constructed (parallel to expense path)."""
        txn = Transaction(
            id=uuid4(),
            type=TransactionType.INCOME,
            amount=Decimal("2500.00"),
            category="salary",
            description="April paycheck",
            date=datetime.date(2026, 4, 15),
        )
        assert txn.type == TransactionType.INCOME

    def test_large_amount_preserved_exactly(self) -> None:
        """Boundary case: very large Decimal amounts retain full precision (F3 large-value adverse condition)."""
        txn = Transaction(
            id=uuid4(),
            type=TransactionType.EXPENSE,
            amount=Decimal("999999999999.99"),
            category="other",
            description="Large transaction",
            date=datetime.date(2026, 1, 1),
        )
        assert txn.amount == Decimal("999999999999.99")

    def test_small_amount_preserved_exactly(self) -> None:
        """Boundary case: very small Decimal amounts (single cent) retain full precision."""
        txn = Transaction(
            id=uuid4(),
            type=TransactionType.EXPENSE,
            amount=Decimal("0.01"),
            category="other",
            description="Penny",
            date=datetime.date(2026, 1, 1),
        )
        assert txn.amount == Decimal("0.01")


class TestTransactionEquality:
    def _make(self, txn_id: UUID, **overrides: object) -> Transaction:
        defaults = dict(
            id=txn_id,
            type=TransactionType.EXPENSE,
            amount=Decimal("10.00"),
            category="food",
            description="Lunch",
            date=datetime.date(2026, 4, 27),
        )
        defaults.update(overrides)
        return Transaction(**defaults)  # type: ignore[arg-type]

    def test_equal_when_ids_match(self) -> None:
        """Equality is identity-based: two transactions with the same id are equal even if other fields differ."""
        txn_id = uuid4()
        a = self._make(txn_id)
        b = self._make(txn_id, description="Different description")
        assert a == b

    def test_not_equal_when_ids_differ(self) -> None:
        """Two transactions with different ids are never equal, even if all other fields match."""
        a = self._make(uuid4())
        b = self._make(uuid4())
        assert a != b

    def test_not_equal_to_non_transaction(self) -> None:
        """Equality returns False (not error) when compared to unrelated types."""
        txn = self._make(uuid4())
        assert txn != "not a transaction"
        assert txn != 42
        assert txn != None  # noqa: E711

    def test_hash_matches_id_hash(self) -> None:
        """Hash is derived from id alone, consistent with __eq__."""
        txn_id = uuid4()
        txn = self._make(txn_id)
        assert hash(txn) == hash(txn_id)

    def test_usable_in_set(self) -> None:
        """Transactions with the same id deduplicate in a set, regardless of other fields."""
        txn_id = uuid4()
        a = self._make(txn_id)
        b = self._make(txn_id, description="Other")
        unique = {a, b}
        assert len(unique) == 1


class TestTransactionRepr:
    def test_repr_includes_all_fields(self) -> None:
        """repr() output contains every field for debugging and test assertion clarity."""
        txn_id = uuid4()
        txn = Transaction(
            id=txn_id,
            type=TransactionType.EXPENSE,
            amount=Decimal("42.50"),
            category="food",
            description="Groceries",
            date=datetime.date(2026, 4, 27),
        )
        result = repr(txn)
        assert str(txn_id) in result
        assert "EXPENSE" in result
        assert "42.50" in result
        assert "food" in result
        assert "Groceries" in result
        assert "2026" in result
