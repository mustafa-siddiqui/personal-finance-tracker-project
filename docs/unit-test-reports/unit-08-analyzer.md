# Unit Test Report — Unit 8: Analyzer

## Functional Requirement

**F8 — Analyze spending summaries, category totals, highest-spending category, and monthly trends.** This unit provides read-only analytics over the full set of recorded transactions and turns stored transaction data into user-facing financial insights.

## Unit

| File | Description |
|------|-------------|
| `src/application/analyzer.py` | `Analyzer` class plus `CategorySummary` and `MonthlySummary` result DTOs |
| `src/application/test_analyzer.py` | Unit tests |

## Date

2026-05-17

## Engineers

Mohd Karim Siddiqui

## Test Methodology

**Approach:** Specification-based black-box testing.

**Why this methodology:**

- `Analyzer` is a read-only analytics service. Its responsibility is to transform a repository-provided transaction list into stable summary outputs.
- The unit has no input parsing, no filesystem access, and no UI logic of its own. The most appropriate unit-test focus is therefore on transaction-set inputs and the resulting summary outputs.
- `TransactionRepositoryInterface` is mocked so the tests stay isolated from persistence behavior (F5) and from validation behavior (F6). This keeps the tests focused on F8 logic only.
- Equivalence partitioning was used to separate empty datasets, expense-only datasets, income-only datasets, mixed monthly datasets, and multi-month datasets.
- Boundary-style thinking was applied to zero-result scenarios, such as analytics over an empty repository and months with no transactions.

**Test case completeness:**

- `category_totals()` is covered for grouping, repeated-category accumulation, transaction-type filtering, and empty datasets.
- `highest_spending_category()` is covered for the normal case and the no-expense case.
- `monthly_summary()` is covered for month filtering, correct `Decimal` totals, net calculation, and zeroed summaries when no data exists for the requested month.
- `monthly_trends()` is covered for chronological ordering, multi-month aggregation, and empty datasets.

## Automated Test Code

Test file: `src/application/test_analyzer.py`. Tests use `unittest.mock.MagicMock(spec=TransactionRepositoryInterface)` so the unit is isolated from real storage and can be driven with precisely controlled transaction datasets.

### Test cases

| # | Test | Inputs | Expected Output |
|---|------|--------|-----------------|
| 1 | `TestCategoryTotals.test_category_totals_groups_expenses_by_category` | Mixed income/expense transactions with repeated expense categories | Returns a dictionary grouped by expense category with exact `Decimal` totals |
| 2 | `TestCategoryTotals.test_category_totals_filters_by_transaction_type` | Income and expense records in the same dataset | `category_totals(TransactionType.INCOME)` includes only income categories |
| 3 | `TestCategoryTotals.test_category_totals_returns_empty_dict_on_empty_dataset` | Empty repository | Returns `{}` |
| 4 | `TestHighestSpendingCategory.test_highest_spending_category_returns_largest_expense_total` | Expense transactions across multiple categories | Returns `CategorySummary` for the category with the greatest total expense |
| 5 | `TestHighestSpendingCategory.test_highest_spending_category_returns_none_when_no_expenses_exist` | Income-only repository | Returns `None` |
| 6 | `TestMonthlySummary.test_monthly_summary_computes_income_expense_and_net_for_target_month` | Transactions spanning the target month and other months | Returns `MonthlySummary` with correct `total_income`, `total_expenses`, and `net` for the requested month only |
| 7 | `TestMonthlySummary.test_monthly_summary_returns_zeroed_summary_when_month_has_no_data` | No transactions in requested month | Returns a zeroed `MonthlySummary` instead of raising an error |
| 8 | `TestMonthlyTrends.test_monthly_trends_returns_summaries_sorted_by_year_month` | Transactions across multiple months and years | Returns a chronologically sorted list of `MonthlySummary` objects with correct totals |
| 9 | `TestMonthlyTrends.test_monthly_trends_returns_empty_list_on_empty_dataset` | Empty repository | Returns `[]` |

The full source of each test is in `src/application/test_analyzer.py`.

## Actual Outputs

All 9 test cases pass. Output of `pytest src/application/test_analyzer.py -v`:

```text
============================= test session starts ==============================
platform linux -- Python 3.13.5, pytest-9.0.2, pluggy-1.6.0 -- /opt/pyvenv/bin/python3
rootdir: /tmp/pft/personal-finance-tracker-project-main
configfile: pytest.ini
collected 9 items

src/application/test_analyzer.py::TestCategoryTotals::test_category_totals_groups_expenses_by_category PASSED
src/application/test_analyzer.py::TestCategoryTotals::test_category_totals_filters_by_transaction_type PASSED
src/application/test_analyzer.py::TestCategoryTotals::test_category_totals_returns_empty_dict_on_empty_dataset PASSED
src/application/test_analyzer.py::TestHighestSpendingCategory::test_highest_spending_category_returns_largest_expense_total PASSED
src/application/test_analyzer.py::TestHighestSpendingCategory::test_highest_spending_category_returns_none_when_no_expenses_exist PASSED
src/application/test_analyzer.py::TestMonthlySummary::test_monthly_summary_computes_income_expense_and_net_for_target_month PASSED
src/application/test_analyzer.py::TestMonthlySummary::test_monthly_summary_returns_zeroed_summary_when_month_has_no_data PASSED
src/application/test_analyzer.py::TestMonthlyTrends::test_monthly_trends_returns_summaries_sorted_by_year_month PASSED
src/application/test_analyzer.py::TestMonthlyTrends::test_monthly_trends_returns_empty_list_on_empty_dataset PASSED

============================== 9 passed in 0.23s ==============================
```

**Result: 9 passed, 0 failed.**
