"""Unit tests for JsonTransactionRepository."""

from __future__ import annotations

import datetime
import json
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

import pytest

from src.domain.exceptions import (
    PersistenceError,
    TransactionNotFound,
    UnsupportedSchemaVersion,
)
from src.domain.transaction import Transaction, TransactionType
from src.repository.json_transaction_repository import (
    SCHEMA_VERSION,
    JsonTransactionRepository,
)


def _make_txn(
    txn_id: Optional[UUID] = None,
    type: TransactionType = TransactionType.EXPENSE,
    amount: str = "42.50",
    category: str = "food",
    description: str = "Groceries",
    date: datetime.date = datetime.date(2026, 4, 27),
) -> Transaction:
    return Transaction(
        id=txn_id or uuid4(),
        type=type,
        amount=Decimal(amount),
        category=category,
        description=description,
        date=date,
    )


@pytest.fixture
def repo_path(tmp_path: Path) -> Path:
    """Path to a transactions.json file inside a fresh temp dir."""
    return tmp_path / "transactions.json"


@pytest.fixture
def repo(repo_path: Path) -> JsonTransactionRepository:
    """An empty JsonTransactionRepository pointed at a fresh temp file."""
    return JsonTransactionRepository(path=repo_path)


class TestAdd:
    def test_add_stores_transaction(self, repo: JsonTransactionRepository) -> None:
        """add() makes a transaction retrievable via get()."""
        txn = _make_txn()
        repo.add(txn)
        assert repo.get(txn.id) == txn

    def test_add_does_not_write_to_disk(
        self, repo: JsonTransactionRepository, repo_path: Path
    ) -> None:
        """add() mutates in-memory state only; disk is unchanged until save() is called."""
        repo.add(_make_txn())
        assert not repo_path.exists()

    def test_add_replaces_transaction_with_same_id(
        self, repo: JsonTransactionRepository
    ) -> None:
        """Adding a transaction with an existing id overwrites the previous one (last-write-wins)."""
        txn_id = uuid4()
        first = _make_txn(txn_id=txn_id, description="first")
        second = _make_txn(txn_id=txn_id, description="second")
        repo.add(first)
        repo.add(second)
        assert repo.get(txn_id).description == "second"


class TestGet:
    def test_get_returns_added_transaction(
        self, repo: JsonTransactionRepository
    ) -> None:
        """get() returns the same Transaction object that was added."""
        txn = _make_txn()
        repo.add(txn)
        assert repo.get(txn.id) == txn

    def test_get_missing_id_raises_transaction_not_found(
        self, repo: JsonTransactionRepository
    ) -> None:
        """get() with an unknown UUID raises TransactionNotFound carrying that UUID."""
        unknown_id = uuid4()
        with pytest.raises(TransactionNotFound) as exc_info:
            repo.get(unknown_id)
        assert exc_info.value.transaction_id == unknown_id

    def test_get_after_delete_raises(self, repo: JsonTransactionRepository) -> None:
        """A previously-added transaction is unretrievable after delete()."""
        txn = _make_txn()
        repo.add(txn)
        repo.delete(txn.id)
        with pytest.raises(TransactionNotFound):
            repo.get(txn.id)


class TestListAll:
    def test_empty_repo_returns_empty_list(
        self, repo: JsonTransactionRepository
    ) -> None:
        """A freshly-constructed repo has no transactions to list."""
        assert repo.list_all() == []

    def test_list_all_returns_all_added(self, repo: JsonTransactionRepository) -> None:
        """list_all() returns every added transaction (order not guaranteed)."""
        txns = [_make_txn() for _ in range(3)]
        for t in txns:
            repo.add(t)
        result = repo.list_all()
        assert len(result) == 3
        assert set(result) == set(txns)

    def test_list_all_excludes_deleted(self, repo: JsonTransactionRepository) -> None:
        """Deleted transactions do not appear in list_all()."""
        a = _make_txn()
        b = _make_txn()
        repo.add(a)
        repo.add(b)
        repo.delete(a.id)
        assert repo.list_all() == [b]


