from src.ui.app import app


def test_add_and_get_transaction_integration():

    client = app.test_client()

    # Step 1: Add transaction through Flask API
    response = client.post(
        "/add",
        json={
            "type": "expense",
            "category": "Food",
            "amount": 25
        }
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "Transaction added"


    # Step 2: Retrieve transactions
    response = client.get("/transactions")

    assert response.status_code == 200

    transactions = response.get_json()

    assert len(transactions) > 0
    assert transactions[0]["category"] == "Food"
    assert transactions[0]["amount"] == 25



def test_delete_transaction_integration():

    client = app.test_client()


    # Add transaction first
    client.post(
        "/add",
        json={
            "type": "expense",
            "category": "Travel",
            "amount": 50
        }
    )


    # Delete first transaction
    response = client.delete("/delete/0")

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Deleted"
