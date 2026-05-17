"""Unit tests for Ledger."""

from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from src.application.ledger import Ledger
from src.domain.exceptions import ValidationError
from src.domain.transaction import Transaction, TransactionType
from src.domain.validator import Validator
from src.repository.transaction_repository_interface import (
    TransactionRepositoryInterface,
)


@pytest.fixture
def mock_repo() -> MagicMock:
    """A mock TransactionRepositoryInterface for isolating Ledger from real I/O."""
    return MagicMock(spec=TransactionRepositoryInterface)


@pytest.fixture
def mock_validator() -> MagicMock:
    """A mock Validator with default 'happy path' return values."""
    v = MagicMock(spec=Validator)
    v.validate_type.return_value = TransactionType.EXPENSE
    v.validate_amount.return_value = Decimal("42.50")
    v.validate_category.return_value = "food"
    v.validate_description.return_value = "Groceries"
    v.validate_date.return_value = datetime.date(2026, 4, 27)
    return v


@pytest.fixture
def ledger(mock_repo: MagicMock, mock_validator: MagicMock) -> Ledger:
    return Ledger(repo=mock_repo, validator=mock_validator)


class TestRecordHappyPath:
    def test_record_returns_transaction(self, ledger: Ledger) -> None:
        """record() returns a Transaction object."""
        result = ledger.record(
            type="expense",
            amount="42.50",
            category="food",
            description="Groceries",
            date="2026-04-27",
        )
        assert isinstance(result, Transaction)

    def test_record_populates_validated_fields(self, ledger: Ledger) -> None:
        """The returned Transaction carries the validator's normalized output, not the raw input."""
        result = ledger.record(
            type="expense",
            amount="42.50",
            category="food",
            description="Groceries",
            date="2026-04-27",
        )
        assert result.type == TransactionType.EXPENSE
        assert result.amount == Decimal("42.50")
        assert result.category == "food"
        assert result.description == "Groceries"
        assert result.date == datetime.date(2026, 4, 27)

    def test_record_generates_uuid(self, ledger: Ledger) -> None:
        """record() generates a fresh UUID server-side; the caller doesn't supply one."""
        result = ledger.record(
            type="expense",
            amount="42.50",
            category="food",
            description="Groceries",
            date="2026-04-27",
        )
        assert isinstance(result.id, UUID)

    def test_record_generates_unique_uuids(self, ledger: Ledger) -> None:
        """Two consecutive record() calls produce distinct UUIDs."""
        a = ledger.record(
            type="expense",
            amount="42.50",
            category="food",
            description="Groceries",
            date="2026-04-27",
        )
        b = ledger.record(
            type="expense",
            amount="42.50",
            category="food",
            description="Groceries",
            date="2026-04-27",
        )
        assert a.id != b.id


class TestRecordValidatorInteraction:
    def test_record_calls_each_validator(
        self, ledger: Ledger, mock_validator: MagicMock
    ) -> None:
        """record() invokes every validator method exactly once."""
        ledger.record(
            type="expense",
            amount="42.50",
            category="food",
            description="Groceries",
            date="2026-04-27",
        )
        mock_validator.validate_type.assert_called_once_with("expense")
        mock_validator.validate_amount.assert_called_once_with("42.50")
        mock_validator.validate_category.assert_called_once_with("food")
        mock_validator.validate_description.assert_called_once_with("Groceries")
        mock_validator.validate_date.assert_called_once_with("2026-04-27")

    def test_record_propagates_validation_error_from_amount(
        self, ledger: Ledger, mock_validator: MagicMock
    ) -> None:
        """A ValidationError raised by the validator surfaces unchanged from record()."""
        mock_validator.validate_amount.side_effect = ValidationError(
            field="amount", message="must be positive"
        )
        with pytest.raises(ValidationError) as exc_info:
            ledger.record(
                type="expense",
                amount="-10",
                category="food",
                description="Groceries",
                date="2026-04-27",
            )
        assert exc_info.value.field == "amount"

    def test_record_propagates_validation_error_from_type(
        self, ledger: Ledger, mock_validator: MagicMock
    ) -> None:
        """A ValidationError on the type field also propagates."""
        mock_validator.validate_type.side_effect = ValidationError(
            field="type", message="invalid"
        )
        with pytest.raises(ValidationError) as exc_info:
            ledger.record(
                type="bogus",
                amount="42.50",
                category="food",
                description="Groceries",
                date="2026-04-27",
            )
        assert exc_info.value.field == "type"

    def test_record_does_not_persist_on_validation_failure(
        self, ledger: Ledger, mock_validator: MagicMock, mock_repo: MagicMock
    ) -> None:
        """If validation fails, repo.add() and repo.save() are never called (no partial writes)."""
        mock_validator.validate_amount.side_effect = ValidationError(
            field="amount", message="must be positive"
        )
        with pytest.raises(ValidationError):
            ledger.record(
                type="expense",
                amount="-10",
                category="food",
                description="Groceries",
                date="2026-04-27",
            )
        mock_repo.add.assert_not_called()
        mock_repo.save.assert_not_called()