class TestDelete:
    def test_delete_removes_transaction(self, repo: JsonTransactionRepository) -> None:
        """delete() removes the transaction from the in-memory store."""
        txn = _make_txn()
        repo.add(txn)
        repo.delete(txn.id)
        assert repo.list_all() == []

    def test_delete_missing_id_raises_transaction_not_found(
        self, repo: JsonTransactionRepository
    ) -> None:
        """delete() with an unknown UUID raises TransactionNotFound carrying that UUID."""
        unknown_id = uuid4()
        with pytest.raises(TransactionNotFound) as exc_info:
            repo.delete(unknown_id)
        assert exc_info.value.transaction_id == unknown_id

    def test_delete_does_not_write_to_disk(
        self, repo: JsonTransactionRepository, repo_path: Path
    ) -> None:
        """delete() mutates in-memory state only; disk is unchanged until save()."""
        txn = _make_txn()
        repo.add(txn)
        repo.save()
        repo.delete(txn.id)
        on_disk = json.loads(repo_path.read_text())
        assert len(on_disk["transactions"]) == 1


class TestSave:
    def test_save_creates_file(
        self, repo: JsonTransactionRepository, repo_path: Path
    ) -> None:
        """save() creates the JSON file on disk."""
        repo.save()
        assert repo_path.exists()

    def test_save_writes_schema_version(
        self, repo: JsonTransactionRepository, repo_path: Path
    ) -> None:
        """The saved file's schema_version matches the constant defined by the implementation."""
        repo.save()
        data = json.loads(repo_path.read_text())
        assert data["schema_version"] == SCHEMA_VERSION

    def test_save_empty_repo_writes_empty_list(
        self, repo: JsonTransactionRepository, repo_path: Path
    ) -> None:
        """An empty repo serializes to an envelope with an empty transactions list (not absent)."""
        repo.save()
        data = json.loads(repo_path.read_text())
        assert data["transactions"] == []

    def test_save_serializes_all_fields(
        self, repo: JsonTransactionRepository, repo_path: Path
    ) -> None:
        """Every Transaction field is serialized to the JSON envelope."""
        txn_id = UUID("550e8400-e29b-41d4-a716-446655440000")
        txn = Transaction(
            id=txn_id,
            type=TransactionType.EXPENSE,
            amount=Decimal("42.50"),
            category="food",
            description="Groceries",
            date=datetime.date(2026, 4, 27),
        )
        repo.add(txn)
        repo.save()
        data = json.loads(repo_path.read_text())
        entry = data["transactions"][0]
        assert entry["id"] == str(txn_id)
        assert entry["type"] == "expense"
        assert entry["amount"] == "42.50"
        assert entry["category"] == "food"
        assert entry["description"] == "Groceries"
        assert entry["date"] == "2026-04-27"

    def test_save_amount_is_serialized_as_string(
        self, repo: JsonTransactionRepository, repo_path: Path
    ) -> None:
        """amount must be a JSON string, never a JSON number (preserves Decimal precision)."""
        repo.add(_make_txn(amount="0.10"))
        repo.save()
        raw = repo_path.read_text()
        data = json.loads(raw)
        assert isinstance(data["transactions"][0]["amount"], str)

    def test_save_overwrites_previous_file(
        self, repo: JsonTransactionRepository, repo_path: Path
    ) -> None:
        """A second save() replaces the prior file contents (not appends)."""
        repo.add(_make_txn())
        repo.save()
        repo.delete(repo.list_all()[0].id)
        repo.save()
        data = json.loads(repo_path.read_text())
        assert data["transactions"] == []

    def test_save_creates_parent_directory(self, tmp_path: Path) -> None:
        """save() creates intermediate directories so the caller doesn't have to."""
        nested_path = tmp_path / "nested" / "dir" / "transactions.json"
        repo = JsonTransactionRepository(path=nested_path)
        repo.save()
        assert nested_path.exists()


