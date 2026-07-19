from fastapi import FastAPI, HTTPException
from typing import List
import httpx
import os

from app.models import OrderRequest, OrderResponse, Order
from app.database import create_order, get_order_by_id, get_all_orders
from app.queue_client import publish_order_notification

app = FastAPI(title="Order Service", version="1.0.0")

# Environment variables for Product Service URL
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8000")


@app.on_event("startup")
async def startup_event():
    print("Order Service started successfully.")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "order-service",
        "version": "1.0.0"
    }


async def verify_product_exists(product_id: int) -> bool:
    """Verify if the product exists by calling the Product Service."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}")
            print(f"Product Service response for product_id {product_id}: {response.status_code}")
            return response.status_code == 200
    except httpx.RequestError as e:
        print(f"Error while verifying product existence: {str(e)}")
        return False
    

@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_new_order(order_request: OrderRequest):
    """Create a new order after validating the product existence."""

    # Step 1: Verify if the product exists
    product_exists = await verify_product_exists(order_request.product_id)
    if not product_exists:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Step 2: Create the order in the database
    order = create_order(
        product_id=order_request.product_id,
        quantity=order_request.quantity,
        customer_email=order_request.customer_email
    )

    # Step 3: Publish order notification to RabbitMQ
    order_data = {
        "id": order.id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "customer_email": order.customer_email,
        "status": order.status.value,
        "created_at": order.created_at.isoformat()
    }

    return OrderResponse(
        id=order.id,
        product_id=order.product_id,
        quantity=order.quantity,
        customer_email=order.customer_email,
        status=order.status.value,
        created_at=order.created_at,
        message="Order created successfully" + (" and notification sent" if publish_order_notification(order_data) else " but failed to send notification")
    )


@app.get("/orders", response_model=List[Order])
async def list_orders():
    """Retrieve all orders."""
    return get_all_orders()


@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: int):
    """Retrieve an order by its ID."""
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order with ID {order_id} not found")
    return order