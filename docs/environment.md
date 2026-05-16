# Development & Test Environment

This document captures the software (with versions) used to develop and test the Personal Finance Tracker, and the steps to reproduce that environment on a new machine.

## Software Used

### Application development

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.8.10 | Implementation language |
| Flask | 3.0.3 | Web framework for the UI layer (F7) |
| pip | 20.0.2 | Package manager |

### Testing

| Software | Version | Purpose |
|----------|---------|---------|
| pytest | 8.3.5 | Test runner and assertion framework |
| pytest-mock | 3.14.1 | Mocking helper used in unit tests |

### Standard library modules used

`uuid`, `decimal`, `datetime`, `json`, `os`, `pathlib`, `typing`, `enum`, `abc`, `unittest.mock` — all from the Python 3.8 standard library, no version pinning required.

### Operating system used during development

| OS | Version |
|----|---------|
| Linux | 6.6.87.2-microsoft-standard-WSL2 (Ubuntu 20.04) |

The test suite is OS-agnostic — `pytest`'s `tmp_path` fixture handles per-test temporary directories portably. Tests should pass on any Linux, macOS, or Windows machine running Python 3.8 or newer.

## Setup Instructions

### Prerequisites

- Python 3.8 or newer
- `git` for cloning the repository

### One-time setup

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

### Running the test suite

With the virtual environment activated:

```bash
# Run all unit tests
make test

# Run tests for a single unit with verbose output
pytest src/domain/test_transaction.py -v
```

`pytest.ini` configures discovery: pytest looks for `test_*.py` files inside `src/` (unit tests, colocated with code) and `tests/` (integration / end-to-end tests).

### Adding a new dependency

```bash
pip install <package-name>
pip freeze > requirements.txt
git add requirements.txt
```

Commit `requirements.txt` so other developers receive the same versions on their next install.
