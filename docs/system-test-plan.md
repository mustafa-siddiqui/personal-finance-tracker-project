# System Test Plan — Personal Finance Tracker

## Date

2026-06-13

## Engineers

Mustafa Siddiqui, Owais Adil Mohammed, Anas Rais Lnu, Mohd Karim Siddiqui

## Purpose

This document defines the **system-level** test plan for the Personal Finance Tracker. Where the unit tests in `docs/unit-test-reports/` exercise individual classes in isolation with mocks, the tests here exercise the application end-to-end through its public HTTP interface, with the real `JsonTransactionRepository` writing to a real (test-scoped) JSON file. These tests are executed manually; they are not part of the automated `make test` target.

## Scope

In scope:

- All eight functional requirements (F1–F8) end-to-end via the Flask UI layer.
- Persistence across application restarts (F5).
- Validation enforcement at the system boundary (F6).
- Error responses (4xx) for malformed user input.

Out of scope:

- Concurrency / multi-process access (single-user assumption — see `design.md` "Known limitations").
- Performance / load testing.
- Browser / front-end rendering tests (no HTML form layer in v1).

## Development & Test Environment

This section captures the software (with versions) used to develop and test the Personal Finance Tracker, and the steps to reproduce that environment on a new machine. A maintainer who has never seen this project should be able to follow the instructions below verbatim and reach a state where `make test` passes and the Flask app responds on `http://127.0.0.1:5000`.

### Software used — application development

| Software | Version | Purpose |
|----------|---------|---------|
| Python | >=3.8.10 | Implementation language |
| Flask | 3.0.3 | Web framework for the UI layer (F7) |
| pip | >=20.0.2 | Package manager |
| git | any | Source control / cloning the repo |

### Software used — testing

| Software | Version | Purpose |
|----------|---------|---------|
| pytest | 8.3.5 | Test runner and assertion framework (unit + integration tests) |
| pytest-mock | 3.14.1 | Mocking helper used in unit tests |
| curl | any | Issuing HTTP requests for manual system tests |

### Standard library modules used

`uuid`, `decimal`, `datetime`, `json`, `os`, `pathlib`, `typing`, `enum`, `abc`, `unittest.mock` — all from the Python 3.8 standard library, no version pinning required.

### Operating systems used during development

| OS | Version |
|----|---------|
| Linux | 6.6.87.2-microsoft-standard-WSL2 (Ubuntu 20.04) |
| macOS | Tahoe 26.5 |

The test suite is OS-agnostic — `pytest`'s `tmp_path` fixture handles per-test temporary directories portably. Tests should pass on any Linux, macOS, or Windows machine running Python 3.8 or newer.

### Deployment & setup instructions

#### Prerequisites

- Python 3.8 or newer on the `PATH`
- `git` for cloning the repository

#### One-time setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd personal-finance-tracker-project

# 2. Create a virtual environment (named .venv by convention)
python3 -m venv .venv

# 3. Activate the virtual environment
source .venv/bin/activate            # Linux / macOS
# .venv\Scripts\activate              # Windows

# 4. Install all dependencies (production + test)
pip install -r requirements.txt
```

The `.venv/` directory is excluded from version control via `.gitignore`. Each developer creates their own.

#### Running the unit / integration test suite

With the virtual environment activated:

```bash
# Run all automated tests (unit + integration)
make test

# Run tests for a single unit with verbose output
pytest src/domain/test_transaction.py -v
```

`pytest.ini` configures discovery: pytest looks for `test_*.py` files inside `src/` (unit tests, colocated with code) and `tests/` (integration / end-to-end tests).

#### Launching the application for system tests

```bash
# From the project root, with venv active:
flask --app src.ui.app run --debug
```

The server listens on `http://127.0.0.1:5000` by default. System tests are issued against this URL.

#### Resetting state between tests

The application persists to `data/transactions.json`. To reset state between unrelated system test groups:

```bash
rm -f data/transactions.json
```

A missing file is treated as an empty store on next launch.

#### Adding a new dependency

```bash
pip install <package-name>
pip freeze > requirements.txt
git add requirements.txt
```

Commit `requirements.txt` so other developers receive the same versions on their next install.

### System test execution assumptions

