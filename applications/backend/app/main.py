from fastapi import FastAPI
from app.services import crud

app = FastAPI()

@app.get("/")
def home():
    return {"message": "CloudMart API Running"}

@app.get("/api/v1/products")
def list_products(category: str = None):
    return crud.get_products(category)

@app.get("/api/v1/cart")
def get_cart(user_id: str):
    return crud.get_cart(user_id)

@app.post("/api/v1/cart/items")
def add_cart_item(item: dict):
    crud.add_to_cart(item)
    return {"message": "Item added to cart"}

@app.post("/api/v1/orders")
def create_order(order: dict):
    crud.create_order(order)
    return {"message": "Order created successfully"}
