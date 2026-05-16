# Unit Test Report — Unit 3: JsonTransactionRepository

## Functional Requirement

**F5 — Persist transactions to / load transactions from local JSON storage.** This unit is the only component in the system that touches the filesystem and serializes/deserializes the JSON envelope.

## Unit

| File | Description |
|------|-------------|
| `src/repository/json_transaction_repository.py` | JSON file-backed implementation of `TransactionRepositoryInterface` |
| `src/repository/test_json_transaction_repository.py` | Unit tests |

## Date

2026-05-16

## Engineers

Mustafa Siddiqui

## Test Methodology

**Approach:** Specification-based black-box testing combined with adverse-condition testing of error paths. A real temporary filesystem (via `pytest`'s `tmp_path` fixture) is used in place of mocks so that the full serialize → write → read → deserialize round trip is exercised end-to-end within the unit's boundary.

**Why this methodology:**

- The repository's contract is defined by `TransactionRepositoryInterface`. Black-box testing exercises that contract directly without coupling tests to the JSON envelope's internal structure.
- Mocking the filesystem here would defeat the purpose: this unit's job *is* file I/O. Using `tmp_path` keeps the tests fast (filesystem in tmpfs on most systems) while exercising the real code path.
- Adverse conditions called out by the design doc — malformed JSON, unsupported schema versions, atomic-write failure — are explicitly tested. Each adverse case must raise the exact exception type the design doc specifies, otherwise a future caller's `try/except` block could silently swallow the wrong error.
- Boundary-value analysis is applied to the `Decimal` amount round trip (largest value `999999999999.99`, smallest non-zero `0.01`) to verify that the design's promise — string-serialized amounts preserving full precision — actually holds when data passes through the file.
- Equivalence partitioning is applied to the load path: missing file vs. valid file vs. malformed JSON vs. wrong schema version vs. wrong shape — each is its own equivalence class with its own expected outcome.

**Test case completeness:**

- Each public method (`add`, `get`, `list_all`, `delete`, `load`, `save`) has tests covering its happy path and any error paths the design doc specifies.
- The in-memory mutation contract (D6) — `add()`/`delete()` do not write to disk, `save()` is explicit — is verified for both `add` and `delete`.
- The atomic write contract (D7) is verified by simulating a rename failure mid-save and asserting the previous file is preserved.
- The schema versioning contract (D8) is verified for the version-mismatch path and the missing-version path.

## Automated Test Code

Test file: `src/repository/test_json_transaction_repository.py`. Tests use the `pytest` `tmp_path` fixture for isolated filesystem state.

### Test cases — `add`, `get`, `list_all`, `delete`

| # | Test | Inputs | Expected Output |
|---|------|--------|-----------------|
| 1 | `TestAdd.test_add_stores_transaction` | A new `Transaction` | Retrievable via `get(txn.id)` |
| 2 | `TestAdd.test_add_does_not_write_to_disk` | `add()` only (no `save()`) | The repo file does not exist on disk |
| 3 | `TestAdd.test_add_replaces_transaction_with_same_id` | Two transactions sharing one UUID | `get()` returns the second (last-write-wins) |
| 4 | `TestGet.test_get_returns_added_transaction` | An added `Transaction` | `get()` returns equal `Transaction` |
| 5 | `TestGet.test_get_missing_id_raises_transaction_not_found` | Unknown UUID | `TransactionNotFound` raised with that UUID |
| 6 | `TestGet.test_get_after_delete_raises` | Add then delete a `Transaction` | `get()` raises `TransactionNotFound` |
| 7 | `TestListAll.test_empty_repo_returns_empty_list` | Fresh repo | `[]` |
| 8 | `TestListAll.test_list_all_returns_all_added` | 3 added transactions | All 3 returned (set equality) |
| 9 | `TestListAll.test_list_all_excludes_deleted` | 2 added, 1 deleted | Only the surviving transaction returned |
| 10 | `TestDelete.test_delete_removes_transaction` | Add then delete | `list_all()` is empty |
| 11 | `TestDelete.test_delete_missing_id_raises_transaction_not_found` | Unknown UUID | `TransactionNotFound` raised with that UUID |
| 12 | `TestDelete.test_delete_does_not_write_to_disk` | Save 1 txn, delete it (no second save) | On-disk file still contains the txn |

### Test cases — `save`, `load`, atomic writes

| # | Test | Inputs | Expected Output |
|---|------|--------|-----------------|
| 13 | `TestSave.test_save_creates_file` | `save()` on empty repo | Target file exists |
| 14 | `TestSave.test_save_writes_schema_version` | `save()` on empty repo | `schema_version == 1` in file |
| 15 | `TestSave.test_save_empty_repo_writes_empty_list` | `save()` on empty repo | `transactions == []` (present, empty) |
| 16 | `TestSave.test_save_serializes_all_fields` | `save()` after adding fully-populated txn | All 6 fields appear in JSON with expected values and types |
| 17 | `TestSave.test_save_amount_is_serialized_as_string` | Amount `Decimal('0.10')` | JSON value for `amount` is a string, not a number |
| 18 | `TestSave.test_save_overwrites_previous_file` | save → delete → save | File contains empty transactions list (replace, not append) |
| 19 | `TestSave.test_save_creates_parent_directory` | Path inside non-existent nested dirs | Intermediate dirs created, file written |
| 20 | `TestLoad.test_load_missing_file_yields_empty_store` | `load()` on non-existent path | `list_all() == []`, no exception |
| 21 | `TestLoad.test_load_round_trip_preserves_transaction` | Save txn with `amount = "999999999999.99"`, then load via fresh instance | Loaded txn equals original; `amount` is exact `Decimal` |
| 22 | `TestLoad.test_load_round_trip_preserves_small_amount` | Save txn with `amount = "0.01"`, load | Loaded `amount == Decimal('0.01')` |
| 23 | `TestLoad.test_load_round_trip_with_multiple_transactions` | Save 5 txns, load via fresh instance | All 5 recovered (set equality) |
| 24 | `TestLoad.test_load_malformed_json_raises_persistence_error` | File contains `"{ this is not valid json"` | `PersistenceError` raised |
| 25 | `TestLoad.test_load_non_object_top_level_raises_persistence_error` | File contains `[]` | `PersistenceError` raised |
| 26 | `TestLoad.test_load_unsupported_schema_version_raises` | File has `schema_version: 99` | `UnsupportedSchemaVersion(found=99, expected=1)` raised |
| 27 | `TestLoad.test_load_missing_schema_version_raises_unsupported` | File has no `schema_version` field | `UnsupportedSchemaVersion` raised |
| 28 | `TestLoad.test_load_transactions_not_a_list_raises_persistence_error` | File has `"transactions": {}` | `PersistenceError` raised |
| 29 | `TestLoad.test_load_invalid_transaction_entry_raises_persistence_error` | Transaction entry missing required fields | `PersistenceError` raised |
| 30 | `TestAtomicWrite.test_save_does_not_leave_tmp_file` | Successful `save()` | No `.tmp` files remain in target directory |
| 31 | `TestAtomicWrite.test_save_preserves_previous_file_if_write_fails` | Save once, then save again with `os.replace` monkeypatched to fail | Original file bytes unchanged after failed second save |

The full source of each test is in `src/repository/test_json_transaction_repository.py`.

## Actual Outputs

All 31 test cases pass. Output of `pytest src/repository/test_json_transaction_repository.py -v`:

```
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-8.3.5, pluggy-1.5.0
cachedir: .pytest_cache
rootdir: /home/masiddiqui/personal/personal-finance-tracker-project
configfile: pytest.ini
plugins: mock-3.14.1
collected 31 items

src/repository/test_json_transaction_repository.py::TestAdd::test_add_stores_transaction PASSED                                  [  3%]
src/repository/test_json_transaction_repository.py::TestAdd::test_add_does_not_write_to_disk PASSED                              [  6%]
src/repository/test_json_transaction_repository.py::TestAdd::test_add_replaces_transaction_with_same_id PASSED                   [  9%]
src/repository/test_json_transaction_repository.py::TestGet::test_get_returns_added_transaction PASSED                           [ 12%]
src/repository/test_json_transaction_repository.py::TestGet::test_get_missing_id_raises_transaction_not_found PASSED             [ 16%]
src/repository/test_json_transaction_repository.py::TestGet::test_get_after_delete_raises PASSED                                 [ 19%]
src/repository/test_json_transaction_repository.py::TestListAll::test_empty_repo_returns_empty_list PASSED                       [ 22%]
src/repository/test_json_transaction_repository.py::TestListAll::test_list_all_returns_all_added PASSED                          [ 25%]
src/repository/test_json_transaction_repository.py::TestListAll::test_list_all_excludes_deleted PASSED                           [ 29%]
src/repository/test_json_transaction_repository.py::TestDelete::test_delete_removes_transaction PASSED                           [ 32%]
src/repository/test_json_transaction_repository.py::TestDelete::test_delete_missing_id_raises_transaction_not_found PASSED       [ 35%]
src/repository/test_json_transaction_repository.py::TestDelete::test_delete_does_not_write_to_disk PASSED                        [ 38%]
src/repository/test_json_transaction_repository.py::TestSave::test_save_creates_file PASSED                                      [ 41%]
src/repository/test_json_transaction_repository.py::TestSave::test_save_writes_schema_version PASSED                             [ 45%]
src/repository/test_json_transaction_repository.py::TestSave::test_save_empty_repo_writes_empty_list PASSED                      [ 48%]
src/repository/test_json_transaction_repository.py::TestSave::test_save_serializes_all_fields PASSED                             [ 51%]
src/repository/test_json_transaction_repository.py::TestSave::test_save_amount_is_serialized_as_string PASSED                    [ 54%]
src/repository/test_json_transaction_repository.py::TestSave::test_save_overwrites_previous_file PASSED                          [ 58%]
src/repository/test_json_transaction_repository.py::TestSave::test_save_creates_parent_directory PASSED                          [ 61%]
src/repository/test_json_transaction_repository.py::TestLoad::test_load_missing_file_yields_empty_store PASSED                   [ 64%]
src/repository/test_json_transaction_repository.py::TestLoad::test_load_round_trip_preserves_transaction PASSED                  [ 67%]
src/repository/test_json_transaction_repository.py::TestLoad::test_load_round_trip_preserves_small_amount PASSED                 [ 70%]
src/repository/test_json_transaction_repository.py::TestLoad::test_load_round_trip_with_multiple_transactions PASSED             [ 74%]
src/repository/test_json_transaction_repository.py::TestLoad::test_load_malformed_json_raises_persistence_error PASSED           [ 77%]
src/repository/test_json_transaction_repository.py::TestLoad::test_load_non_object_top_level_raises_persistence_error PASSED     [ 80%]
src/repository/test_json_transaction_repository.py::TestLoad::test_load_unsupported_schema_version_raises PASSED                 [ 83%]
src/repository/test_json_transaction_repository.py::TestLoad::test_load_missing_schema_version_raises_unsupported PASSED         [ 87%]
src/repository/test_json_transaction_repository.py::TestLoad::test_load_transactions_not_a_list_raises_persistence_error PASSED  [ 90%]
src/repository/test_json_transaction_repository.py::TestLoad::test_load_invalid_transaction_entry_raises_persistence_error PASSED [ 93%]
src/repository/test_json_transaction_repository.py::TestAtomicWrite::test_save_does_not_leave_tmp_file PASSED                    [ 96%]
src/repository/test_json_transaction_repository.py::TestAtomicWrite::test_save_preserves_previous_file_if_write_fails PASSED     [100%]

============================== 31 passed in 0.07s ==============================
```

**Result: 31 passed, 0 failed.**
