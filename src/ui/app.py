from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from flask import Flask, request, jsonify

from src.application.ledger import Ledger
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


def get_transaction_amount(txn):
    return Decimal(str(txn.amount))


def transaction_to_dict(txn):
    return {
        "id": str(txn.id),
        "type": get_transaction_type(txn),
        "amount": str(txn.amount),
        "category": txn.category,
        "description": txn.description,
        "date": str(txn.date),
    }


def compute_balance(transactions):
    income = Decimal("0.00")
    expenses = Decimal("0.00")

    for txn in transactions:
        txn_type = get_transaction_type(txn)
        amount = get_transaction_amount(txn)

        if txn_type == "income":
            income += amount
        elif txn_type == "expense":
            expenses += amount

    return {
        "income": f"{income:.2f}",
        "expenses": f"{expenses:.2f}",
        "balance": f"{income - expenses:.2f}",
    }


def get_year_month(txn):
    date_text = str(txn.date)
    year = int(date_text[0:4])
    month = int(date_text[5:7])
    return year, month


def compute_analytics(transactions):
    category_totals = defaultdict(Decimal)
    monthly_totals = defaultdict(lambda: {
        "income": Decimal("0.00"),
        "expenses": Decimal("0.00"),
    })

    for txn in transactions:
        txn_type = get_transaction_type(txn)
        amount = get_transaction_amount(txn)
        year, month = get_year_month(txn)

        if txn_type == "expense":
            category_totals[txn.category] += amount
            monthly_totals[(year, month)]["expenses"] += amount

        elif txn_type == "income":
            monthly_totals[(year, month)]["income"] += amount

    category_totals_response = {
        category: f"{amount:.2f}"
        for category, amount in category_totals.items()
    }

    highest_spending_category = None
    if category_totals:
        highest_spending_category = max(
            category_totals,
            key=lambda category: category_totals[category],
        )

    monthly_trends = []
    for (year, month), totals in sorted(monthly_totals.items()):
        income = totals["income"]
        expenses = totals["expenses"]

        monthly_trends.append({
            "year": year,
            "month": month,
            "income": f"{income:.2f}",
            "expenses": f"{expenses:.2f}",
            "net": f"{income - expenses:.2f}",
        })

    return {
        "category_totals": category_totals_response,
        "highest_spending_category": highest_spending_category,
        "monthly_trends": monthly_trends,
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

            return jsonify({
                "message": "Transaction added",
                "transaction": transaction_to_dict(txn),
            }), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/transactions", methods=["GET"])
    def get_transactions():
        repo.load()
        transactions = ledger.list_all()

        return jsonify([
            transaction_to_dict(txn)
            for txn in transactions
        ])

    @app.route("/delete/<txn_id>", methods=["DELETE"])
    def delete_transaction(txn_id):
        try:
            ledger.delete(UUID(txn_id))
            return jsonify({"message": "Deleted"}), 200

        except ValueError:
            return jsonify({"error": "Invalid transaction id"}), 400

        except Exception as e:
            return jsonify({"error": str(e)}), 404

    @app.route("/balance", methods=["GET"])
    def get_balance():
        repo.load()
        transactions = ledger.list_all()

        return jsonify(compute_balance(transactions))

    @app.route("/analytics", methods=["GET"])
    @app.route("/analyze", methods=["GET"])
    def get_analytics():
        repo.load()
        transactions = ledger.list_all()

        return jsonify(compute_analytics(transactions))

    return app


app = create_app()
