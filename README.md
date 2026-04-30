# Personal Finance Tracker

A standalone Python application for recording income and expenses, categorizing spending, and calculating account balances. Built for a Software Verification and Testing course — the architecture prioritizes testability.

## Documentation

- [Design Document](docs/design.md) — architecture, class diagrams, JSON schema, and design decisions

## Setup

### Prerequisites

- Python 3.8+
- [pipenv](https://pipenv.pypa.io/)

### Installation

```bash
git clone <repo-url>
cd personal-finance-tracker-project
pipenv install --dev
```

This creates a virtual environment and installs all production and dev dependencies.

### Running tests

```bash
pipenv run pytest
```

Or activate the shell first:

```bash
pipenv shell
pytest
```

### Adding dependencies

```bash
# Production dependency
pipenv install <package-name>

# Dev-only dependency
pipenv install --dev <package-name>
```

Commit both `Pipfile` and `Pipfile.lock` after adding dependencies.

## Team

| Team Member | Role |
|-------------|------|
| Mustafa Siddiqui | Backend Architect & Developer |
| Owais Adil Mohammed | Core Backend Developer |
| Anas Rais Lnu | Security & UI Specialist |
| Mohd Karim Siddiqui | Reporting & Analytics Developer |
