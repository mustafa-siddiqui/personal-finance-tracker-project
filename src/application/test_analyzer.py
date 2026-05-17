"""Unit tests for Analyzer."""

from __future__ import annotations

import datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import MagicMock

from src.application.analyzer import Analyzer, CategorySummary, MonthlySummary
from src.domain.transaction import Transaction, TransactionType
from src.repository.transaction_repository_interface import TransactionRepositoryInterface


def make_txn(
    txn_type: TransactionType,
    amount: str,
    category: str,
    date_str: str,
    description: str = "sample",
) -> Transaction:
    return Transaction(
        id=uuid4(),
        type=txn_type,
        amount=Decimal(amount),
        category=category,
        description=description,
        date=datetime.date.fromisoformat(date_str),
    )


class TestCategoryTotals:
    def test_category_totals_groups_expenses_by_category(self) -> None:
        repo = MagicMock(spec=TransactionRepositoryInterface)
        repo.list_all.return_value = [
            make_txn(TransactionType.EXPENSE, "12.50", "Food", "2026-05-01"),
            make_txn(TransactionType.EXPENSE, "7.50", "Food", "2026-05-02"),
            make_txn(TransactionType.EXPENSE, "20.00", "Transport", "2026-05-03"),
            make_txn(TransactionType.INCOME, "1000.00", "Salary", "2026-05-01"),
        ]

        analyzer = Analyzer(repo)

        assert analyzer.category_totals(TransactionType.EXPENSE) == {
            "Food": Decimal("20.00"),
            "Transport": Decimal("20.00"),
        }

    def test_category_totals_filters_by_transaction_type(self) -> None:
        repo = MagicMock(spec=TransactionRepositoryInterface)
        repo.list_all.return_value = [
            make_txn(TransactionType.INCOME, "2500.00", "Salary", "2026-05-01"),
            make_txn(TransactionType.INCOME, "150.25", "Freelance", "2026-05-03"),
            make_txn(TransactionType.EXPENSE, "40.00", "Food", "2026-05-04"),
        ]

        analyzer = Analyzer(repo)

        assert analyzer.category_totals(TransactionType.INCOME) == {
            "Salary": Decimal("2500.00"),
            "Freelance": Decimal("150.25"),
        }

    def test_category_totals_returns_empty_dict_on_empty_dataset(self) -> None:
        repo = MagicMock(spec=TransactionRepositoryInterface)
        repo.list_all.return_value = []

        analyzer = Analyzer(repo)

        assert analyzer.category_totals(TransactionType.EXPENSE) == {}


class TestHighestSpendingCategory:
    def test_highest_spending_category_returns_largest_expense_total(self) -> None:
        repo = MagicMock(spec=TransactionRepositoryInterface)
        repo.list_all.return_value = [
            make_txn(TransactionType.EXPENSE, "75.00", "Groceries", "2026-05-02"),
            make_txn(TransactionType.EXPENSE, "45.00", "Groceries", "2026-05-10"),
            make_txn(TransactionType.EXPENSE, "80.00", "Rent", "2026-05-01"),
            make_txn(TransactionType.INCOME, "2000.00", "Salary", "2026-05-01"),
        ]

        analyzer = Analyzer(repo)

        assert analyzer.highest_spending_category() == CategorySummary(
            category="Groceries", total=Decimal("120.00")
        )

    def test_highest_spending_category_returns_none_when_no_expenses_exist(self) -> None:
        repo = MagicMock(spec=TransactionRepositoryInterface)
        repo.list_all.return_value = [
            make_txn(TransactionType.INCOME, "2000.00", "Salary", "2026-05-01")
        ]

        analyzer = Analyzer(repo)

        assert analyzer.highest_spending_category() is None


class TestMonthlySummary:
    def test_monthly_summary_computes_income_expense_and_net_for_target_month(self) -> None:
        repo = MagicMock(spec=TransactionRepositoryInterface)
        repo.list_all.return_value = [
            make_txn(TransactionType.INCOME, "3000.00", "Salary", "2026-05-01"),
            make_txn(TransactionType.INCOME, "200.00", "Freelance", "2026-05-15"),
            make_txn(TransactionType.EXPENSE, "150.25", "Food", "2026-05-02"),
            make_txn(TransactionType.EXPENSE, "49.75", "Transport", "2026-05-03"),
            make_txn(TransactionType.EXPENSE, "500.00", "Rent", "2026-04-30"),
        ]

        analyzer = Analyzer(repo)

        assert analyzer.monthly_summary(2026, 5) == MonthlySummary(
            year=2026,
            month=5,
            total_income=Decimal("3200.00"),
            total_expenses=Decimal("200.00"),
            net=Decimal("3000.00"),
        )

    def test_monthly_summary_returns_zeroed_summary_when_month_has_no_data(self) -> None:
        repo = MagicMock(spec=TransactionRepositoryInterface)
        repo.list_all.return_value = [
            make_txn(TransactionType.EXPENSE, "50.00", "Food", "2026-05-01")
        ]

        analyzer = Analyzer(repo)

        assert analyzer.monthly_summary(2026, 6) == MonthlySummary(
            year=2026,
            month=6,
            total_income=Decimal("0"),
            total_expenses=Decimal("0"),
            net=Decimal("0"),
        )


class TestMonthlyTrends:
    def test_monthly_trends_returns_summaries_sorted_by_year_month(self) -> None:
        repo = MagicMock(spec=TransactionRepositoryInterface)
        repo.list_all.return_value = [
            make_txn(TransactionType.EXPENSE, "200.00", "Rent", "2026-05-01"),
            make_txn(TransactionType.INCOME, "1000.00", "Salary", "2026-04-01"),
            make_txn(TransactionType.EXPENSE, "150.00", "Food", "2026-04-10"),
            make_txn(TransactionType.INCOME, "1100.00", "Salary", "2026-05-15"),
            make_txn(TransactionType.EXPENSE, "75.00", "Food", "2025-12-20"),
        ]

        analyzer = Analyzer(repo)

        assert analyzer.monthly_trends() == [
            MonthlySummary(
                year=2025,
                month=12,
                total_income=Decimal("0"),
                total_expenses=Decimal("75.00"),
                net=Decimal("-75.00"),
            ),
            MonthlySummary(
                year=2026,
                month=4,
                total_income=Decimal("1000.00"),
                total_expenses=Decimal("150.00"),
                net=Decimal("850.00"),
            ),
            MonthlySummary(
                year=2026,
                month=5,
                total_income=Decimal("1100.00"),
                total_expenses=Decimal("200.00"),
                net=Decimal("900.00"),
            ),
        ]

    def test_monthly_trends_returns_empty_list_on_empty_dataset(self) -> None:
        repo = MagicMock(spec=TransactionRepositoryInterface)
        repo.list_all.return_value = []

        analyzer = Analyzer(repo)

        assert analyzer.monthly_trends() == []
