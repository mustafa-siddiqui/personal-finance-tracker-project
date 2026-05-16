# Personal Finance Tracker

A standalone Python application for recording income and expenses, categorizing spending, and calculating account balances. Built for a Software Verification and Testing course — the architecture prioritizes testability.

## Documentation

- [Design Document](docs/design.md) — architecture, class diagrams, JSON schema, and design decisions

## Setup

### Prerequisites

- Python 3.8 or newer

### Installation

```bash
git clone <repo-url>
cd personal-finance-tracker-project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the venv with `.venv\Scripts\activate` instead.

### Running tests

With the venv activated:

```bash
pytest
```

### Adding dependencies

With the venv activated:

```bash
pip install <package-name>
pip freeze > requirements.txt
```

Commit `requirements.txt` after adding dependencies.

## Team

| Team Member | Role |
|-------------|------|
| Mustafa Siddiqui | Backend Architect & Developer |
| Owais Adil Mohammed | Core Backend Developer |
| Anas Rais Lnu | Security & UI Specialist |
| Mohd Karim Siddiqui | Reporting & Analytics Developer |
