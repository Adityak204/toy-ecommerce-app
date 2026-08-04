from fastapi import FastAPI, HTTPException
from typing import List
import httpx
import os
import logging

from app.models import OrderRequest, OrderResponse, Order
from app.database import create_order, get_order_by_id, get_all_orders
from app.queue_client import publish_order_notification
from app.logging_config import setup_logging
from app.middleware.logging_middleware import LoggingMiddleware
from app.log_context import get_correlation_id

# Configure logging
setup_logging()

# Get logger for this module
logger = logging.getLogger(__name__)

app = FastAPI(title="Order Service", version="1.0.0")

# Add logging middleware to the application
app.add_middleware(LoggingMiddleware)

# Environment variables for Product Service URL
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8000")


@app.on_event("startup")
async def startup_event():
    logger.info(
        "Service started successfully",
        extra={
            "event": "service_startup",
            "product_service_url": PRODUCT_SERVICE_URL,
        }
    )


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
            correlation_id = get_correlation_id()
            response = await client.get(
                f"{PRODUCT_SERVICE_URL}/products/{product_id}",
                headers={
                    "X-Correlation-Id": correlation_id
                } if correlation_id else {}

            )
            logger.info(
                "Product existence verified",
                extra={
                    "event": "product_existence_verified",
                    "product_id": product_id,
                    "correlation_id": correlation_id,
                    "exists": response.status_code == 200,
                    "status_code": response.status_code,
                }
            )
            return response.status_code == 200
    except httpx.RequestError as e:
        logger.exception(
            "Product existence verification failed",
            extra={
                "event": "product_existence_verification_failed",
                "product_id": product_id,
                "exception": type(e).__name__,
                "message": str(e),
            }
        )
        return False
    

@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_new_order(order_request: OrderRequest):
    """Create a new order after validating the product existence."""

    # Step 1: Verify if the product exists
    product_exists = await verify_product_exists(order_request.product_id)
    if not product_exists:
        logger.warning(
            "Order creation failed - product not found",
            extra={
                "event": "order_creation_failed",
                "product_id": order_request.product_id,
                "reason": "Product not found",
            }
        )
        raise HTTPException(status_code=404, detail=f"Product with ID {order_request.product_id} not found")
    
    # Step 2: Create the order in the database
    order = create_order(
        product_id=order_request.product_id,
        quantity=order_request.quantity,
        customer_email=order_request.customer_email
    )
    logger.info(
        "Order created",
        extra={
            "event": "order_created",
            "order_id": order.id,
            "product_id": order.product_id,
            "quantity": order.quantity,
        }
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
    orders = get_all_orders()
    logger.info(
        "Orders retrieved",
        extra={
            "event": "orders_retrieved",
            "order_count": len(orders),
        }
    )
    return orders


@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: int):
    """Retrieve an order by its ID."""
    order = get_order_by_id(order_id)
    if not order:
        logger.warning(
            "Order not found",
            extra={
                "event": "order_not_found",
                "order_id": order_id,
            }
        )
        raise HTTPException(status_code=404, detail=f"Order with ID {order_id} not found")
    logger.info(
        "Order retrieved",
        extra={
            "event": "order_retrieved",
            "order_id": order_id,
        }
    )
    return order