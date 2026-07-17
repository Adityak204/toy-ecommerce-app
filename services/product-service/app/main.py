from fastapi import FastAPI, HTTPException
from typing import List
import os

from app.models import Product, ProductCreate, ProductResponse
from app.database import intitalize_sample_data, get_all_products, get_product_by_id, create_product

app = FastAPI(title="Product Service", version="1.0.0")

# Initialize sample data when the application starts
@app.on_event("startup")
async def startup_event():
    intitalize_sample_data()
    print("Sample data initialized successfully.")

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
    return products

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int):
    """Retrieve a product by its ID."""
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
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
    return new_product