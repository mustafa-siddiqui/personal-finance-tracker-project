"""BalanceCalculator — computes current balance from transactions (F3)."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from src.domain.exceptions import ValidationError
from src.domain.transaction import Transaction, TransactionType


class BalanceCalculator:
    """Calculate account balance from income and expense transactions."""

    @staticmethod
    def calculate(transactions: Iterable[Transaction]) -> Decimal:
        """
        Calculate current balance as total income minus total expenses.

        Returns Decimal("0") for an empty transaction collection.

        Raises:
            ValidationError: If transactions is None or contains invalid entries.
        """
        if transactions is None:
            raise ValidationError(field="transactions", message="must not be None")

        balance = Decimal("0")

        for txn in transactions:
            BalanceCalculator._validate_transaction(txn)

            if txn.type == TransactionType.INCOME:
                balance += txn.amount
            elif txn.type == TransactionType.EXPENSE:
                balance -= txn.amount
            else:
                raise ValidationError(
                    field="type",
                    message="must be TransactionType.INCOME or TransactionType.EXPENSE",
                )

        return balance

    @staticmethod
    def _validate_transaction(txn: Transaction) -> None:
        """Defensively validate transaction objects before calculation."""
        if not isinstance(txn, Transaction):
            raise ValidationError(
                field="transactions",
                message="all items must be Transaction instances",
            )

        if not isinstance(txn.amount, Decimal):
            raise ValidationError(field="amount", message="must be a Decimal")

        if not txn.amount.is_finite():
            raise ValidationError(field="amount", message="must be a finite number")

        if txn.amount <= 0:
            raise ValidationError(field="amount", message="must be greater than zero")

        if not isinstance(txn.type, TransactionType):
            raise ValidationError(field="type", message="must be a TransactionType")
