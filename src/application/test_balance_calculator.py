import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from src.application.balance_calculator import BalanceCalculator
from src.domain.exceptions import ValidationError
from src.domain.transaction import Transaction, TransactionType


def make_transaction(transaction_type, amount):
    return Transaction(
        id=uuid4(),
        type=transaction_type,
        amount=Decimal(amount),
        category="general",
        description="test transaction",
        date=datetime.date(2026, 1, 1),
    )


def test_calculate_returns_zero_for_empty_dataset():
    assert BalanceCalculator.calculate([]) == Decimal("0")


def test_calculate_income_minus_expenses():
    transactions = [
        make_transaction(TransactionType.INCOME, "1000.00"),
        make_transaction(TransactionType.EXPENSE, "250.25"),
        make_transaction(TransactionType.EXPENSE, "100.75"),
    ]

    assert BalanceCalculator.calculate(transactions) == Decimal("649.00")


def test_calculate_can_return_negative_balance():
    transactions = [
        make_transaction(TransactionType.INCOME, "100.00"),
        make_transaction(TransactionType.EXPENSE, "150.00"),
    ]

    assert BalanceCalculator.calculate(transactions) == Decimal("-50.00")


def test_calculate_handles_large_values_exactly():
    transactions = [
        make_transaction(TransactionType.INCOME, "999999999999999999999.99"),
        make_transaction(TransactionType.EXPENSE, "0.99"),
    ]

    assert BalanceCalculator.calculate(transactions) == Decimal("999999999999999999999.00")


def test_calculate_rejects_none_collection():
    with pytest.raises(ValidationError):
        BalanceCalculator.calculate(None)


def test_calculate_rejects_invalid_transaction_item():
    with pytest.raises(ValidationError):
        BalanceCalculator.calculate(["not-a-transaction"])


def test_calculate_rejects_invalid_amount():
    txn = make_transaction(TransactionType.INCOME, "100.00")
    txn.amount = Decimal("-1.00")

    with pytest.raises(ValidationError):
        BalanceCalculator.calculate([txn])
