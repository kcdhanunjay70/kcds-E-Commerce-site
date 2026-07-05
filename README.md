# KCDS E-Commerce Site — MongoDB

Responsive shopping application built with HTML, CSS, JavaScript, Flask, PyMongo and MongoDB.

## Features

- MongoDB `products` and `orders` collections
- Automatic product seed data and unique SKU index
- Product search, categories and admin product creation
- Session cart, checkout, atomic stock updates and order history
- Dashboard statistics and MongoDB health endpoint
- Render and MongoDB Atlas ready

## Run locally

1. Start MongoDB.
2. Copy `.env.example` values into your environment.
3. Install and run:

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.

## Environment

| Variable | Default |
| --- | --- |
| `MONGO_URI` | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | `kcds_ecommerce` |
| `SECRET_KEY` | Development-only fallback |

For Render, set `MONGO_URI` to the MongoDB Atlas connection string. The `/api/health` endpoint verifies the active MongoDB connection.

## Tests

```bash
pytest -q
```

Tests use an isolated in-memory MongoDB-compatible client.
