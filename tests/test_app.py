from app import create_app, db


def make_client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "SECRET_KEY": "test"})
    return app.test_client()


def test_health_endpoint():
    client = make_client()
    response = client.get("/api/health")
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["success"] is True


def test_products_seeded():
    client = make_client()
    response = client.get("/api/products")
    payload = response.get_json()
    assert response.status_code == 200
    assert len(payload["products"]) >= 6
    assert "Mobiles" in payload["categories"]


def test_cart_add_and_checkout_order():
    client = make_client()
    product = client.get("/api/products").get_json()["products"][0]
    cart_response = client.post("/api/cart", json={"productId": product["id"], "quantity": 2})
    cart = cart_response.get_json()["cart"]
    assert cart_response.status_code == 200
    assert cart["count"] == 2
    assert cart["total"] > 0

    order_response = client.post(
        "/api/orders",
        json={
            "customerName": "Test Buyer",
            "email": "buyer@example.com",
            "phone": "9999999999",
            "address": "Test address, Hyderabad",
        },
    )
    order = order_response.get_json()["order"]
    assert order_response.status_code == 201
    assert order["status"] == "Placed"
    assert order["items"][0]["quantity"] == 2


def test_create_product_validation():
    client = make_client()
    response = client.post("/api/products", json={})
    assert response.status_code == 400
    assert response.get_json()["success"] is False
