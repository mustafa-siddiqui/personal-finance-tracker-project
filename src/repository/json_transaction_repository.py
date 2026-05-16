"""JsonTransactionRepository — JSON file-backed implementation of TransactionRepositoryInterface."""

from __future__ import annotations

import datetime
import json
import os
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List
from uuid import UUID

from src.domain.exceptions import (
    PersistenceError,
    TransactionNotFound,
    UnsupportedSchemaVersion,
)
from src.domain.transaction import Transaction, TransactionType
from src.repository.transaction_repository_interface import (
    TransactionRepositoryInterface,
)

SCHEMA_VERSION = 1


class JsonTransactionRepository(TransactionRepositoryInterface):
    def __init__(self, path: Path) -> None:
        self._path = path
        self._transactions: Dict[UUID, Transaction] = {}

    def add(self, txn: Transaction) -> None:
        self._transactions[txn.id] = txn

    def get(self, txn_id: UUID) -> Transaction:
        if txn_id not in self._transactions:
            raise TransactionNotFound(transaction_id=txn_id)
        return self._transactions[txn_id]

    def list_all(self) -> List[Transaction]:
        return list(self._transactions.values())

    def delete(self, txn_id: UUID) -> None:
        if txn_id not in self._transactions:
            raise TransactionNotFound(transaction_id=txn_id)
        del self._transactions[txn_id]

    def load(self) -> None:
        if not self._path.exists():
            self._transactions = {}
            return

        try:
            raw = self._path.read_text(encoding="utf-8")
        except OSError as e:
            raise PersistenceError(message=f"Failed to read {self._path}: {e}") from e

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise PersistenceError(message=f"Malformed JSON in {self._path}: {e}") from e

        if not isinstance(data, dict):
            raise PersistenceError(message="Top-level JSON value must be an object")

        version = data.get("schema_version")
        if version != SCHEMA_VERSION:
            raise UnsupportedSchemaVersion(
                found_version=version if isinstance(version, int) else -1,
                expected_version=SCHEMA_VERSION,
            )

        txn_dicts = data.get("transactions")
        if not isinstance(txn_dicts, list):
            raise PersistenceError(message="'transactions' must be a list")

        loaded: Dict[UUID, Transaction] = {}
        for entry in txn_dicts:
            txn = self._deserialize_transaction(entry)
            loaded[txn.id] = txn
        self._transactions = loaded

    def save(self) -> None:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "transactions": [self._serialize_transaction(t) for t in self._transactions.values()],
        }
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        try:
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            os.replace(tmp_path, self._path)
        except OSError as e:
            raise PersistenceError(message=f"Failed to write {self._path}: {e}") from e

    @staticmethod
    def _serialize_transaction(txn: Transaction) -> Dict[str, Any]:
        return {
            "id": str(txn.id),
            "type": txn.type.value,
            "amount": str(txn.amount),
            "category": txn.category,
            "description": txn.description,
            "date": txn.date.isoformat(),
        }

    @staticmethod
    def _deserialize_transaction(entry: Any) -> Transaction:
        if not isinstance(entry, dict):
            raise PersistenceError(message="Transaction entry must be an object")
        try:
            return Transaction(
                id=UUID(entry["id"]),
                type=TransactionType(entry["type"]),
                amount=Decimal(entry["amount"]),
                category=entry["category"],
                description=entry["description"],
                date=datetime.date.fromisoformat(entry["date"]),
            )
        except (KeyError, ValueError, TypeError) as e:
            raise PersistenceError(message=f"Invalid transaction entry: {e}") from e
