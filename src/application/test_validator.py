import pytest
from decimal import Decimal
from src.application.validator import Validator, ValidationError


def test_validate_transaction_type_valid():
    assert Validator.validate_transaction_type("income") == "income"


def test_validate_transaction_type_invalid():
    with pytest.raises(ValidationError):
        Validator.validate_transaction_type("invalid")


def test_validate_amount_valid():
    assert Validator.validate_amount("100.50") == Decimal("100.50")


def test_validate_amount_negative():
    with pytest.raises(ValidationError):
        Validator.validate_amount("-5")


def test_validate_amount_non_numeric():
    with pytest.raises(ValidationError):
        Validator.validate_amount("abc")


def test_validate_category_valid():
    assert Validator.validate_category("Food") == "Food"


def test_validate_category_empty():
    with pytest.raises(ValidationError):
        Validator.validate_category("")


def test_validate_description_valid():
    assert Validator.validate_description("Lunch") == "Lunch"


def test_validate_description_empty():
    with pytest.raises(ValidationError):
        Validator.validate_description("")


def test_validate_date_valid():
    assert Validator.validate_date("2026-05-17")


def test_validate_date_invalid():
    with pytest.raises(ValidationError):
        Validator.validate_date("17-05-2026")
