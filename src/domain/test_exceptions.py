"""Unit tests for the custom exception hierarchy."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.domain.exceptions import (
    FinanceTrackerError,
    PersistenceError,
    TransactionNotFound,
    UnsupportedSchemaVersion,
    ValidationError,
)


class TestFinanceTrackerError:
    def test_is_an_exception(self) -> None:
        """The base class is a real Exception so it can be raised and caught."""
        assert issubclass(FinanceTrackerError, Exception)


class TestValidationError:
    def test_subclass_of_base(self) -> None:
        """ValidationError is part of the FinanceTrackerError hierarchy."""
        assert issubclass(ValidationError, FinanceTrackerError)

    def test_stores_field_and_message(self) -> None:
        """Field and message context are preserved as attributes for test assertions."""
        err = ValidationError(field="amount", message="must be positive")
        assert err.field == "amount"
        assert err.message == "must be positive"

    def test_str_includes_field_and_message(self) -> None:
        """str(err) surfaces both the field name and the failure reason for debugging."""
        err = ValidationError(field="amount", message="must be positive")
        text = str(err)
        assert "amount" in text
        assert "must be positive" in text

    def test_can_be_raised_and_caught_as_base(self) -> None:
        """ValidationError can be caught via the FinanceTrackerError base class."""
        with pytest.raises(FinanceTrackerError):
            raise ValidationError(field="x", message="bad")


class TestTransactionNotFound:
    def test_subclass_of_base(self) -> None:
        """TransactionNotFound is part of the FinanceTrackerError hierarchy."""
        assert issubclass(TransactionNotFound, FinanceTrackerError)

    def test_stores_transaction_id(self) -> None:
        """The missing transaction's UUID is preserved as an attribute."""
        txn_id = uuid4()
        err = TransactionNotFound(transaction_id=txn_id)
        assert err.transaction_id == txn_id

    def test_str_includes_id(self) -> None:
        """str(err) surfaces the missing UUID for debugging."""
        txn_id = uuid4()
        err = TransactionNotFound(transaction_id=txn_id)
        assert str(txn_id) in str(err)


class TestPersistenceError:
    def test_subclass_of_base(self) -> None:
        """PersistenceError is part of the FinanceTrackerError hierarchy."""
        assert issubclass(PersistenceError, FinanceTrackerError)

    def test_stores_message(self) -> None:
        """The failure description is preserved as an attribute."""
        err = PersistenceError(message="disk full")
        assert err.message == "disk full"

    def test_str_includes_message(self) -> None:
        """str(err) surfaces the failure description."""
        err = PersistenceError(message="disk full")
        assert "disk full" in str(err)


class TestUnsupportedSchemaVersion:
    def test_subclass_of_base(self) -> None:
        """UnsupportedSchemaVersion is part of the FinanceTrackerError hierarchy."""
        assert issubclass(UnsupportedSchemaVersion, FinanceTrackerError)

    def test_not_subclass_of_persistence_error(self) -> None:
        """Per design decision: UnsupportedSchemaVersion is intentionally NOT a PersistenceError subclass."""
        assert not issubclass(UnsupportedSchemaVersion, PersistenceError)

    def test_stores_versions(self) -> None:
        """Both found and expected versions are preserved as attributes."""
        err = UnsupportedSchemaVersion(found_version=2, expected_version=1)
        assert err.found_version == 2
        assert err.expected_version == 1

    def test_str_includes_versions(self) -> None:
        """str(err) surfaces both version numbers for debugging."""
        err = UnsupportedSchemaVersion(found_version=2, expected_version=1)
        text = str(err)
        assert "2" in text
        assert "1" in text


class TestExceptionHierarchy:
    def test_all_exceptions_share_common_base(self) -> None:
        """A single except clause can catch every custom exception."""
        exceptions = [
            ValidationError(field="x", message="bad"),
            TransactionNotFound(transaction_id=uuid4()),
            PersistenceError(message="disk full"),
            UnsupportedSchemaVersion(found_version=2, expected_version=1),
        ]
        for exc in exceptions:
            try:
                raise exc
            except FinanceTrackerError:
                pass  # expected
            except Exception:
                pytest.fail(f"{type(exc).__name__} was not caught by FinanceTrackerError")