1. The application is launched via `flask --app src.ui.app run` from the project root with the venv active.
2. `data/transactions.json` is empty or absent at the start of each test group (delete the file between groups to reset state).
3. Requests are issued with `curl` or any HTTP client capable of setting `Content-Type: application/json`.
4. The tester records the exact request, response body, status code, and on-disk file state in the "Actual Output" column of each test case.

## Methodology

**Approach:** Use-case-driven black-box system testing. Each major feature is described as a short use case followed by a table of concrete test cases. Inputs are concrete; expected outputs are observable values (return values, response bodies, status codes, on-disk file contents).

**Why this methodology:** At the system level we are verifying that the layers — UI, application, domain, repository — compose correctly into the behavior promised by the functional requirements. We treat the application as a black box at the highest available seam and assert only on observable interface behavior.

### Two test surfaces

The application has two natural system-level surfaces. Both are exercised in this plan:

- **Backend integration surface.** The application's public Python API: `Ledger`, `BalanceCalculator`, `Analyzer`, `JsonTransactionRepository`. These tests are **automated** in `tests/test_system_backend.py` and run with the rest of the suite via `make test`. They wire the real `Ledger` to the real `JsonTransactionRepository` against a `tmp_path`-scoped JSON file, and exercise F1, F2, F3, F4, F5, F6, F8 end-to-end without any HTTP layer. This is the "without UI" stack referenced throughout this document.
- **HTTP / UI surface.** The Flask app defined in `src/ui/app.py`. These tests are **manual** at present (no rendered HTML form in v1). The tester issues `curl` requests and records the response body and on-disk side effects in the "Actual Output" column.

## Use Cases and Test Cases

### UC-1 — Record a transaction (F1, F5, F6)

**Actor:** User
**Precondition:** Application running; `data/transactions.json` empty or absent.
**Main flow:**
1. User submits a new transaction with `type`, `amount`, `category`, `description`, `date`.
2. The application layer hands the raw values to `Ledger.record()`.
3. `Ledger` calls `Validator` for each field; on failure it raises `ValidationError`.
4. On success `Ledger` builds a `Transaction` with a fresh server-generated UUID, calls `repo.add()`, then `repo.save()`.
5. The new transaction (including its `id`) is returned to the caller.

**Postcondition (success):** The on-disk JSON file contains the new transaction; `schema_version` is `1`.
**Postcondition (failure):** The on-disk JSON file is byte-for-byte identical to its pre-test state (no partial writes).

**Backend integration surface (`tests/test_system_backend.py::TestUC1RecordTransaction`):**

| # | Test | Test Methodology | Inputs | Expected Output | Actual Output |
|---|------|------------------|--------|-----------------|---------------|
| 1.1 | Happy-path expense persists to disk | Specification-based / equivalence partition: representative valid expense | `Ledger.record(type="expense", amount="42.50", category="food", description="Groceries", date="2026-06-13")` against an empty repo | Returns a `Transaction` with a `UUID` id; on disk: `schema_version=1`, `transactions` of length 1 with `amount="42.50"` and `type="expense"` | PASS — all assertions hold |
| 1.2 | Happy-path income | Equivalence partition: alternate `type` value | `record(type="income", amount="2500.00", category="salary", description="April paycheck", date="2026-04-15")` | On disk: transaction with `type="income"`, `category="salary"` | PASS |
| 1.3 | Large-value precision (D1) | Boundary-value: max realistic amount | `record(... amount="999999999999.99" ...)` | On disk the persisted `amount` string is exactly `"999999999999.99"` (no float rounding, no scientific notation) | PASS — exact string match |
| 1.4 | Smallest legal amount | Boundary-value: minimum positive | `record(... amount="0.01" ...)` | On disk amount exactly `"0.01"` | PASS |
| 1.5 | Negative amount rejected | Equivalence partition: invalid amount class | `record(... amount="-10.00" ...)` | Raises `ValidationError(field="amount")`; JSON file does not exist (no partial write) | PASS — `exc.field == "amount"`, file absent |
| 1.6 | Zero amount rejected | Boundary-value: just below minimum positive | `record(... amount="0" ...)` | Raises `ValidationError(field="amount")` | PASS |
| 1.7 | Non-numeric amount rejected | Equivalence partition: malformed amount | `record(... amount="abc" ...)` | Raises `ValidationError(field="amount")` | PASS |
| 1.8 | Disallowed category rejected | Equivalence partition: invalid category class | `record(... category="crypto" ...)` | Raises `ValidationError(field="category")` | PASS |
| 1.9 | Empty description rejected | Boundary-value: minimum length | `record(... description="" ...)` | Raises `ValidationError(field="description")` | PASS |
| 1.10 | Malformed date rejected | Specification-based: format violation | `record(... date="2026/04/30" ...)` | Raises `ValidationError(field="date")` | PASS |
| 1.11 | Invalid `type` value rejected | Equivalence partition: outside `{income, expense}` | `record(type="transfer", ...)` | Raises `ValidationError(field="type")` | PASS |
| 1.12 | UUIDs unique across calls | Regression check | Two consecutive `record()` calls with identical inputs | The two returned `Transaction.id` values differ | PASS |

