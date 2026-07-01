# KCDS E-Commerce Site

Online shopping website built with HTML, CSS, JavaScript, Python Flask and SQL database support for PostgreSQL/MySQL.

## Features

- Jigel responsive e-commerce UI with product catalog.
- Product search and category filtering.
- Shopping cart with quantity update and totals.
- Checkout flow that creates orders and updates product stock.
- Admin module to add products.
- Recent orders dashboard.
- SQLAlchemy models for products, orders and order items.
- Uses `DATABASE_URL` for PostgreSQL/MySQL in production.
- SQLite fallback for local development.
- Render deployment configuration and GitHub Actions CI.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.

## Database

Local default:

```text
sqlite:///ecommerce.db
```

Production examples:

```text
postgresql://user:password@host:5432/dbname
mysql+pymysql://user:password@host:3306/dbname
```

Set the connection string as `DATABASE_URL`.

## API Endpoints

- `GET /api/health`
- `GET /api/products`
- `POST /api/products`
- `GET /api/cart`
- `POST /api/cart`
- `PATCH /api/cart/<product_id>`
- `DELETE /api/cart`
- `POST /api/orders`
- `GET /api/orders`
- `GET /api/stats`

## Deploy on Render

Use `render.yaml`, connect this GitHub repository, and set `DATABASE_URL` plus `SECRET_KEY`.

## Tests

```bash
pytest -q
```
