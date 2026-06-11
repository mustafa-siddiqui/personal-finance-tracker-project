from src.ui.app import app, transactions


def test_add_and_get_transaction_integration():

    client = app.test_client()

    # 🔥 RESET STATE (IMPORTANT)
    transactions.clear()

    # Step 1: Add transaction
    response = client.post(
        "/add",
        json={
            "type": "expense",
            "category": "Food",
            "amount": 25
        }
    )

    assert response.status_code == 201

    # Step 2: Get transactions
    response = client.get("/transactions")

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 1
    assert data[0]["category"] == "Food"
    assert data[0]["amount"] == 25



def test_delete_transaction_integration():

    client = app.test_client()

    transactions.clear()

    client.post(
        "/add",
        json={
            "type": "expense",
            "category": "Travel",
            "amount": 50
        }
    )

    response = client.delete("/delete/0")

    assert response.status_code == 200
    assert response.get_json()["message"] == "Deleted"
