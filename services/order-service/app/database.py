from typing import Dict, List, Optional
from pydantic import EmailStr
from datetime import datetime
from app.models import Order, OrderStatus

# In-memory database simulation
orders_db: Dict[int, Order] = {}

# Auto-incrementing order ID
_next_id = 1

def create_order(product_id: int, quantity: int, customer_email: EmailStr) -> Order:
    """Create a new order"""
    global _next_id

    order = Order(
        id=_next_id,
        product_id=product_id,
        quantity=quantity,
        customer_email=customer_email,
        status=OrderStatus.PENDING,
        created_at=datetime.now()
    )

    orders_db[_next_id] = order
    _next_id += 1
    return order


def get_all_orders() -> List[Order]:
    """Retrieve all orders"""
    return list(orders_db.values())


def get_order_by_id(order_id: int) -> Optional[Order]:
    """Retrieve an order by its ID"""
    return orders_db.get(order_id)


def update_order_status(order_id: int, new_status: OrderStatus) -> Optional[Order]:
    """Update the status of an existing order"""
    order = orders_db.get(order_id)
    if order:
        order.status = new_status
        orders_db[order_id] = order
        return order
    return None