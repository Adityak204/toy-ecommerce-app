from fastapi import FastAPI, HTTPException
from typing import List
import os
import logging

from app.models import Product, ProductCreate, ProductResponse
from app.database import intitalize_sample_data, get_all_products, get_product_by_id, create_product
from app.logging_config import setup_logging
from app.middleware.logging_middleware import LoggingMiddleware

# Configure logging
setup_logging()

# Get logger for this module
logger = logging.getLogger(__name__)


app = FastAPI(title="Product Service", version="1.0.0")

# Add logging middleware to the application
app.add_middleware(LoggingMiddleware)

# Initialize sample data when the application starts
@app.on_event("startup")
async def startup_event():
    products_count = intitalize_sample_data()
    logger.info(
        "Service started successfully",
        extra={
            "event": "service_startup",
            "product_count": products_count,
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint to verify the service is running."""
    return {
        "status": "healthy",
        "service": "Product Service",
        "version": "1.0.0",
    }

@app.get("/products", response_model=List[ProductResponse])
async def list_products():
    """Retrieve a list of all products."""
    products = get_all_products()
    logger.info(
        "Products retrieved",
        extra={
            "event": "products_retrieved",
            "product_count": len(products),
        }
    )
    return products

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int):
    """Retrieve a product by its ID."""
    product = get_product_by_id(product_id)
    if not product:
        logger.warning(
            "Product not found",
            extra={
                "event": "product_not_found",
                "product_id": product_id,
            }
        )
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
    logger.info(
        "Product retrieved",
        extra={
            "event": "product_retrieved",
            "product_id": product_id,
            "product_name": product.name,
        }
    )
    return product

@app.post("/products", response_model=ProductResponse, status_code=201)
async def add_product(product: ProductCreate):
    """Create a new product."""
    new_product = create_product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock_quantity=product.stock_quantity
    )
    logger.info(
        "Product created",
        extra={
            "event": "product_created",
            "product_id": new_product.id,
            "product_name": new_product.name,
            "product_price": float(new_product.price),
        }
    )
    return new_product