from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from azure.cosmos import CosmosClient, PartitionKey, exceptions
import os
import uuid
from datetime import datetime

app = FastAPI(title="CloudMart API", version="1.1.0")

# Build info
BUILD_TIME = datetime.utcnow().isoformat()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Cosmos DB Configuration
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "")
COSMOS_KEY = os.environ.get("COSMOS_KEY", "")
DATABASE_NAME = "cloudmart"

# Initialize Cosmos DB client
client = None
database = None
products_container = None
cart_container = None
orders_container = None

def init_cosmos():
    global client, database, products_container, cart_container, orders_container
    if COSMOS_ENDPOINT and COSMOS_KEY:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        database = client.get_database_client(DATABASE_NAME)
        products_container = database.get_container_client("products")
        cart_container = database.get_container_client("cart")
        orders_container = database.get_container_client("orders")
        
        # Seed products if empty
        try:
            items = list(products_container.query_items("SELECT * FROM c", enable_cross_partition_query=True))
            if len(items) == 0:
                seed_products()
        except:
            pass

def seed_products():
    products = [
        {"id": "1", "name": "Wireless Headphones Pro", "description": "Premium noise-cancelling wireless headphones with 30hr battery", "category": "Electronics", "price": 199.99, "stock": 50, "image": "🎧"},
        {"id": "2", "name": "Smart Watch Elite", "description": "Advanced fitness tracking smartwatch with GPS", "category": "Electronics", "price": 299.99, "stock": 30, "image": "⌚"},
        {"id": "3", "name": "Running Shoes X1", "description": "Lightweight breathable running shoes", "category": "Sports", "price": 89.99, "stock": 100, "image": "👟"},
        {"id": "4", "name": "Laptop Backpack Pro", "description": "Water-resistant 15.6 inch laptop backpack", "category": "Accessories", "price": 49.99, "stock": 75, "image": "🎒"},
        {"id": "5", "name": "Coffee Maker Deluxe", "description": "12-cup programmable coffee maker", "category": "Home", "price": 79.99, "stock": 40, "image": "☕"},
        {"id": "6", "name": "Yoga Mat Premium", "description": "Extra thick eco-friendly yoga mat", "category": "Sports", "price": 35.99, "stock": 60, "image": "🧘"},
        {"id": "7", "name": "Bluetooth Speaker", "description": "Portable waterproof bluetooth speaker", "category": "Electronics", "price": 59.99, "stock": 45, "image": "🔊"},
        {"id": "8", "name": "Desk Lamp LED", "description": "Adjustable LED desk lamp with USB port", "category": "Home", "price": 29.99, "stock": 80, "image": "💡"}
    ]
    for p in products:
        try:
            products_container.create_item(p)
        except exceptions.CosmosResourceExistsError:
            pass

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    init_cosmos()

class CartItem(BaseModel):
    product_id: str
    quantity: int = 1

# Default user for demo
DEFAULT_USER = "demo_user"

# HTML Template for Frontend (abbreviated for documentation)
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CloudMart - E-Commerce Platform</title>
<style>
/* Modern gradient UI with purple/blue theme */
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
     background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh}
