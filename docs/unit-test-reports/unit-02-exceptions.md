# Unit Test Report — Unit 2: Exception Hierarchy

## Functional Requirement

**F1 — Record transactions** and **F5 — Persist** (cross-cutting). The exception hierarchy defines the error contracts raised throughout the system. F1's `Validator`-driven failures and F5's persistence failures both surface through this unit.

## Unit

| File | Description |
|------|-------------|
| `src/domain/exceptions.py` | `FinanceTrackerError` base + `ValidationError`, `TransactionNotFound`, `PersistenceError`, `UnsupportedSchemaVersion` |
| `src/domain/test_exceptions.py` | Unit tests |

## Date

2026-05-16

## Engineers

Mustafa Siddiqui

## Test Methodology

**Approach:** Specification-based black-box testing focused on contract verification.

**Why this methodology:**

- Exception classes have no algorithmic behavior — their contract is entirely structural (inheritance, attribute storage, message formatting). Black-box tests verify each element of that contract directly.
- The design doc (D9) states that "distinct types let tests assert on the *reason* a call failed, not just that it failed." This unit's tests must therefore verify both *that* each exception is distinct *and* that each exception preserves its context (e.g. the missing UUID, the schema version mismatch) so downstream tests can make precise assertions.
- A single integration-style test (`test_all_exceptions_share_common_base`) verifies the cross-cutting property that the design doc establishes — that `FinanceTrackerError` can serve as a unified catch — by raising and catching every concrete exception type.
- The design doc explicitly notes that `UnsupportedSchemaVersion` is *not* a subclass of `PersistenceError`. This is regression-protected by `test_not_subclass_of_persistence_error`, ensuring future refactors don't silently change the public hierarchy.

**Test case completeness:**

- For each of the 4 concrete exception classes:
  - Inheritance from `FinanceTrackerError` is verified.
  - Every documented attribute is verified to be stored.
  - The `str()` representation is verified to include each attribute (so logs and test failures are informative).
- The base class `FinanceTrackerError` is verified to derive from `Exception` (otherwise `raise` would not work).
- The negative-case design constraint (`UnsupportedSchemaVersion` ≠ `PersistenceError`) is explicitly tested.
- A combined behavioral test verifies the "unified catch" property across all exception types.

## Automated Test Code

Test file: `src/domain/test_exceptions.py`

### Test cases

| # | Test | Inputs | Expected Output |
|---|------|--------|-----------------|
| 1 | `TestFinanceTrackerError.test_is_an_exception` | `FinanceTrackerError` class | `issubclass(FinanceTrackerError, Exception)` is True |
| 2 | `TestValidationError.test_subclass_of_base` | `ValidationError` class | Subclass of `FinanceTrackerError` |
| 3 | `TestValidationError.test_stores_field_and_message` | `ValidationError(field="amount", message="must be positive")` | `err.field == "amount"`, `err.message == "must be positive"` |
| 4 | `TestValidationError.test_str_includes_field_and_message` | Same as above | `str(err)` contains `"amount"` and `"must be positive"` |
| 5 | `TestValidationError.test_can_be_raised_and_caught_as_base` | `raise ValidationError(...)` inside `pytest.raises(FinanceTrackerError)` | Caught successfully |
| 6 | `TestTransactionNotFound.test_subclass_of_base` | `TransactionNotFound` class | Subclass of `FinanceTrackerError` |
| 7 | `TestTransactionNotFound.test_stores_transaction_id` | `TransactionNotFound(transaction_id=<uuid>)` | `err.transaction_id` equals the UUID |
| 8 | `TestTransactionNotFound.test_str_includes_id` | Same as above | `str(err)` contains the UUID string |
| 9 | `TestPersistenceError.test_subclass_of_base` | `PersistenceError` class | Subclass of `FinanceTrackerError` |
| 10 | `TestPersistenceError.test_stores_message` | `PersistenceError(message="disk full")` | `err.message == "disk full"` |
| 11 | `TestPersistenceError.test_str_includes_message` | Same as above | `str(err)` contains `"disk full"` |
| 12 | `TestUnsupportedSchemaVersion.test_subclass_of_base` | `UnsupportedSchemaVersion` class | Subclass of `FinanceTrackerError` |
| 13 | `TestUnsupportedSchemaVersion.test_not_subclass_of_persistence_error` | `UnsupportedSchemaVersion` class | NOT a subclass of `PersistenceError` (regression-protect design decision) |
| 14 | `TestUnsupportedSchemaVersion.test_stores_versions` | `UnsupportedSchemaVersion(found_version=2, expected_version=1)` | `err.found_version == 2`, `err.expected_version == 1` |
| 15 | `TestUnsupportedSchemaVersion.test_str_includes_versions` | Same as above | `str(err)` contains both `"2"` and `"1"` |
| 16 | `TestExceptionHierarchy.test_all_exceptions_share_common_base` | One instance of every concrete exception type | Each is caught by `except FinanceTrackerError` |

The full source of each test is in `src/domain/test_exceptions.py`.

## Actual Outputs

All 16 test cases pass. Output of `pytest src/domain/test_exceptions.py -v`:

```
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-8.3.5, pluggy-1.5.0
cachedir: .pytest_cache
rootdir: /home/masiddiqui/personal/personal-finance-tracker-project
configfile: pytest.ini
plugins: mock-3.14.1
collected 16 items

src/domain/test_exceptions.py::TestFinanceTrackerError::test_is_an_exception PASSED                              [  6%]
src/domain/test_exceptions.py::TestValidationError::test_subclass_of_base PASSED                                 [ 12%]
src/domain/test_exceptions.py::TestValidationError::test_stores_field_and_message PASSED                         [ 18%]
src/domain/test_exceptions.py::TestValidationError::test_str_includes_field_and_message PASSED                   [ 25%]
src/domain/test_exceptions.py::TestValidationError::test_can_be_raised_and_caught_as_base PASSED                 [ 31%]
src/domain/test_exceptions.py::TestTransactionNotFound::test_subclass_of_base PASSED                             [ 37%]
src/domain/test_exceptions.py::TestTransactionNotFound::test_stores_transaction_id PASSED                        [ 43%]
src/domain/test_exceptions.py::TestTransactionNotFound::test_str_includes_id PASSED                              [ 50%]
src/domain/test_exceptions.py::TestPersistenceError::test_subclass_of_base PASSED                                [ 56%]
src/domain/test_exceptions.py::TestPersistenceError::test_stores_message PASSED                                  [ 62%]
src/domain/test_exceptions.py::TestPersistenceError::test_str_includes_message PASSED                            [ 68%]
src/domain/test_exceptions.py::TestUnsupportedSchemaVersion::test_subclass_of_base PASSED                        [ 75%]
src/domain/test_exceptions.py::TestUnsupportedSchemaVersion::test_not_subclass_of_persistence_error PASSED       [ 81%]
src/domain/test_exceptions.py::TestUnsupportedSchemaVersion::test_stores_versions PASSED                         [ 87%]
src/domain/test_exceptions.py::TestUnsupportedSchemaVersion::test_str_includes_versions PASSED                   [ 93%]
src/domain/test_exceptions.py::TestExceptionHierarchy::test_all_exceptions_share_common_base PASSED              [100%]

============================== 16 passed in 0.04s ==============================
```

**Result: 16 passed, 0 failed.**
