from flask import Flask, request, jsonify

app = Flask(__name__)

transactions = []


@app.route("/")
def home():
    return "Personal Finance Tracker"


@app.route("/add", methods=["POST"])
def add_transaction():

    data = request.json

    if "amount" not in data:
        return jsonify({"error": "Amount is required"}), 400

    transactions.append(data)

    return jsonify({"message": "Transaction added"}), 201


@app.route("/transactions")
def get_transactions():
    return jsonify(transactions)


@app.route("/delete/<int:index>", methods=["DELETE"])
def delete_transaction(index):

    if index >= len(transactions):
        return jsonify({"error": "Transaction not found"}), 404

    transactions.pop(index)

    return jsonify({"message": "Deleted"})