**HTTP / UI surface — to be filled in by UI owner once `app.py` is repaired:**

| # | Test | Inputs | Expected Output | Actual Output |
|---|------|--------|-----------------|---------------|
| 1.H1 | Happy-path expense via HTTP | `POST /add` body `{"type":"expense","amount":"42.50","category":"food","description":"Groceries","date":"2026-06-13"}` | `201 Created`; body includes `id`; JSON file contains the new transaction | _to be filled_ |
| 1.H2 | Missing field via HTTP | `POST /add` body omitting `amount` | `400 Bad Request`; body includes `error`; JSON file unchanged | _to be filled_ |
| 1.H3 | Negative amount via HTTP | `POST /add` body with `"amount":"-10.00"` | `400 Bad Request`; body indicates `amount` invalid; JSON file unchanged | _to be filled_ |
| 1.H4 | Disallowed category via HTTP | `POST /add` body with `"category":"crypto"` | `400 Bad Request`; body indicates `category` invalid; JSON file unchanged | _to be filled_ |
| 1.H5 | Malformed date via HTTP | `POST /add` body with `"date":"2026/06/13"` | `400 Bad Request`; body indicates `date` invalid; JSON file unchanged | _to be filled_ |

### UC-2 — View / list transactions (F2)

**Actor:** User
**Precondition:** Application started; backing JSON file may be empty, missing, or populated.
**Main flow:**
1. User requests the full list of transactions.
2. UI layer calls `Ledger.list_all()`, which delegates to `repo.list_all()`.
3. The repository returns the in-memory list (already hydrated from disk by `repo.load()` at startup).
4. UI returns a JSON array.

**Postcondition:** No state change; the JSON file is not modified.

**Backend integration surface (`tests/test_system_backend.py::TestUC2ListTransactions`):**

| # | Test | Test Methodology | Inputs | Expected Output | Actual Output |
|---|------|------------------|--------|-----------------|---------------|
| 2.1 | Empty store lists empty | Boundary: empty collection | `repo.list_all()` on a freshly-loaded repo against a non-existent JSON file | Returns `[]` | PASS — `repo.list_all() == []` |
| 2.2 | Populated store lists all | Equivalence: representative populated case | Record 3 transactions via `Ledger.record()`, then call `repo.list_all()` | Returns a list of length 3 | PASS — `len(repo.list_all()) == 3` |
| 2.3 | Round-trip field fidelity | Symmetry test (D2): persist + reload preserves every field | Record 1 transaction; instantiate a fresh `JsonTransactionRepository` against the same path and call `load()` | Reloaded transaction's `type`, `amount` (`Decimal`), `category`, `description`, and `date` (`datetime.date`) equal the originals | PASS — all five fields match exactly |

**HTTP / UI surface:**

| # | Test | Inputs | Expected Output | Actual Output |
|---|------|--------|-----------------|---------------|
| 2.H1 | Empty list via HTTP | `GET /transactions` with no transactions recorded | `200 OK`; body is `[]` | _to be filled_ |
| 2.H2 | Populated list via HTTP | `GET /transactions` after recording 3 transactions | `200 OK`; body is a JSON array of length 3 | _to be filled_ |
| 2.H3 | Round-trip fidelity via HTTP | Compare each transaction returned by `GET /transactions` against the body of the prior `POST /add` | All five user-supplied fields match | _to be filled_ |

