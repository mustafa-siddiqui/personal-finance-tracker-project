"""Custom exception hierarchy for the finance tracker."""

from uuid import UUID


class FinanceTrackerError(Exception):
    """Base exception for all finance tracker errors."""


class ValidationError(FinanceTrackerError):
    """Raised when input fails validation rules."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"Validation error on '{field}': {message}")


class TransactionNotFound(FinanceTrackerError):
    """Raised when a transaction ID does not exist in the store."""

    def __init__(self, transaction_id: UUID) -> None:
        self.transaction_id = transaction_id
        super().__init__(f"Transaction not found: {transaction_id}")


class PersistenceError(FinanceTrackerError):
    """Raised when file I/O fails or stored data is malformed."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class UnsupportedSchemaVersion(FinanceTrackerError):
    """Raised when the JSON file has an unrecognized schema_version."""

    def __init__(self, found_version: int, expected_version: int) -> None:
        self.found_version = found_version
        self.expected_version = expected_version
        super().__init__(
            f"Unsupported schema version: found {found_version}, expected {expected_version}"
        )
