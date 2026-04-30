"""Transaction dataclass and TransactionType enum."""

from __future__ import annotations

import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID


class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction:
    """Immutable record of a single financial transaction."""

    def __init__(
        self,
        id: UUID,
        type: TransactionType,
        amount: Decimal,
        category: str,
        description: str,
        date: datetime.date,
    ) -> None:
        self.id = id
        self.type = type
        self.amount = amount
        self.category = category
        self.description = description
        self.date = date

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"Transaction(id={self.id!r}, type={self.type!r}, "
            f"amount={self.amount!r}, category={self.category!r}, "
            f"description={self.description!r}, date={self.date!r})"
        )
