# Unit Test Report — Unit 1: Transaction Model

## Functional Requirement

**F1 — Record transactions.** This unit provides the in-memory data structure produced by `Ledger.record()` and consumed by every other component.

## Unit

| File | Description |
|------|-------------|
| `src/domain/transaction.py` | `Transaction` data class and `TransactionType` enum |
| `src/domain/test_transaction.py` | Unit tests |

## Date

2026-05-16

## Engineers

Mustafa Siddiqui

## Test Methodology

**Approach:** Specification-based black-box testing with selected boundary and equivalence-class cases.

**Why this methodology:**

- The `Transaction` class is a value object with no branching logic — its behavior is fully described by its public contract (field assignment, equality, hashing, representation). Black-box testing exercises that contract directly without coupling tests to internal representation, which keeps the tests stable as the implementation evolves.
- For the `amount` field, boundary-value analysis is used (very small `0.01` and very large `999999999999.99` `Decimal` values) to verify that the design decision to use `Decimal` end-to-end (D1 in the design doc) actually preserves precision in the data structure. This directly supports the F3 "large value handling" adverse condition.
- For equality and hashing, equivalence partitioning separates "same id" from "different id" cases, plus the boundary case of comparing against a non-`Transaction` value.

**Test case completeness:**

- Every field of `Transaction` is asserted on at least once in `test_all_fields_assigned`.
- Both members of `TransactionType` are tested individually.
- The `__eq__` contract is tested for: equality with same id, inequality with different id, inequality with non-`Transaction` types (string, int, None).
- The `__hash__` contract is tested for: equality with `hash(id)`, and behavior when used in a `set` (deduplication of objects with the same id but different field values).
- `__repr__` is tested for inclusion of every field, since the design doc states that exception/debugging contexts should be informative.

## Automated Test Code

Test file: `src/domain/test_transaction.py`

### Test cases

| # | Test | Inputs | Expected Output |
|---|------|--------|-----------------|
| 1 | `TestTransactionType.test_income_value` | `TransactionType.INCOME.value` | `"income"` |
| 2 | `TestTransactionType.test_expense_value` | `TransactionType.EXPENSE.value` | `"expense"` |
| 3 | `TestTransactionType.test_only_two_members` | `len(TransactionType)` | `2` |
| 4 | `TestTransactionConstruction.test_all_fields_assigned` | A fully-populated `Transaction` | All six fields readable as constructed |
| 5 | `TestTransactionConstruction.test_income_construction` | `type=TransactionType.INCOME` | `txn.type == TransactionType.INCOME` |
| 6 | `TestTransactionConstruction.test_large_amount_preserved_exactly` | `amount=Decimal("999999999999.99")` | Same `Decimal` value, no precision loss |
| 7 | `TestTransactionConstruction.test_small_amount_preserved_exactly` | `amount=Decimal("0.01")` | Same `Decimal` value, no precision loss |
| 8 | `TestTransactionEquality.test_equal_when_ids_match` | Two `Transaction` instances with the same `id` but different descriptions | `a == b` |
| 9 | `TestTransactionEquality.test_not_equal_when_ids_differ` | Two `Transaction` instances with different `id`s | `a != b` |
| 10 | `TestTransactionEquality.test_not_equal_to_non_transaction` | Compare against `"not a transaction"`, `42`, `None` | `txn != x` for all |
| 11 | `TestTransactionEquality.test_hash_matches_id_hash` | A `Transaction` with a known `id` | `hash(txn) == hash(id)` |
| 12 | `TestTransactionEquality.test_usable_in_set` | Two `Transaction` objects with same `id`, different descriptions, in a `set` | `len(set) == 1` |
| 13 | `TestTransactionRepr.test_repr_includes_all_fields` | A populated `Transaction` | `repr(txn)` includes id, type, amount, category, description, date |

The full source of each test is in `src/domain/test_transaction.py`.

## Actual Outputs

All 13 test cases pass. Output of `pytest src/domain/test_transaction.py -v`:

```
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-8.3.5, pluggy-1.5.0
cachedir: .pytest_cache
rootdir: /home/masiddiqui/personal/personal-finance-tracker-project
configfile: pytest.ini
plugins: mock-3.14.1
collected 13 items

src/domain/test_transaction.py::TestTransactionType::test_income_value PASSED                 [  7%]
src/domain/test_transaction.py::TestTransactionType::test_expense_value PASSED                [ 15%]
src/domain/test_transaction.py::TestTransactionType::test_only_two_members PASSED             [ 23%]
src/domain/test_transaction.py::TestTransactionConstruction::test_all_fields_assigned PASSED  [ 30%]
src/domain/test_transaction.py::TestTransactionConstruction::test_income_construction PASSED  [ 38%]
src/domain/test_transaction.py::TestTransactionConstruction::test_large_amount_preserved_exactly PASSED [ 46%]
src/domain/test_transaction.py::TestTransactionConstruction::test_small_amount_preserved_exactly PASSED [ 53%]
src/domain/test_transaction.py::TestTransactionEquality::test_equal_when_ids_match PASSED     [ 61%]
src/domain/test_transaction.py::TestTransactionEquality::test_not_equal_when_ids_differ PASSED [ 69%]
src/domain/test_transaction.py::TestTransactionEquality::test_not_equal_to_non_transaction PASSED [ 76%]
src/domain/test_transaction.py::TestTransactionEquality::test_hash_matches_id_hash PASSED     [ 84%]
src/domain/test_transaction.py::TestTransactionEquality::test_usable_in_set PASSED            [ 92%]
src/domain/test_transaction.py::TestTransactionRepr::test_repr_includes_all_fields PASSED     [100%]

============================== 13 passed in 0.03s ==============================
```

**Result: 13 passed, 0 failed.**
