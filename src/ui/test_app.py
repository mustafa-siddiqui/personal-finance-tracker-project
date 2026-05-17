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


def test_add_transaction_success(client):

    response = client.post(
        "/add",
        json={
            "amount": 100,
            "category": "Food"
        }
    )

    assert response.status_code == 201


def test_add_transaction_missing_amount(client):

    response = client.post(
        "/add",
        json={
            "category": "Food"
        }
    )

    assert response.status_code == 400


def test_get_transactions(client):

    response = client.get("/transactions")

    assert response.status_code == 200


def test_delete_transaction(client):

    client.post(
        "/add",
        json={
            "amount": 50,
            "category": "Transport"
        }
    )

    response = client.delete("/delete/0")

    assert response.status_code == 200
