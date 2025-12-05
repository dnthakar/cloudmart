from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="CloudMart API")

# Temporary in-memory data (for testing before Cosmos)
class Product(BaseModel):
    id: str
    name: str
    category: str
    price: float

PRODUCTS = [
    Product(id="1", name="Laptop", category="Electronics", price=333.99),
    Product(id="2", name="earphones", category="Electronics", price=299.99),
    Product(id="3", name="table", category="Furniture", price=649.99),
]


@app.get("/")
def read_root():
    return {"message": "Hello there Welcome to CloudMart!"}


@app.get("/health")
def health_check():
    return {"status": "ok", "db": "not connected yet (local test)"}


@app.get("/api/v1/products", response_model=List[Product])
def list_products(category: Optional[str] = None):
    if category:
        return [p for p in PRODUCTS if p.category.lower() == category.lower()]
    return PRODUCTS