### UC-3 — Calculate current balance (F3)

**Actor:** User
**Precondition:** Application started; transaction store may be empty or populated.
**Main flow:**
1. User requests current balance.
2. `BalanceCalculator.calculate(repo.list_all())` is invoked.
3. For every transaction, `INCOME` adds `amount` and `EXPENSE` subtracts `amount`, all in `Decimal` arithmetic.
4. The resulting `Decimal` is returned.

**Postcondition:** No state change; this is a pure read.

**Backend integration surface (`tests/test_system_backend.py::TestUC3Balance`):**

| # | Test | Test Methodology | Inputs | Expected Output | Actual Output |
|---|------|------------------|--------|-----------------|---------------|
| 3.1 | Empty store balance is zero | Boundary: empty input | `BalanceCalculator.calculate([])` | `Decimal("0")` | PASS — returned `Decimal("0")` |
| 3.2 | Income only | Equivalence: pure-income class | One `income` of `2500.00` | `Decimal("2500.00")` | PASS |
| 3.3 | Expenses only (negative balance) | Equivalence: pure-expense class | Two expenses of `42.50` and `100.00` | `Decimal("-142.50")` | PASS |
| 3.4 | Mixed income and expenses | Equivalence: representative real-world case | Income `1000.00`; expenses `200.00` and `50.00` | `Decimal("750.00")` | PASS |
| 3.5 | Large value precision (D1) | Boundary: max realistic amount | One income of `999999999999.99` | `Decimal("999999999999.99")` (no float drift) | PASS — exact equality preserved |

**HTTP / UI surface:**

| # | Test | Inputs | Expected Output | Actual Output |
|---|------|--------|-----------------|---------------|
| 3.H1 | Balance via HTTP, empty store | `GET /balance` against an empty store | `200 OK`; body contains balance `"0"` (or `"0.00"`) | _to be filled — endpoint not yet implemented_ |
| 3.H2 | Balance via HTTP, mixed | Record one `income=1000.00`, two expenses (`200.00`, `50.00`); then `GET /balance` | `200 OK`; balance `"750.00"` | _to be filled — endpoint not yet implemented_ |

### UC-4 — Delete a transaction (F4, F5)

**Actor:** User
**Precondition:** Application started; at least one transaction exists for the happy-path case.
**Main flow:**
1. User submits a delete request identifying a transaction by UUID.
2. UI layer parses the URL parameter to a `UUID` and calls `Ledger.delete(txn_id)`.
3. `Ledger` defensively type-checks the argument, calls `repo.delete(txn_id)`, then `repo.save()`.
4. UI returns a success response.

**Postcondition (success):** The transaction is removed from both the in-memory store and the JSON file.
**Postcondition (failure):** The store and JSON file are unchanged.

**Backend integration surface (`tests/test_system_backend.py::TestUC4DeleteTransaction`):**

| # | Test | Test Methodology | Inputs | Expected Output | Actual Output |
|---|------|------------------|--------|-----------------|---------------|
| 4.1 | Delete existing transaction persists | Happy path + symmetry test | Record one transaction; call `Ledger.delete(txn.id)` | `repo.list_all()` is empty; `data/transactions.json` `"transactions"` array is empty | PASS — in-memory empty AND on-disk array empty |
| 4.2 | Delete unknown UUID raises | Equivalence: error path | Call `Ledger.delete(UUID("00000000-..."))` against an empty repo | Raises `TransactionNotFound` | PASS — exception raised |
| 4.3 | Defensive isinstance check | Specification-based: type contract | Call `Ledger.delete("00000000-...")` (string, not UUID) | Raises `ValidationError(field="id")` | PASS — `exc.field == "id"` |

**HTTP / UI surface:**

