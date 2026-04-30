"""TransactionRepositoryInterface — abstract base class for transaction storage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from src.domain.transaction import Transaction


class TransactionRepositoryInterface(ABC):
    """Defines the persistence contract for transaction storage.

    add() and delete() mutate in-memory state only.
    save() must be called explicitly to persist changes to disk.
    load() must be called on startup to hydrate from the backing store.
    """

    @abstractmethod
    def add(self, txn: Transaction) -> None:
        """Add a transaction to the store."""

    @abstractmethod
    def get(self, txn_id: UUID) -> Transaction:
        """Retrieve a transaction by ID.

        Raises:
            TransactionNotFound: If no transaction with the given ID exists.
        """

    @abstractmethod
    def list_all(self) -> List[Transaction]:
        """Return all transactions in the store."""

    @abstractmethod
    def delete(self, txn_id: UUID) -> None:
        """Remove a transaction by ID.

        Raises:
            TransactionNotFound: If no transaction with the given ID exists.
        """

    @abstractmethod
    def load(self) -> None:
        """Load transactions from the backing store into memory."""

    @abstractmethod
    def save(self) -> None:
        """Persist in-memory transactions to the backing store."""