class TestRecordRepositoryInteraction:
    def test_record_calls_add_then_save(
        self, ledger: Ledger, mock_repo: MagicMock
    ) -> None:
        """add() is called before save() (order matters: nothing persists without add() first)."""
        ledger.record(
            type="expense",
            amount="42.50",
            category="food",
            description="Groceries",
            date="2026-04-27",
        )
        # Verify both were called and in the correct order
        assert mock_repo.method_calls[0][0] == "add"
        assert mock_repo.method_calls[1][0] == "save"

    def test_record_passes_built_transaction_to_add(
        self, ledger: Ledger, mock_repo: MagicMock
    ) -> None:
        """The Transaction passed to add() is the same one returned by record()."""
        result = ledger.record(
            type="expense",
            amount="42.50",
            category="food",
            description="Groceries",
            date="2026-04-27",
        )
        added_txn = mock_repo.add.call_args[0][0]
        assert added_txn is result

    def test_record_calls_save_exactly_once(
        self, ledger: Ledger, mock_repo: MagicMock
    ) -> None:
        """save() is called exactly once per record() (no double-saves)."""
        ledger.record(
            type="expense",
            amount="42.50",
            category="food",
            description="Groceries",
            date="2026-04-27",
        )
        mock_repo.save.assert_called_once()


class TestLedgerGet:
    def test_get_returns_transaction_when_found(
        self, ledger: Ledger, mock_repo: MagicMock
    ) -> None:
        txn_id = UUID("12345678-1234-5678-1234-567812345678")
        expected = Transaction(
            id=txn_id,
            type=TransactionType.EXPENSE,
            amount=Decimal("42.50"),
            category="food",
            description="Groceries",
            date=datetime.date(2026, 4, 27),
        )
        mock_repo.get.return_value = expected

        result = ledger.get(str(txn_id))

        assert result is expected
        mock_repo.get.assert_called_once_with(txn_id)

    def test_get_validates_transaction_id(
        self, ledger: Ledger, mock_validator: MagicMock
    ) -> None:
        txn_id = UUID("12345678-1234-5678-1234-567812345678")

        ledger.get(str(txn_id))

        mock_validator.validate_id.assert_called_once_with(str(txn_id))

    def test_get_propagates_validation_error(
        self, ledger: Ledger, mock_validator: MagicMock, mock_repo: MagicMock
    ) -> None:
        mock_validator.validate_id.side_effect = ValidationError(
            field="id", message="invalid UUID"
        )

        with pytest.raises(ValidationError):
            ledger.get("bad-id")

        mock_repo.get.assert_not_called()


class TestLedgerDelete:
    def test_delete_removes_transaction_and_saves(
        self, ledger: Ledger, mock_repo: MagicMock
    ) -> None:
        txn_id = UUID("12345678-1234-5678-1234-567812345678")
        mock_repo.delete.return_value = True

        result = ledger.delete(str(txn_id))

        assert result is True
        mock_repo.delete.assert_called_once_with(txn_id)
        mock_repo.save.assert_called_once()

    def test_delete_validates_transaction_id(
        self, ledger: Ledger, mock_validator: MagicMock
    ) -> None:
        txn_id = UUID("12345678-1234-5678-1234-567812345678")

        ledger.delete(str(txn_id))

        mock_validator.validate_id.assert_called_once_with(str(txn_id))

    def test_delete_does_not_save_when_transaction_not_found(
        self, ledger: Ledger, mock_repo: MagicMock
    ) -> None:
        txn_id = UUID("12345678-1234-5678-1234-567812345678")
        mock_repo.delete.return_value = False

        result = ledger.delete(str(txn_id))

        assert result is False
        mock_repo.delete.assert_called_once_with(txn_id)
        mock_repo.save.assert_not_called()

    def test_delete_propagates_validation_error(
        self, ledger: Ledger, mock_validator: MagicMock, mock_repo: MagicMock
    ) -> None:
        mock_validator.validate_id.side_effect = ValidationError(
            field="id", message="invalid UUID"
        )

        with pytest.raises(ValidationError):
            ledger.delete("bad-id")

        mock_repo.delete.assert_not_called()
        mock_repo.save.assert_not_called()
