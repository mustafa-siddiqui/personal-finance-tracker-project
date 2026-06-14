import pytest

from src.ui.app import create_app


@pytest.fixture
def client(tmp_path):
    test_data_path = tmp_path / "transactions.json"

    app = create_app(data_path=test_data_path)
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def valid_expense(description="Test food transaction"):
    return {
        "type": "expense",
        "amount": "100.00",
        "category": "food",
        "description": description,
        "date": "2026-06-11",
    }


def valid_income(description="Test salary transaction"):
    return {
        "type": "income",
        "amount": "500.00",
        "category": "salary",
        "description": description,
        "date": "2026-06-11",
    }


def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Personal Finance Tracker" in response.data


def test_add_transaction_success(client):
    response = client.post("/add", json=valid_expense())

    assert response.status_code == 201

    data = response.get_json()
    assert data["message"] == "Transaction added"
    assert "transaction" in data
    assert "id" in data["transaction"]
    assert data["transaction"]["category"] == "food"


def test_add_transaction_missing_amount(client):
    bad_transaction = valid_expense()
    del bad_transaction["amount"]

    response = client.post("/add", json=bad_transaction)

    assert response.status_code == 400

    data = response.get_json()
    assert "error" in data


def test_get_transactions_returns_saved_transactions(client):
    client.post("/add", json=valid_expense(description="Groceries test"))

    response = client.get("/transactions")

    assert response.status_code == 200

    data = response.get_json()
    assert isinstance(data, list)
    assert any(txn["description"] == "Groceries test" for txn in data)


def test_delete_transaction_by_uuid(client):
    add_response = client.post(
        "/add",
        json={
            "type": "expense",
            "amount": "50.00",
            "category": "transportation",
            "description": "Delete test transaction",
            "date": "2026-06-11",
        },
    )

    assert add_response.status_code == 201

    added_data = add_response.get_json()
    transaction_id = added_data["transaction"]["id"]

    delete_response = client.delete(f"/delete/{transaction_id}")

    assert delete_response.status_code == 200

    transactions_response = client.get("/transactions")
    transactions = transactions_response.get_json()

    assert all(txn["id"] != transaction_id for txn in transactions)


def test_delete_transaction_invalid_uuid(client):
    response = client.delete("/delete/not-a-valid-uuid")

    assert response.status_code == 400

    data = response.get_json()
    assert "error" in data


def test_balance_endpoint_uses_backend_calculator(client):
    client.post("/add", json=valid_income())
    client.post("/add", json=valid_expense())

    response = client.get("/balance")

    assert response.status_code == 200

    data = response.get_json()
    assert data["balance"] == "400.00"


def test_analytics_endpoint_uses_backend_analyzer(client):
    client.post("/add", json=valid_income())
    client.post("/add", json=valid_expense())

    response = client.get("/analytics")

    assert response.status_code == 200

    data = response.get_json()

    assert "category_totals" in data
    assert "highest_spending_category" in data
    assert "monthly_trends" in data

    assert data["category_totals"]["food"] == "100.00"
    assert data["highest_spending_category"]["category"] == "food"
    assert data["highest_spending_category"]["total"] == "100.00"

    assert len(data["monthly_trends"]) == 1
    assert data["monthly_trends"][0]["year"] == 2026
    assert data["monthly_trends"][0]["month"] == 6
    assert data["monthly_trends"][0]["total_income"] == "500.00"
    assert data["monthly_trends"][0]["total_expenses"] == "100.00"
    assert data["monthly_trends"][0]["net"] == "400.00"


def test_monthly_summary_endpoint(client):
    client.post("/add", json=valid_income())
    client.post("/add", json=valid_expense())

    response = client.get("/analytics/monthly-summary?year=2026&month=6")

    assert response.status_code == 200

    data = response.get_json()
    assert data["year"] == 2026
    assert data["month"] == 6
    assert data["total_income"] == "500.00"
    assert data["total_expenses"] == "100.00"
    assert data["net"] == "400.00"


def test_monthly_summary_missing_query_params(client):
    response = client.get("/analytics/monthly-summary")

    assert response.status_code == 400

    data = response.get_json()
    assert "error" in data
