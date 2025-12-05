from app.database import products_container, cart_container, orders_container

def get_products(category=None):
    query = "SELECT * FROM c"
    if category:
        query = f"SELECT * FROM c WHERE c.category='{category}'"
    return list(products_container.query_items(query=query, enable_cross_partition_query=True))

def add_to_cart(item):
    cart_container.create_item(body=item)

def get_cart(user_id):
    query = f"SELECT * FROM c WHERE c.user_id='{user_id}'"
    return list(cart_container.query_items(query=query, enable_cross_partition_query=True))

def create_order(order):
    orders_container.create_item(body=order)
