import os
from datetime import datetime, timezone
from uuid import uuid4

from flask import Flask, jsonify, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func


db = SQLAlchemy()


DEFAULT_PRODUCTS = [
    {
        "sku": "KC-PHN-001",
        "name": "Nova X5 Smartphone",
        "category": "Mobiles",
        "price": 18999,
        "stock": 24,
        "rating": 4.6,
        "image": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=900&q=80",
        "description": "AMOLED display, 5G performance, 128GB storage and all-day battery for students and professionals.",
        "featured": True,
    },
    {
        "sku": "KC-LAP-014",
        "name": "KCDS ProBook 14",
        "category": "Laptops",
        "price": 57999,
        "stock": 12,
        "rating": 4.7,
        "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80",
        "description": "Lightweight laptop with fast SSD, long battery life and excellent coding performance.",
        "featured": True,
    },
    {
        "sku": "KC-AUD-202",
        "name": "Pulse Wireless Headphones",
        "category": "Audio",
        "price": 2499,
        "stock": 48,
        "rating": 4.4,
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80",
        "description": "Deep bass, noise isolation and 40-hour battery for classes, travel and gaming.",
        "featured": False,
    },
    {
        "sku": "KC-WCH-330",
        "name": "FitTrack Smart Watch",
        "category": "Wearables",
        "price": 3999,
        "stock": 31,
        "rating": 4.3,
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=80",
        "description": "Fitness tracking, notifications, heart-rate monitoring and premium metal body.",
        "featured": True,
    },
    {
        "sku": "KC-BAG-510",
        "name": "Urban Laptop Backpack",
        "category": "Accessories",
        "price": 1599,
        "stock": 60,
        "rating": 4.5,
        "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80",
        "description": "Water-resistant backpack with laptop sleeve, organizer pockets and travel-ready comfort.",
        "featured": False,
    },
    {
        "sku": "KC-TAB-112",
        "name": "StudyTab 10",
        "category": "Tablets",
        "price": 14999,
        "stock": 19,
        "rating": 4.2,
        "image": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=900&q=80",
        "description": "10-inch tablet for notes, streaming, online classes and light productivity.",
        "featured": False,
    },
]


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(40), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    rating = db.Column(db.Float, nullable=False, default=4.0)
    image = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=False)
    featured = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "stock": self.stock,
            "rating": self.rating,
            "image": self.image,
            "description": self.description,
            "featured": self.featured,
        }


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(40), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(140), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)
    shipping = db.Column(db.Integer, nullable=False)
    tax = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Placed")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "orderNo": self.order_no,
            "customerName": self.customer_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "subtotal": self.subtotal,
            "shipping": self.shipping,
            "tax": self.tax,
            "total": self.total,
            "status": self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else "",
            "items": [item.to_dict() for item in self.items],
        }


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    product_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)
    line_total = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "productId": self.product_id,
            "productName": self.product_name,
            "quantity": self.quantity,
            "unitPrice": self.unit_price,
            "lineTotal": self.line_total,
        }


def normalize_database_url(url):
    if not url:
        return "sqlite:///ecommerce.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def clean(value, max_length=500):
    return str(value or "").strip()[:max_length]


def digits(value):
    return "".join(char for char in str(value or "") if char.isdigit())


def money_parts(cart_items):
    subtotal = sum(item["lineTotal"] for item in cart_items)
    shipping = 0 if subtotal >= 20000 or subtotal == 0 else 99
    tax = round(subtotal * 0.05)
    return {"subtotal": subtotal, "shipping": shipping, "tax": tax, "total": subtotal + shipping + tax}


def get_cart():
    cart = session.setdefault("cart", {})
    return {str(key): int(value) for key, value in cart.items()}


def save_cart(cart):
    session["cart"] = {str(key): int(value) for key, value in cart.items() if int(value) > 0}
    session.modified = True


def cart_details():
    cart = get_cart()
    items = []
    for product_id, quantity in cart.items():
        product = db.session.get(Product, int(product_id))
        if not product:
            continue
        safe_quantity = min(quantity, product.stock)
        items.append({
            "product": product.to_dict(),
            "quantity": safe_quantity,
            "lineTotal": product.price * safe_quantity,
        })
    totals = money_parts(items)
    return {"items": items, **totals, "count": sum(item["quantity"] for item in items)}


