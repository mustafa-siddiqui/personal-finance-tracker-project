import pytest

from src.ui.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Personal Finance Tracker" in response.data


def test_add_transaction_success(client):
    response = client.post(
        "/add",
        json={
            "type": "expense",
            "amount": "100.00",
            "category": "food",
            "description": "Test food transaction",
            "date": "2026-06-11",
        },
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["message"] == "Transaction added"
    assert "transaction" in data
    assert "id" in data["transaction"]
    assert data["transaction"]["category"] == "food"


def test_add_transaction_missing_amount(client):
    response = client.post(
        "/add",
        json={
            "type": "expense",
            "category": "food",
            "description": "Missing amount test",
            "date": "2026-06-11",
        },
    )

    assert response.status_code == 400

    data = response.get_json()
    assert "error" in data


def test_get_transactions(client):
    response = client.get("/transactions")

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_delete_transaction(client):
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

    delete_data = delete_response.get_json()
    assert delete_data["message"] == "Deleted"
