from pathlib import Path
from uuid import UUID

from flask import Flask, request, jsonify

from src.application.analyzer import Analyzer
from src.application.balance_calculator import BalanceCalculator
from src.application.ledger import Ledger
from src.domain.transaction import TransactionType
from src.domain.validator import Validator
from src.repository.json_transaction_repository import JsonTransactionRepository


ALLOWED_CATEGORIES = [
    "salary",
    "freelance",
    "food",
    "transportation",
    "housing",
    "utilities",
    "entertainment",
    "healthcare",
    "education",
    "other",
]

DATA_PATH = Path("data") / "transactions.json"


def get_transaction_type(txn):
    return txn.type.value if hasattr(txn.type, "value") else str(txn.type)


def transaction_to_dict(txn):
    return {
        "id": str(txn.id),
        "type": get_transaction_type(txn),
        "amount": str(txn.amount),
        "category": txn.category,
        "description": txn.description,
        "date": str(txn.date),
    }


def monthly_summary_to_dict(summary):
    return {
        "year": summary.year,
        "month": summary.month,
        "total_income": str(summary.total_income),
        "total_expenses": str(summary.total_expenses),
        "net": str(summary.net),
    }


def create_app(data_path=DATA_PATH):
    app = Flask(__name__)

    data_path = Path(data_path)
    data_path.parent.mkdir(parents=True, exist_ok=True)

    validator = Validator(allowed_categories=ALLOWED_CATEGORIES)

    repo = JsonTransactionRepository(path=data_path)
    repo.load()

    ledger = Ledger(repo=repo, validator=validator)

    @app.route("/")
    def home():
        return "Personal Finance Tracker"

    @app.route("/add", methods=["POST"])
    def add_transaction():
        data = request.get_json(silent=True) or {}

        required_fields = ["type", "amount", "category", "description", "date"]

        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        try:
            txn = ledger.record(
                type=data["type"],
                amount=data["amount"],
                category=data["category"],
                description=data["description"],
                date=data["date"],
            )

            return jsonify(
                {
                    "message": "Transaction added",
                    "transaction": transaction_to_dict(txn),
                }
            ), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/transactions", methods=["GET"])
    def get_transactions():
        repo.load()
        transactions = ledger.list_all()

        return jsonify([transaction_to_dict(txn) for txn in transactions])

    @app.route("/delete/<txn_id>", methods=["DELETE"])
    def delete_transaction(txn_id):
        try:
            repo.load()
            ledger.delete(UUID(txn_id))

            return jsonify({"message": "Deleted"}), 200

        except ValueError:
            return jsonify({"error": "Invalid transaction id"}), 400

        except Exception as e:
            return jsonify({"error": str(e)}), 404

    @app.route("/balance", methods=["GET"])
    def get_balance():
        repo.load()
        balance = BalanceCalculator.calculate(repo.list_all())

        return jsonify({"balance": str(balance)})

    @app.route("/analytics", methods=["GET"])
    @app.route("/analyze", methods=["GET"])
    def get_analytics():
        repo.load()

        analyzer = Analyzer(repo=repo)

        category_totals = analyzer.category_totals(TransactionType.EXPENSE)
        highest_spending = analyzer.highest_spending_category()
        monthly_trends = analyzer.monthly_trends()

        highest_spending_response = None
        if highest_spending is not None:
            highest_spending_response = {
                "category": highest_spending.category,
                "total": str(highest_spending.total),
            }

        return jsonify(
            {
                "category_totals": {
                    category: str(total)
                    for category, total in category_totals.items()
                },
                "highest_spending_category": highest_spending_response,
                "monthly_trends": [
                    monthly_summary_to_dict(summary)
                    for summary in monthly_trends
                ],
            }
        )

    @app.route("/analytics/monthly-summary", methods=["GET"])
    def get_monthly_summary():
        repo.load()

        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)

        if year is None or month is None:
            return jsonify({"error": "year and month are required"}), 400

        analyzer = Analyzer(repo=repo)
        summary = analyzer.monthly_summary(year, month)

        return jsonify(monthly_summary_to_dict(summary))

    return app


app = create_app()
