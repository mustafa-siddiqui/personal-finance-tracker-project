"""Ledger — records, retrieves, lists, and deletes transactions (F1, F2, F4)."""

from __future__ import annotations

from typing import List
from uuid import UUID, uuid4

from src.domain.exceptions import ValidationError
from src.domain.transaction import Transaction
from src.domain.validator import Validator
from src.repository.transaction_repository_interface import (
    TransactionRepositoryInterface,
)


class Ledger:
    def __init__(
        self,
        repo: TransactionRepositoryInterface,
        validator: Validator,
    ) -> None:
        self._repo = repo
        self._validator = validator

    def record(
        self,
        type: str,
        amount: str,
        category: str,
        description: str,
        date: str,
    ) -> Transaction:
        """Validate raw inputs, build a Transaction, save it, and return it."""
        validated_type = self._validator.validate_type(type)
        validated_amount = self._validator.validate_amount(amount)
        validated_category = self._validator.validate_category(category)
        validated_description = self._validator.validate_description(description)
        validated_date = self._validator.validate_date(date)

        txn = Transaction(
            id=uuid4(),
            type=validated_type,
            amount=validated_amount,
            category=validated_category,
            description=validated_description,
            date=validated_date,
        )

        self._repo.add(txn)
        self._repo.save()
        return txn

    def list_all(self) -> List[Transaction]:
        """Return all transactions from the repository."""
        return self._repo.list_all()

    def get(self, txn_id: UUID) -> Transaction:
        """Retrieve a single transaction by UUID."""
        if not isinstance(txn_id, UUID):
            raise ValidationError(field="id", message="must be a UUID")

        return self._repo.get(txn_id)

    def delete(self, txn_id: UUID) -> None:
        """Delete a transaction by UUID and save the repository."""
        if not isinstance(txn_id, UUID):
            raise ValidationError(field="id", message="must be a UUID")

        self._repo.delete(txn_id)
        self._repo.save()
