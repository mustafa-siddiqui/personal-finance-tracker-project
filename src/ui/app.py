from pathlib import Path

from flask import Flask, request, jsonify

from src.application.ledger import Ledger
from src.domain.validator import Validator
from src.repository.json_transaction_repository import JsonTransactionRepository

app = Flask(__name__)

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

validator = Validator(allowed_categories=ALLOWED_CATEGORIES)

repo = JsonTransactionRepository(path=DATA_PATH)
repo.load()

ledger = Ledger(repo=repo, validator=validator)


@app.route("/")
def home():
    return "Personal Finance Tracker"


@app.route("/add", methods=["POST"])
def add_transaction():
    data = request.json

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
            "id": str(txn.id),
        }), 201

    except KeyError as e:
        return jsonify({"error": f"Missing field: {e.args[0]}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/transactions")
def get_transactions():
    return jsonify(transactions)


@app.route("/delete/<int:index>", methods=["DELETE"])
def delete_transaction(index):

    if index >= len(transactions):
        return jsonify({"error": "Transaction not found"}), 404

    transactions.pop(index)

    return jsonify({"message": "Deleted"})