/* ... full CSS styles ... */
</style>
</head>
<body>
<header class="header">
<div class="header-content">
<div class="logo">Cloud<span>Mart</span><span class="db-badge">🗄️ Cosmos DB</span></div>
<button class="cart-btn" onclick="openCart()">🛒 Cart <span class="cart-count" id="cartCount">0</span></button>
</div>
</header>
<!-- Full HTML/JS implementation for product catalog, cart, checkout -->
<script>
// JavaScript for API integration, cart management, order placement
let products=[], cart=[], categories=[];
async function init() {
    products = await fetch("/api/v1/products").then(r => r.json());
    categories = await fetch("/api/v1/categories").then(r => r.json());
    cart = await fetch("/api/v1/cart").then(r => r.json());
    renderFilters(); renderProducts(); updateCartCount();
}
// ... full JavaScript implementation ...
init();
</script>
</body>
</html>'''

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_TEMPLATE

@app.get("/health")
def health():
    db_status = "connected" if client else "disconnected"
    return {
        "status": "healthy", 
        "service": "cloudmart-api", 
        "version": "1.1.0",
        "build_time": BUILD_TIME,
        "database": "cosmos-db", 
        "db_status": db_status,
        "deployed_via": "GitHub Actions + Docker Hub"
    }

@app.get("/api/v1/products")
def list_products(category: str = None):
    if not products_container:
        return []
    try:
        if category:
            query = f"SELECT * FROM c WHERE c.category = @category"
            items = list(products_container.query_items(query, 
                parameters=[{"name": "@category", "value": category}], 
                enable_cross_partition_query=True))
        else:
            items = list(products_container.query_items("SELECT * FROM c", 
                enable_cross_partition_query=True))
        return items
    except Exception as e:
        return []

@app.get("/api/v1/products/{product_id}")
def get_product(product_id: str):
    if not products_container:
        raise HTTPException(status_code=503, detail="Database not available")
    try:
        items = list(products_container.query_items(
            f"SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": product_id}],
            enable_cross_partition_query=True
        ))
        if items:
            return items[0]
        raise HTTPException(status_code=404, detail="Product not found")
    except exceptions.CosmosHttpResponseError:
        raise HTTPException(status_code=404, detail="Product not found")

@app.get("/api/v1/categories")
def get_categories():
    if not products_container:
        return []
    try:
        items = list(products_container.query_items(
            "SELECT DISTINCT c.category FROM c", 
            enable_cross_partition_query=True))
        return [item["category"] for item in items]
    except:
        return []

@app.get("/api/v1/cart")
def get_cart():
    if not cart_container:
        return []
    try:
        items = list(cart_container.query_items(
            "SELECT * FROM c WHERE c.user_id = @user_id",
            parameters=[{"name": "@user_id", "value": DEFAULT_USER}],
            enable_cross_partition_query=True
        ))
        return items
    except:
        return []

@app.post("/api/v1/cart/items")
def add_to_cart(item: CartItem):
    if not cart_container:
        return {"error": "Database not available"}
    try:
        existing = list(cart_container.query_items(
            "SELECT * FROM c WHERE c.user_id = @user_id AND c.product_id = @product_id",
            parameters=[
                {"name": "@user_id", "value": DEFAULT_USER},
                {"name": "@product_id", "value": item.product_id}
            ],
            enable_cross_partition_query=True
        ))
        
        if existing:
            cart_item = existing[0]
            cart_item["quantity"] = item.quantity
            cart_container.upsert_item(cart_item)
        else:
            cart_item = {
                "id": str(uuid.uuid4()),
                "user_id": DEFAULT_USER,
                "product_id": item.product_id,
                "quantity": item.quantity
            }
            cart_container.create_item(cart_item)
        
        return {"message": "Saved to Cosmos DB"}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/v1/cart/items/{product_id}")
def remove_from_cart(product_id: str):
    if not cart_container:
        return {"error": "Database not available"}
    try:
        items = list(cart_container.query_items(
            "SELECT * FROM c WHERE c.user_id = @user_id AND c.product_id = @product_id",
            parameters=[
                {"name": "@user_id", "value": DEFAULT_USER},
                {"name": "@product_id", "value": product_id}
            ],
            enable_cross_partition_query=True
        ))
        for item in items:
            cart_container.delete_item(item["id"], partition_key=DEFAULT_USER)
        return {"message": "Removed from Cosmos DB"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/v1/orders")
def create_order():
    if not orders_container or not cart_container:
        return {"error": "Database not available"}
    try:
        cart_items = list(cart_container.query_items(
            "SELECT * FROM c WHERE c.user_id = @user_id",
            parameters=[{"name": "@user_id", "value": DEFAULT_USER}],
            enable_cross_partition_query=True
        ))
        
        order = {
            "id": str(uuid.uuid4()),
            "user_id": DEFAULT_USER,
            "items": [{"product_id": i["product_id"], "quantity": i["quantity"]} for i in cart_items],
            "status": "confirmed",
            "created_at": datetime.utcnow().isoformat()
        }
        orders_container.create_item(order)
        
        for item in cart_items:
            cart_container.delete_item(item["id"], partition_key=DEFAULT_USER)
        
        return order
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/orders")
def get_orders():
    if not orders_container:
        return []
    try:
        items = list(orders_container.query_items(
            "SELECT * FROM c WHERE c.user_id = @user_id",
            parameters=[{"name": "@user_id", "value": DEFAULT_USER}],
            enable_cross_partition_query=True
        ))
        return items
    except:
        return []
