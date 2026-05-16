# Unit Test Report — Unit 4: Ledger.record()

## Functional Requirement

**F1 — Record transactions.** `Ledger.record()` is the application-layer entry point that accepts raw user input, validates it, builds a `Transaction`, and persists it.

## Unit

| File | Description |
|------|-------------|
| `src/application/ledger.py` | `Ledger` class — only the `record()` method is in scope for this report (F2 / F4 methods are owned by Owais and remain unimplemented) |
| `src/application/test_ledger.py` | Unit tests |

## Date

2026-05-16

## Engineers

Mustafa Siddiqui

## Test Methodology

**Approach:** Specification-based black-box testing combined with interaction (collaboration) testing using mocks for the `Validator` and `TransactionRepositoryInterface` dependencies.

**Why this methodology:**

- `Ledger.record()` is an orchestrator: it owns no data-transformation logic of its own. Its responsibility is to call validators in the right order, build a `Transaction` from the validators' normalized output, and hand it off to the repository. The correct way to test an orchestrator is to verify *what it does to its collaborators*, not to re-test the collaborators themselves.
- `Validator` and `TransactionRepositoryInterface` are mocked so this unit's behavior is isolated from F6 (Anas's validation rules) and F5 (the JSON serialization layer). Each of those is independently tested by its own unit (Unit 2 / Unit 3 + Anas's eventual F6 unit). Mocks preserve the boundary between units, which is the whole point of unit testing.
- Black-box testing of the public contract (`record(...) -> Transaction`) is combined with interaction testing (asserting which collaborator methods were called, with what arguments, in what order). Both are necessary because:
  - The return value matters — callers receive the `Transaction`.
  - The side effects matter — failure to call `repo.save()` would silently lose data, and calling `repo.save()` *before* validating would write garbage to disk.
- Equivalence partitioning separates the happy-path equivalence class from the validation-failure class. Within validation failures, multiple fields are tested (amount, type) to ensure the propagation behavior is uniform.
- Order-sensitive interactions (`add()` must precede `save()`) are explicitly verified, since the design doc (Persistence Abstraction section) makes this contract part of the repository's API.

**Test case completeness:**

- **Happy path:** return type, returned field values match validator output, fresh UUID generated, UUIDs are unique across calls.
- **Collaborator interaction:** each validator is called exactly once with the corresponding raw input.
- **Failure paths:** validator-raised `ValidationError` propagates unchanged; failed validation never reaches `repo.add()` or `repo.save()` (no partial-write bugs).
- **Persistence ordering:** `add()` is called before `save()`; the `Transaction` passed to `add()` is the one returned to the caller; `save()` is called exactly once.

## Automated Test Code

Test file: `src/application/test_ledger.py`. Tests use `unittest.mock.MagicMock(spec=...)` to stand in for `Validator` and `TransactionRepositoryInterface`, isolating `Ledger` from real validation rules and real I/O.

### Test cases

| # | Test | Inputs | Expected Output |
|---|------|--------|-----------------|
| 1 | `TestRecordHappyPath.test_record_returns_transaction` | Valid raw inputs | Returns a `Transaction` instance |
| 2 | `TestRecordHappyPath.test_record_populates_validated_fields` | Valid raw inputs | Returned `Transaction`'s fields equal the validator's normalized return values (not the raw inputs) |
| 3 | `TestRecordHappyPath.test_record_generates_uuid` | Valid raw inputs | Returned `Transaction.id` is a `UUID` |
| 4 | `TestRecordHappyPath.test_record_generates_unique_uuids` | Two consecutive `record()` calls with identical inputs | The two returned `Transaction`s have different `id` values |
| 5 | `TestRecordValidatorInteraction.test_record_calls_each_validator` | Valid raw inputs | `validate_type`, `validate_amount`, `validate_category`, `validate_description`, `validate_date` each called once with the matching raw value |
| 6 | `TestRecordValidatorInteraction.test_record_propagates_validation_error_from_amount` | `validate_amount` configured to raise `ValidationError(field="amount", ...)` | `record()` raises `ValidationError`; `exc.field == "amount"` |
| 7 | `TestRecordValidatorInteraction.test_record_propagates_validation_error_from_type` | `validate_type` configured to raise `ValidationError(field="type", ...)` | `record()` raises `ValidationError`; `exc.field == "type"` |
| 8 | `TestRecordValidatorInteraction.test_record_does_not_persist_on_validation_failure` | Validation fails | `mock_repo.add` and `mock_repo.save` are never called |
| 9 | `TestRecordRepositoryInteraction.test_record_calls_add_then_save` | Valid raw inputs | `add()` is the first call on the repo, `save()` is the second |
| 10 | `TestRecordRepositoryInteraction.test_record_passes_built_transaction_to_add` | Valid raw inputs | The `Transaction` passed to `repo.add()` is the same object returned by `record()` |
| 11 | `TestRecordRepositoryInteraction.test_record_calls_save_exactly_once` | Valid raw inputs | `repo.save` called exactly one time |

The full source of each test is in `src/application/test_ledger.py`.

## Actual Outputs

All 11 test cases pass. Output of `pytest src/application/test_ledger.py -v`:

```
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-8.3.5, pluggy-1.5.0
cachedir: .pytest_cache
rootdir: /home/masiddiqui/personal/personal-finance-tracker-project
configfile: pytest.ini
plugins: mock-3.14.1
collected 11 items

src/application/test_ledger.py::TestRecordHappyPath::test_record_returns_transaction PASSED                          [  9%]
src/application/test_ledger.py::TestRecordHappyPath::test_record_populates_validated_fields PASSED                   [ 18%]
src/application/test_ledger.py::TestRecordHappyPath::test_record_generates_uuid PASSED                               [ 27%]
src/application/test_ledger.py::TestRecordHappyPath::test_record_generates_unique_uuids PASSED                       [ 36%]
src/application/test_ledger.py::TestRecordValidatorInteraction::test_record_calls_each_validator PASSED              [ 45%]
src/application/test_ledger.py::TestRecordValidatorInteraction::test_record_propagates_validation_error_from_amount PASSED [ 54%]
src/application/test_ledger.py::TestRecordValidatorInteraction::test_record_propagates_validation_error_from_type PASSED [ 63%]
src/application/test_ledger.py::TestRecordValidatorInteraction::test_record_does_not_persist_on_validation_failure PASSED [ 72%]
src/application/test_ledger.py::TestRecordRepositoryInteraction::test_record_calls_add_then_save PASSED              [ 81%]
src/application/test_ledger.py::TestRecordRepositoryInteraction::test_record_passes_built_transaction_to_add PASSED  [ 90%]
src/application/test_ledger.py::TestRecordRepositoryInteraction::test_record_calls_save_exactly_once PASSED          [100%]

============================== 11 passed in 0.06s ==============================
```

**Result: 11 passed, 0 failed.**
