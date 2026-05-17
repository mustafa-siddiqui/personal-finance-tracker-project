"""Analyzer — spending summaries, category totals, and monthly trends (F8)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from src.domain.transaction import TransactionType
from src.repository.transaction_repository_interface import TransactionRepositoryInterface


@dataclass(frozen=True)
class CategorySummary:
    """Aggregate total for a single category."""

    category: str
    total: Decimal


@dataclass(frozen=True)
class MonthlySummary:
    """Income/expense totals for a single calendar month."""

    year: int
    month: int
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal


class Analyzer:
    """Read-only analytics service over all recorded transactions."""

    def __init__(self, repo: TransactionRepositoryInterface) -> None:
        self._repo = repo

    def category_totals(self, type: TransactionType) -> Dict[str, Decimal]:
        totals: Dict[str, Decimal] = {}
        for txn in self._repo.list_all():
            if txn.type is not type:
                continue
            totals[txn.category] = totals.get(txn.category, Decimal("0")) + txn.amount
        return totals

    def highest_spending_category(self) -> Optional[CategorySummary]:
        totals = self.category_totals(TransactionType.EXPENSE)
        if not totals:
            return None

        category, total = max(
            totals.items(),
            key=lambda item: (item[1], item[0]),  # deterministic tie-break
        )
        return CategorySummary(category=category, total=total)

    def monthly_summary(self, year: int, month: int) -> MonthlySummary:
        total_income = Decimal("0")
        total_expenses = Decimal("0")

        for txn in self._repo.list_all():
            if txn.date.year != year or txn.date.month != month:
                continue
            if txn.type is TransactionType.INCOME:
                total_income += txn.amount
            elif txn.type is TransactionType.EXPENSE:
                total_expenses += txn.amount

        return MonthlySummary(
            year=year,
            month=month,
            total_income=total_income,
            total_expenses=total_expenses,
            net=total_income - total_expenses,
        )

    def monthly_trends(self) -> List[MonthlySummary]:
        grouped: Dict[Tuple[int, int], Dict[str, Decimal]] = {}

        for txn in self._repo.list_all():
            key = (txn.date.year, txn.date.month)
            bucket = grouped.setdefault(
                key,
                {"income": Decimal("0"), "expense": Decimal("0")},
            )
            if txn.type is TransactionType.INCOME:
                bucket["income"] += txn.amount
            elif txn.type is TransactionType.EXPENSE:
                bucket["expense"] += txn.amount

        summaries: List[MonthlySummary] = []
        for year, month in sorted(grouped.keys()):
            income = grouped[(year, month)]["income"]
            expense = grouped[(year, month)]["expense"]
            summaries.append(
                MonthlySummary(
                    year=year,
                    month=month,
                    total_income=income,
                    total_expenses=expense,
                    net=income - expense,
                )
            )
        return summaries