| # | Test | Inputs | Expected Output | Actual Output |
|---|------|--------|-----------------|---------------|
| 4.H1 | Delete existing via HTTP | Record a transaction, then `DELETE /delete/<that-uuid>` | `200 OK`; transaction gone from `GET /transactions` and from JSON file | _to be filled |
| 4.H2 | Delete unknown UUID via HTTP | `DELETE /delete/00000000-0000-0000-0000-000000000000` | `404 Not Found`; JSON file unchanged | _to be filled_ |
| 4.H3 | Delete malformed UUID via HTTP | `DELETE /delete/not-a-uuid` | `400 Bad Request` (or `404` from Flask's `<uuid:>` converter); JSON file unchanged | _to be filled_ |

### UC-5 — Persistence across restarts (F5)

**Actor:** User
**Precondition:** Application has at some point persisted state to `data/transactions.json` (or has not — see test 5.2).
**Main flow:**
1. User starts the application.
2. `JsonTransactionRepository.load()` is called once at startup.
3. Subsequent reads (`list_all`, balance, analytics) operate on the hydrated in-memory store.

**Postcondition (success):** The in-memory store accurately reflects the on-disk state.
**Postcondition (failure):** The on-disk file is **not** overwritten or modified by a failed load.

**Backend integration surface (`tests/test_system_backend.py::TestUC5Persistence`):**

| # | Test | Test Methodology | Inputs | Expected Output | Actual Output |
|---|------|------------------|--------|-----------------|---------------|
| 5.1 | Round-trip across repo instances | Symmetry test: save then load via a fresh instance | Record 2 transactions through `Ledger`; instantiate a new `JsonTransactionRepository(path=...)` and call `load()` | `fresh.list_all()` returns 2 transactions | PASS |
| 5.2 | Missing file loads as empty | Boundary: file does not exist | Call `load()` against a path that has never existed | `repo.list_all() == []`; no exception | PASS |
| 5.3 | Corrupt file raises PersistenceError | Specification-based: malformed input | Write `"not json {{"` to the JSON file; call `load()` | Raises `PersistenceError`; the corrupt file is left byte-identical (not overwritten) | PASS — exception raised; file content preserved |
| 5.4 | Unsupported schema_version raises | Specification-based: version contract (D8) | Write `{"schema_version": 999, "transactions": []}`; call `load()` | Raises `UnsupportedSchemaVersion` | PASS |

**HTTP / UI surface:**

| # | Test | Inputs | Expected Output | Actual Output |
|---|------|--------|-----------------|---------------|
| 5.H1 | Round-trip across Flask restarts | Record 2 transactions via `POST /add`; `kill` the Flask process; relaunch; `GET /transactions` | Both transactions returned with identical field values | _to be filled_ |
| 5.H2 | Empty file on first launch | Delete `data/transactions.json`; launch Flask; `GET /transactions` | `200 OK`; body `[]`; no crash | _to be filled_ |
| 5.H3 | Corrupt file behavior | Overwrite `data/transactions.json` with `not json`; relaunch Flask | App either fails to start with a clear error, or first request returns `500`; corrupt file is **not** overwritten | _to be filled_ |
| 5.H4 | Unsupported schema | Edit `schema_version` to `999`; relaunch Flask | App fails fast with `UnsupportedSchemaVersion`; existing data file is left intact | _to be filled_ |

### UC-6 — Input validation (F6)

Validation is exercised at the system level by every UC-1 negative case (1.5–1.13) on the backend integration surface, and by the corresponding HTTP rows once the UI is repaired. Each negative case confirms that:

1. `Validator` is reached from the application layer.
2. Failure raises a typed `ValidationError` with the correct `field`.
3. No partial write reaches `data/transactions.json` (verified by checking the file does not exist or is unchanged).

### UC-7 — User interface (F7)

**Actor:** User
**Precondition:** Application running.
**Main flow:** User opens the app's homepage in a browser and interacts with rendered forms / lists.

| # | Test | Inputs | Expected Output | Actual Output |
|---|------|--------|-----------------|---------------|
| 7.1 | Home page reachable | `GET /` | `200 OK`; body contains the page title or a marker string | _to be filled — currently returns plain text "Personal Finance Tracker", no rendered template_ |
| 7.2 | Add form renders | `GET /` and inspect HTML | Body contains a `<form>` for transaction entry with fields for type, amount, category, description, date | _to be filled — no template exists yet_ |
| 7.3 | Transaction list renders | After recording a transaction, `GET /` | Body lists the recorded transaction with a delete control | _to be filled — no template exists yet_ |

*Note: v1 has no rendered HTML templates and as such these tests are not applicable *

### UC-8 — Analyze spending (F8)

**Actor:** User
**Precondition:** Application started; transactions may be empty or populated.
**Main flow:**
1. User requests an analytics view (category totals, highest-spending category, monthly summary, or monthly trends).
2. `Analyzer` reads `repo.list_all()` and aggregates in `Decimal` arithmetic.
3. Results are returned as `dict` / `CategorySummary` / `MonthlySummary` / `list[MonthlySummary]`.

**Postcondition:** No state change; analytics are pure reads.

**Backend integration surface (`tests/test_system_backend.py::TestUC8Analytics`):**

| # | Test | Test Methodology | Inputs | Expected Output | Actual Output |
|---|------|------------------|--------|-----------------|---------------|
| 8.1 | Category totals aggregates correctly | Equivalence: representative multi-category case | 3 expenses: food `40.00`, food `60.00`, transportation `25.00` | `{"food": Decimal("100.00"), "transportation": Decimal("25.00")}` | PASS |
| 8.2 | Highest-spending category | Same dataset as 8.1 | `analyzer.highest_spending_category()` | `CategorySummary(category="food", total=Decimal("100.00"))` | PASS |
| 8.3 | Empty store returns None | Boundary: empty input | `analyzer.highest_spending_category()` on empty repo | `None` (no exception) | PASS |
| 8.4 | Monthly summary populated | Equivalence: month with both income and expense | Income `1000.00` + expense `200.00`, both dated 2026-04-15/2026-04-20 | `MonthlySummary(year=2026, month=4, total_income=1000.00, total_expenses=200.00, net=800.00)` | PASS |
| 8.5 | Monthly summary empty month zeroed | Boundary: month with no data | `analyzer.monthly_summary(2026, 1)` on empty repo | `total_income=0`, `total_expenses=0`, `net=0` (no exception) | PASS |
| 8.6 | Monthly trends chronological | Specification-based: ordering contract | Three income transactions dated 2026-04-15, 2026-05-15, 2026-06-15 | Returned list of `MonthlySummary` with `(year, month)` pairs `[(2026,4), (2026,5), (2026,6)]` in order | PASS |

**HTTP / UI surface:**

| # | Test | Inputs | Expected Output | Actual Output |
|---|------|--------|-----------------|---------------|
| 8.H1 | Category totals via HTTP | Record dataset 8.1 above; `GET /analytics/category-totals?type=expense` | `200 OK`; body matches expected aggregation | _to be filled — endpoint not yet implemented_ |
| 8.H2 | Highest-spending category via HTTP | Same dataset; `GET /analytics/highest-spending` | `200 OK`; body identifies `food` with total `100.00` | _to be filled_ |
| 8.H3 | Monthly summary via HTTP | Record dataset 8.4; `GET /analytics/monthly?year=2026&month=4` | `200 OK`; body matches expected summary | _to be filled_ |
| 8.H4 | Monthly trends via HTTP | Record dataset 8.6; `GET /analytics/monthly-trends` | `200 OK`; body lists 3 months in chronological order | _to be filled_ |

## Pass / Fail Criteria

A test case **passes** if and only if the actual return values, response bodies, and observable file state on disk all match the "Expected Output" column. A single mismatch is a fail; partial credit is not given.

The system test pass is considered complete when every test case in this document — across both the backend integration surface and the HTTP / UI surface — executes to a pass on the same build, with `data/transactions.json` reset between unrelated test groups.

## Test Execution

### Backend integration surface (automated)

Run from the project root with the venv activated:

```bash
pytest tests/test_system_backend.py -v
```

Each test uses `pytest`'s `tmp_path` fixture to isolate its own JSON file, so tests are reproducible and do not interfere with each other.

**Latest run — 2026-06-13, all 33 backend system tests passed:**

```
============================= test session starts ==============================
platform linux -- Python 3.8.10, pytest-8.3.5, pluggy-1.5.0
rootdir: /home/masiddiqui/personal/personal-finance-tracker-project
configfile: pytest.ini
plugins: mock-3.14.1
collected 33 items

tests/test_system_backend.py::TestUC1RecordTransaction::test_happy_path_expense_persists_to_disk PASSED
tests/test_system_backend.py::TestUC1RecordTransaction::test_happy_path_income PASSED
tests/test_system_backend.py::TestUC1RecordTransaction::test_large_value_precision PASSED
tests/test_system_backend.py::TestUC1RecordTransaction::test_smallest_legal_amount PASSED
tests/test_system_backend.py::TestUC1RecordTransaction::test_negative_amount_rejected PASSED
tests/test_system_backend.py::TestUC1RecordTransaction::test_zero_amount_rejected PASSED
tests/test_system_backend.py::TestUC1RecordTransaction::test_non_numeric_amount_rejected PASSED
tests/test_system_backend.py::TestUC1RecordTransaction::test_disallowed_category_rejected PASSED
tests/test_system_backend.py::TestUC1RecordTransaction::test_empty_description_rejected PASSED
tests/test_system_backend.py::TestUC1RecordTransaction::test_malformed_date_rejected PASSED
tests/test_system_backend.py::TestUC1RecordTransaction::test_invalid_type_rejected PASSED
tests/test_system_backend.py::TestUC1RecordTransaction::test_uuids_unique_across_calls PASSED
tests/test_system_backend.py::TestUC2ListTransactions::test_empty_store_lists_empty PASSED
tests/test_system_backend.py::TestUC2ListTransactions::test_populated_store_lists_all PASSED
tests/test_system_backend.py::TestUC2ListTransactions::test_round_trip_field_fidelity PASSED
tests/test_system_backend.py::TestUC3Balance::test_empty_store_balance_is_zero PASSED
tests/test_system_backend.py::TestUC3Balance::test_income_only PASSED
tests/test_system_backend.py::TestUC3Balance::test_expenses_only_negative PASSED
tests/test_system_backend.py::TestUC3Balance::test_mixed_income_and_expenses PASSED
tests/test_system_backend.py::TestUC3Balance::test_large_value_precision PASSED
tests/test_system_backend.py::TestUC4DeleteTransaction::test_delete_existing_transaction_persists PASSED
tests/test_system_backend.py::TestUC4DeleteTransaction::test_delete_unknown_uuid_raises PASSED
tests/test_system_backend.py::TestUC4DeleteTransaction::test_delete_rejects_string_argument PASSED
tests/test_system_backend.py::TestUC5Persistence::test_round_trip_across_repo_instances PASSED
tests/test_system_backend.py::TestUC5Persistence::test_missing_file_loads_as_empty PASSED
tests/test_system_backend.py::TestUC5Persistence::test_corrupt_file_raises_persistence_error PASSED
tests/test_system_backend.py::TestUC5Persistence::test_unsupported_schema_version_raises PASSED
tests/test_system_backend.py::TestUC8Analytics::test_category_totals_aggregates_correctly PASSED
tests/test_system_backend.py::TestUC8Analytics::test_highest_spending_category PASSED
tests/test_system_backend.py::TestUC8Analytics::test_highest_spending_empty_returns_none PASSED
tests/test_system_backend.py::TestUC8Analytics::test_monthly_summary_populated PASSED
tests/test_system_backend.py::TestUC8Analytics::test_monthly_summary_empty_month_zeroed PASSED
tests/test_system_backend.py::TestUC8Analytics::test_monthly_trends_chronological PASSED

============================== 33 passed in 0.10s ==============================
```

**Result: 33 passed, 0 failed.** This output covers F1, F2, F3, F4, F5, F6, and F8 end-to-end through the full backend stack (`Ledger` → `Validator` → `JsonTransactionRepository` → on-disk JSON file → re-instantiated repository → `BalanceCalculator` / `Analyzer`).

### HTTP / UI surface (manual)

These tests are executed by the UI owner once `src/ui/app.py` is repaired against the design contract. Steps:

1. Reset state: `rm -f data/transactions.json`.
2. Launch the app: `flask --app src.ui.app run --debug`.
3. For each `*.H*` row in the use cases above, issue the request with `curl`, observe the response, and inspect `data/transactions.json` where applicable.
4. Record the actual response body, status code, and on-disk state in the "Actual Output" cell.

