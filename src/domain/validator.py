"""Validator — input validation for transaction fields (F6)."""

from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation
from typing import List
from uuid import UUID

from src.domain.exceptions import ValidationError
from src.domain.transaction import TransactionType


class Validator:
    def __init__(self, allowed_categories: List[str]) -> None:
        self._allowed_categories = allowed_categories

    def validate_id(self, value: str) -> UUID:
        if not isinstance(value, str):
            raise ValidationError(field="id", message="must be a string")
        try:
            return UUID(value)
        except (ValueError, TypeError) as e:
            raise ValidationError(field="id", message=f"not a valid UUID: {e}") from e

    def validate_amount(self, value: str) -> Decimal:
        if not isinstance(value, str):
            raise ValidationError(field="amount", message="must be a string")
        if value.strip() == "":
            raise ValidationError(field="amount", message="must not be empty")
        try:
            amount = Decimal(value)
        except (InvalidOperation, ValueError) as e:
            raise ValidationError(
                field="amount", message=f"not a valid decimal: {e}"
            ) from e
        if not amount.is_finite():
            raise ValidationError(field="amount", message="must be a finite number")
        if amount <= 0:
            raise ValidationError(field="amount", message="must be greater than zero")
        return amount

    def validate_category(self, value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError(field="category", message="must be a string")
        category = value.strip()
        if category == "":
            raise ValidationError(field="category", message="must not be empty")
        if category not in self._allowed_categories:
            raise ValidationError(
                field="category",
                message=f"'{category}' is not in the allowed category list",
            )
        return category

    def validate_description(self, value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError(field="description", message="must be a string")
        description = value.strip()
        if description == "":
            raise ValidationError(field="description", message="must not be empty")
        return description

    def validate_date(self, value: str) -> datetime.date:
        if not isinstance(value, str):
            raise ValidationError(field="date", message="must be a string")
        try:
            return datetime.date.fromisoformat(value)
        except ValueError as e:
            raise ValidationError(
                field="date", message=f"must be in YYYY-MM-DD format: {e}"
            ) from e

    def validate_type(self, value: str) -> TransactionType:
        if not isinstance(value, str):
            raise ValidationError(field="type", message="must be a string")
        try:
            return TransactionType(value)
        except ValueError as e:
            raise ValidationError(
                field="type",
                message=f"must be 'income' or 'expense', got '{value}'",
            ) from e
