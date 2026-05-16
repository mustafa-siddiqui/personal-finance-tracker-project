"""Ledger — records, retrieves, and deletes transactions (F1, F2, F4).

This file currently implements F1 (record). F2 (list_all/get) and F4 (delete) will be added later.
"""

from __future__ import annotations

from typing import List
from uuid import UUID, uuid4

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
        """Validate raw string inputs, build a Transaction with a fresh UUID,
        persist it via the repository, and return it.

        Raises:
            ValidationError: If any field fails validation.
        """
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

    # F2 / F4 — signatures left for the team to implement
    def list_all(self) -> List[Transaction]:
        raise NotImplementedError

    def get(self, txn_id: UUID) -> Transaction:
        raise NotImplementedError

    def delete(self, txn_id: UUID) -> None:
        raise NotImplementedError