def seed_products():
    if Product.query.count() == 0:
        for item in DEFAULT_PRODUCTS:
            db.session.add(Product(**item))
        db.session.commit()


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
    except (TypeError, ValueError):
        raise ValueError("Price, stock and rating must be valid numbers")
    if not all([name, sku, category, description]):
        raise ValueError("Name, SKU, category and description are required")
    if price < 1 or price > 1000000:
        raise ValueError("Price must be between 1 and 1000000")
    if stock < 0 or stock > 10000:
        raise ValueError("Stock must be between 0 and 10000")
    if rating < 1 or rating > 5:
        raise ValueError("Rating must be between 1 and 5")
    return {
        "name": name,
        "sku": sku,
        "category": category,
        "description": description,
        "image": image,
        "price": price,
        "stock": stock,
        "rating": rating,
        "featured": bool(payload.get("featured")),
    }


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = normalize_database_url(os.getenv("DATABASE_URL"))
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_SORT_KEYS"] = False
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        seed_products()

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"success": True, "status": "ok", "database": app.config["SQLALCHEMY_DATABASE_URI"].split(":", 1)[0]})

    @app.get("/api/products")
    def products():
        query = clean(request.args.get("q"), 120).lower()
        category = clean(request.args.get("category"), 80)
        product_query = Product.query
        if category:
            product_query = product_query.filter(Product.category == category)
        items = [item.to_dict() for item in product_query.order_by(Product.featured.desc(), Product.name.asc()).all()]
        if query:
            items = [item for item in items if query in " ".join([item["name"], item["category"], item["description"]]).lower()]
        categories = [row[0] for row in db.session.query(Product.category).distinct().order_by(Product.category).all()]
        return jsonify({"success": True, "products": items, "categories": categories})

    @app.post("/api/products")
    def products_create():
        try:
            product = Product(**validate_product(request.get_json(silent=True) or {}))
            db.session.add(product)
            db.session.commit()
            return jsonify({"success": True, "product": product.to_dict()}), 201
        except ValueError as exc:
            return jsonify({"success": False, "message": str(exc)}), 400
        except Exception as exc:
            db.session.rollback()
            return jsonify({"success": False, "message": f"Could not save product: {exc}"}), 400

    @app.get("/api/cart")
    def cart():
        return jsonify({"success": True, "cart": cart_details()})

    @app.post("/api/cart")
    def cart_add():
        payload = request.get_json(silent=True) or {}
        product_id = int(payload.get("productId") or 0)
        quantity = int(payload.get("quantity") or 1)
        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({"success": False, "message": "Product not found"}), 404
        if quantity < 1:
            return jsonify({"success": False, "message": "Quantity must be at least 1"}), 400
        cart_data = get_cart()
        current = cart_data.get(str(product_id), 0)
        cart_data[str(product_id)] = min(product.stock, current + quantity)
        save_cart(cart_data)
        return jsonify({"success": True, "cart": cart_details()})

    @app.patch("/api/cart/<int:product_id>")
    def cart_update(product_id):
        quantity = int((request.get_json(silent=True) or {}).get("quantity") or 0)
        cart_data = get_cart()
        if quantity <= 0:
            cart_data.pop(str(product_id), None)
        else:
            product = db.session.get(Product, product_id)
            if not product:
                return jsonify({"success": False, "message": "Product not found"}), 404
            cart_data[str(product_id)] = min(product.stock, quantity)
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
        order = Order(
            order_no=f"KC{datetime.now().strftime('%Y%m%d')}{uuid4().hex[:6].upper()}",
            customer_name=customer_name,
            email=email,
            phone=phone,
            address=address,
            subtotal=details["subtotal"],
            shipping=details["shipping"],
            tax=details["tax"],
            total=details["total"],
        )
        try:
            for item in details["items"]:
                product = db.session.get(Product, item["product"]["id"])
                if not product or product.stock < item["quantity"]:
                    raise ValueError(f"{item['product']['name']} stock is not available")
                product.stock -= item["quantity"]
                order.items.append(OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    quantity=item["quantity"],
                    unit_price=product.price,
                    line_total=item["lineTotal"],
                ))
            db.session.add(order)
            db.session.commit()
            save_cart({})
            return jsonify({"success": True, "order": order.to_dict()}), 201
        except ValueError as exc:
            db.session.rollback()
            return jsonify({"success": False, "message": str(exc)}), 400

    @app.get("/api/orders")
    def orders():
        items = [item.to_dict() for item in Order.query.order_by(Order.created_at.desc()).limit(20).all()]
        return jsonify({"success": True, "orders": items})

    @app.get("/api/stats")
    def stats():
        product_count = Product.query.count()
        order_count = Order.query.count()
        revenue = db.session.query(func.coalesce(func.sum(Order.total), 0)).scalar()
        stock = db.session.query(func.coalesce(func.sum(Product.stock), 0)).scalar()
        return jsonify({
            "success": True,
            "stats": {
                "productCount": product_count,
                "orderCount": order_count,
                "revenue": int(revenue or 0),
                "stock": int(stock or 0),
                "cartCount": cart_details()["count"],
            },
        })

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
