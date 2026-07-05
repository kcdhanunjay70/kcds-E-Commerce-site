import os
from datetime import datetime, timezone
from uuid import uuid4

from bson import ObjectId
from flask import Flask, jsonify, render_template, request, session
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError


DEFAULT_PRODUCTS = [
    {"sku": "KC-PHN-001", "name": "Nova X5 Smartphone", "category": "Mobiles", "price": 18999, "stock": 24, "rating": 4.6, "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=900&q=80", "description": "AMOLED display, 5G performance, 128GB storage and all-day battery for students and professionals.", "featured": True},
    {"sku": "KC-LAP-014", "name": "KCDS ProBook 14", "category": "Laptops", "price": 57999, "stock": 12, "rating": 4.7, "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80", "description": "Lightweight laptop with fast SSD, long battery life and excellent coding performance.", "featured": True},
    {"sku": "KC-AUD-202", "name": "Pulse Wireless Headphones", "category": "Audio", "price": 2499, "stock": 48, "rating": 4.4, "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80", "description": "Deep bass, noise isolation and 40-hour battery for classes, travel and gaming.", "featured": False},
    {"sku": "KC-WCH-330", "name": "FitTrack Smart Watch", "category": "Wearables", "price": 3999, "stock": 31, "rating": 4.3, "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80", "description": "Fitness tracking, notifications, heart-rate monitoring and premium metal body.", "featured": True},
    {"sku": "KC-BAG-510", "name": "Urban Laptop Backpack", "category": "Accessories", "price": 1599, "stock": 60, "rating": 4.5, "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80", "description": "Water-resistant backpack with laptop sleeve, organizer pockets and travel-ready comfort.", "featured": False},
    {"sku": "KC-TAB-112", "name": "StudyTab 10", "category": "Tablets", "price": 14999, "stock": 19, "rating": 4.2, "image": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=900&q=80", "description": "10-inch tablet for notes, streaming, online classes and light productivity.", "featured": False},
]


def clean(value, max_length=500):
    return str(value or "").strip()[:max_length]


def digits(value):
    return "".join(char for char in str(value or "") if char.isdigit())


def public_product(row):
    item = dict(row)
    item["id"] = str(item.pop("_id"))
    item.pop("created_at", None)
    return item


def public_order(row):
    item = dict(row)
    item["id"] = str(item.pop("_id"))
    item["orderNo"] = item.pop("order_no")
    item["customerName"] = item.pop("customer_name")
    created_at = item.pop("created_at", None)
    item["createdAt"] = created_at.isoformat() if created_at else ""
    for order_item in item["items"]:
        order_item["productId"] = str(order_item.pop("product_id"))
        order_item["productName"] = order_item.pop("product_name")
        order_item["unitPrice"] = order_item.pop("unit_price")
        order_item["lineTotal"] = order_item.pop("line_total")
    return item


def validate_product(payload):
    name = clean(payload.get("name"), 120)
    sku = clean(payload.get("sku"), 40).upper()
    category = clean(payload.get("category"), 60)
    description = clean(payload.get("description"), 800)
    image = clean(payload.get("image"), 500) or "https://images.unsplash.com/photo-1607083206968-13611e3d76db?auto=format&fit=crop&w=900&q=80"
    try:
        price = int(float(payload.get("price")))
        stock = int(float(payload.get("stock")))
        rating = float(payload.get("rating") or 4.0)
    except (TypeError, ValueError) as exc:
        raise ValueError("Price, stock and rating must be valid numbers") from exc
    if not all([name, sku, category, description]):
        raise ValueError("Name, SKU, category and description are required")
    if not 1 <= price <= 1000000:
        raise ValueError("Price must be between 1 and 1000000")
    if not 0 <= stock <= 10000:
        raise ValueError("Stock must be between 0 and 10000")
    if not 1 <= rating <= 5:
        raise ValueError("Rating must be between 1 and 5")
    return {"name": name, "sku": sku, "category": category, "description": description, "image": image, "price": price, "stock": stock, "rating": rating, "featured": bool(payload.get("featured")), "created_at": datetime.now(timezone.utc)}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-change-me"),
        MONGO_URI=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        MONGO_DB_NAME=os.getenv("MONGO_DB_NAME", "kcds_ecommerce"),
        JSON_SORT_KEYS=False,
    )
    if test_config:
        app.config.update(test_config)

    mongo_client = app.config.get("MONGO_CLIENT") or MongoClient(app.config["MONGO_URI"], serverSelectionTimeoutMS=3000)
    database = mongo_client[app.config["MONGO_DB_NAME"]]
    products_collection = database.products
    orders_collection = database.orders
    initialized = False

    def initialize_database():
        nonlocal initialized
        if initialized:
            return
        products_collection.create_index([("sku", ASCENDING)], unique=True)
        orders_collection.create_index([("order_no", ASCENDING)], unique=True)
        orders_collection.create_index([("created_at", DESCENDING)])
        if products_collection.count_documents({}) == 0:
            products_collection.insert_many([{**item, "created_at": datetime.now(timezone.utc)} for item in DEFAULT_PRODUCTS])
        initialized = True

    @app.before_request
    def ensure_database():
        initialize_database()

    def parse_product_id(value):
        try:
            return ObjectId(str(value))
        except Exception:
            return None

    def money_parts(cart_items):
        subtotal = sum(item["lineTotal"] for item in cart_items)
        shipping = 0 if subtotal >= 20000 or subtotal == 0 else 99
        tax = round(subtotal * 0.05)
        return {"subtotal": subtotal, "shipping": shipping, "tax": tax, "total": subtotal + shipping + tax}

    def get_cart():
        return {str(key): int(value) for key, value in session.setdefault("cart", {}).items()}

    def save_cart(cart):
        session["cart"] = {str(key): int(value) for key, value in cart.items() if int(value) > 0}
        session.modified = True

    def cart_details():
        items = []
        for product_id, quantity in get_cart().items():
            object_id = parse_product_id(product_id)
            product = products_collection.find_one({"_id": object_id}) if object_id else None
            if not product:
                continue
            safe_quantity = min(quantity, product["stock"])
            product_data = public_product(product)
            items.append({"product": product_data, "quantity": safe_quantity, "lineTotal": product["price"] * safe_quantity})
        totals = money_parts(items)
        return {"items": items, **totals, "count": sum(item["quantity"] for item in items)}

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        mongo_client.admin.command("ping")
        return jsonify({"success": True, "status": "ok", "database": "mongodb"})

    @app.get("/api/products")
    def products():
        query = clean(request.args.get("q"), 120)
        category = clean(request.args.get("category"), 80)
        mongo_query = {}
        if category:
            mongo_query["category"] = category
        if query:
            mongo_query["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"category": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
            ]
        rows = products_collection.find(mongo_query).sort([("featured", DESCENDING), ("name", ASCENDING)])
        categories = sorted(products_collection.distinct("category"))
        return jsonify({"success": True, "products": [public_product(row) for row in rows], "categories": categories})

    @app.post("/api/products")
    def products_create():
        try:
            product = validate_product(request.get_json(silent=True) or {})
            product_id = products_collection.insert_one(product).inserted_id
            return jsonify({"success": True, "product": public_product(products_collection.find_one({"_id": product_id}))}), 201
        except ValueError as exc:
            return jsonify({"success": False, "message": str(exc)}), 400
        except DuplicateKeyError:
            return jsonify({"success": False, "message": "SKU already exists"}), 409

    @app.get("/api/cart")
    def cart():
        return jsonify({"success": True, "cart": cart_details()})

    @app.post("/api/cart")
    def cart_add():
        payload = request.get_json(silent=True) or {}
        product_id = parse_product_id(payload.get("productId"))
        try:
            quantity = int(payload.get("quantity") or 1)
        except (TypeError, ValueError):
            quantity = 0
        product = products_collection.find_one({"_id": product_id}) if product_id else None
        if not product:
            return jsonify({"success": False, "message": "Product not found"}), 404
        if quantity < 1:
            return jsonify({"success": False, "message": "Quantity must be at least 1"}), 400
        cart_data = get_cart()
        key = str(product_id)
        cart_data[key] = min(product["stock"], cart_data.get(key, 0) + quantity)
        save_cart(cart_data)
        return jsonify({"success": True, "cart": cart_details()})

    @app.patch("/api/cart/<product_id>")
    def cart_update(product_id):
        object_id = parse_product_id(product_id)
        try:
            quantity = int((request.get_json(silent=True) or {}).get("quantity") or 0)
        except (TypeError, ValueError):
            quantity = 0
        cart_data = get_cart()
        if quantity <= 0:
            cart_data.pop(product_id, None)
        else:
            product = products_collection.find_one({"_id": object_id}) if object_id else None
            if not product:
                return jsonify({"success": False, "message": "Product not found"}), 404
            cart_data[product_id] = min(product["stock"], quantity)
        save_cart(cart_data)
        return jsonify({"success": True, "cart": cart_details()})

    @app.delete("/api/cart")
    def cart_clear():
        save_cart({})
        return jsonify({"success": True, "cart": cart_details()})

    @app.post("/api/orders")
    def orders_create():
        payload = request.get_json(silent=True) or {}
        details = cart_details()
        if not details["items"]:
            return jsonify({"success": False, "message": "Cart is empty"}), 400
        customer_name = clean(payload.get("customerName"), 100)
        email = clean(payload.get("email"), 140)
        phone = digits(payload.get("phone"))[:10]
        address = clean(payload.get("address"), 800)
        if not customer_name or not email or len(phone) != 10 or not address:
            return jsonify({"success": False, "message": "Customer name, email, 10 digit phone and address are required"}), 400

        order_items = []
        updated = []
        for item in details["items"]:
            product_id = ObjectId(item["product"]["id"])
            product = products_collection.find_one_and_update(
                {"_id": product_id, "stock": {"$gte": item["quantity"]}},
                {"$inc": {"stock": -item["quantity"]}},
                return_document=ReturnDocument.AFTER,
            )
            if not product:
                for rollback_id, rollback_quantity in updated:
                    products_collection.update_one({"_id": rollback_id}, {"$inc": {"stock": rollback_quantity}})
                return jsonify({"success": False, "message": f"{item['product']['name']} stock is not available"}), 400
            updated.append((product_id, item["quantity"]))
            order_items.append({"product_id": product_id, "product_name": product["name"], "quantity": item["quantity"], "unit_price": product["price"], "line_total": item["lineTotal"]})

        order = {
            "order_no": f"KC{datetime.now().strftime('%Y%m%d')}{uuid4().hex[:6].upper()}",
            "customer_name": customer_name, "email": email, "phone": phone, "address": address,
            "subtotal": details["subtotal"], "shipping": details["shipping"], "tax": details["tax"],
            "total": details["total"], "status": "Placed", "created_at": datetime.now(timezone.utc),
            "items": order_items,
        }
        order["_id"] = orders_collection.insert_one(order).inserted_id
        save_cart({})
        return jsonify({"success": True, "order": public_order(order)}), 201

    @app.get("/api/orders")
    def orders():
        rows = orders_collection.find().sort("created_at", DESCENDING).limit(20)
        return jsonify({"success": True, "orders": [public_order(row) for row in rows]})

    @app.get("/api/stats")
    def stats():
        revenue_rows = list(orders_collection.aggregate([{"$group": {"_id": None, "value": {"$sum": "$total"}}}]))
        stock_rows = list(products_collection.aggregate([{"$group": {"_id": None, "value": {"$sum": "$stock"}}}]))
        return jsonify({"success": True, "stats": {
            "productCount": products_collection.count_documents({}),
            "orderCount": orders_collection.count_documents({}),
            "revenue": revenue_rows[0]["value"] if revenue_rows else 0,
            "stock": stock_rows[0]["value"] if stock_rows else 0,
            "cartCount": cart_details()["count"],
        }})

    app.extensions["mongo_client"] = mongo_client
    app.extensions["mongo_db"] = database
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
