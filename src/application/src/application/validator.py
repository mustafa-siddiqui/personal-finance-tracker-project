from decimal import Decimal, InvalidOperation
from datetime import datetime


class ValidationError(Exception):
    pass


class Validator:

    VALID_TRANSACTION_TYPES = ["income", "expense"]

    @staticmethod
    def validate_transaction_type(transaction_type: str):
        if not transaction_type:
            raise ValidationError("Transaction type is required.")

        transaction_type = transaction_type.lower().strip()

        if transaction_type not in Validator.VALID_TRANSACTION_TYPES:
            raise ValidationError("Invalid transaction type.")

        return transaction_type

    @staticmethod
    def validate_amount(amount: str):
        try:
            value = Decimal(amount)

            if value <= 0:
                raise ValidationError("Amount must be greater than zero.")

            return value

        except (InvalidOperation, ValueError):
            raise ValidationError("Invalid amount.")

    @staticmethod
    def validate_category(category: str):
        if not category or not category.strip():
            raise ValidationError("Category is required.")

        return category.strip()

    @staticmethod
    def validate_description(description: str):
        if not description or not description.strip():
            raise ValidationError("Description is required.")

        return description.strip()

    @staticmethod
    def validate_date(date_str: str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Invalid date format.")