class TestLoad:
    def test_load_missing_file_yields_empty_store(
        self, repo: JsonTransactionRepository
    ) -> None:
        """load() against a non-existent file leaves the repo empty (not an error)."""
        repo.load()
        assert repo.list_all() == []

    def test_load_round_trip_preserves_transaction(self, repo_path: Path) -> None:
        """A transaction saved by one repo instance is recovered identically by a fresh load()."""
        txn = _make_txn(
            txn_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            amount="999999999999.99",  # boundary: large value preserved through round-trip
        )
        writer = JsonTransactionRepository(path=repo_path)
        writer.add(txn)
        writer.save()

        reader = JsonTransactionRepository(path=repo_path)
        reader.load()
        assert reader.get(txn.id).amount == Decimal("999999999999.99")
        assert reader.get(txn.id) == txn

    def test_load_round_trip_preserves_small_amount(self, repo_path: Path) -> None:
        """Boundary case: a Decimal('0.01') survives serialize → write → read → deserialize."""
        txn = _make_txn(amount="0.01")
        w = JsonTransactionRepository(path=repo_path)
        w.add(txn)
        w.save()
        r = JsonTransactionRepository(path=repo_path)
        r.load()
        assert r.get(txn.id).amount == Decimal("0.01")

    def test_load_round_trip_with_multiple_transactions(self, repo_path: Path) -> None:
        """Multiple transactions all survive a save/load cycle."""
        txns = [_make_txn() for _ in range(5)]
        w = JsonTransactionRepository(path=repo_path)
        for t in txns:
            w.add(t)
        w.save()
        r = JsonTransactionRepository(path=repo_path)
        r.load()
        assert set(r.list_all()) == set(txns)

    def test_load_malformed_json_raises_persistence_error(
        self, repo_path: Path
    ) -> None:
        """A file containing invalid JSON raises PersistenceError, not a parse exception."""
        repo_path.write_text("{ this is not valid json")
        repo = JsonTransactionRepository(path=repo_path)
        with pytest.raises(PersistenceError):
            repo.load()

    def test_load_non_object_top_level_raises_persistence_error(
        self, repo_path: Path
    ) -> None:
        """A file with a JSON array (not an object) at top level is rejected."""
        repo_path.write_text("[]")
        repo = JsonTransactionRepository(path=repo_path)
        with pytest.raises(PersistenceError):
            repo.load()

    def test_load_unsupported_schema_version_raises(self, repo_path: Path) -> None:
        """A file with the wrong schema_version raises UnsupportedSchemaVersion (not PersistenceError)."""
        repo_path.write_text(json.dumps({"schema_version": 99, "transactions": []}))
        repo = JsonTransactionRepository(path=repo_path)
        with pytest.raises(UnsupportedSchemaVersion) as exc_info:
            repo.load()
        assert exc_info.value.found_version == 99
        assert exc_info.value.expected_version == SCHEMA_VERSION

    def test_load_missing_schema_version_raises_unsupported(
        self, repo_path: Path
    ) -> None:
        """A file without schema_version is treated as an unsupported version (not a generic error)."""
        repo_path.write_text(json.dumps({"transactions": []}))
        repo = JsonTransactionRepository(path=repo_path)
        with pytest.raises(UnsupportedSchemaVersion):
            repo.load()

    def test_load_transactions_not_a_list_raises_persistence_error(
        self, repo_path: Path
    ) -> None:
        """If transactions is the wrong shape (e.g. a dict), raise PersistenceError."""
        repo_path.write_text(json.dumps({"schema_version": 1, "transactions": {}}))
        repo = JsonTransactionRepository(path=repo_path)
        with pytest.raises(PersistenceError):
            repo.load()

    def test_load_invalid_transaction_entry_raises_persistence_error(
        self, repo_path: Path
    ) -> None:
        """A malformed transaction record (missing fields) raises PersistenceError."""
        repo_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "transactions": [{"id": "not-a-uuid"}],
                }
            )
        )
        repo = JsonTransactionRepository(path=repo_path)
        with pytest.raises(PersistenceError):
            repo.load()


class TestAtomicWrite:
    def test_save_does_not_leave_tmp_file(
        self, repo: JsonTransactionRepository, repo_path: Path
    ) -> None:
        """After a successful save(), no .tmp artifact remains in the directory."""
        repo.add(_make_txn())
        repo.save()
        siblings = list(repo_path.parent.iterdir())
        assert all(not s.name.endswith(".tmp") for s in siblings)

    def test_save_preserves_previous_file_if_write_fails(
        self, repo_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the atomic rename fails, the original file is left untouched (no data loss)."""
        # First, save a known-good file
        first = JsonTransactionRepository(path=repo_path)
        original_txn = _make_txn(description="ORIGINAL")
        first.add(original_txn)
        first.save()
        original_bytes = repo_path.read_bytes()

        # Now try to save again, but force os.replace to fail
        second = JsonTransactionRepository(path=repo_path)
        second.add(_make_txn(description="NEW"))

        import src.repository.json_transaction_repository as module

        def fail_replace(*args: object, **kwargs: object) -> None:
            raise OSError("simulated rename failure")

        monkeypatch.setattr(module.os, "replace", fail_replace)

        with pytest.raises(PersistenceError):
            second.save()

        # Original file is unchanged
        assert repo_path.read_bytes() == original_bytes
