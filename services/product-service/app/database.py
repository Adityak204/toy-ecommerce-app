from typing import Dict, List, Optional
import logging
from app.models import Product

# Get logger for this module
logger = logging.getLogger(__name__)

# In-memory database simulation
products_db: Dict[int, Product] = {}

# Auto-incrementing ID for products
_next_id = 1


def intitalize_sample_data():
    """Pre-populate the in-memory database with sample products."""
    global _next_id

    sample_products = [
        {"name": "Laptop", "description": "A high-performance laptop", "price": 999.99, "stock_quantity": 10},
        {"name": "Smartphone", "description": "A latest model smartphone", "price": 699.99, "stock_quantity": 25},
        {"name": "Headphones", "description": "Noise-cancelling headphones", "price": 199.99, "stock_quantity": 50},
        {"name": "Smartwatch", "description": "A smartwatch with various features", "price": 299.99, "stock_quantity": 15},
        {"name": "Tablet", "description": "A lightweight tablet for everyday use", "price": 399.99, "stock_quantity": 20},
        {"name": "Camera", "description": "A digital camera for photography enthusiasts", "price": 499.99, "stock_quantity": 8},
        {"name": "Gaming Console", "description": "A popular gaming console", "price": 399.99, "stock_quantity": 12},
        {"name": "Bluetooth Speaker", "description": "A portable Bluetooth speaker", "price": 149.99, "stock_quantity": 30},
        {"name": "External Hard Drive", "description": "A 1TB external hard drive", "price": 89.99, "stock_quantity": 40},
        {"name": "Wireless Mouse", "description": "A wireless mouse for computers", "price": 29.99, "stock_quantity": 60},
    ]
    
    for product_data in sample_products:
        product = Product(id=_next_id, **product_data)
        products_db[_next_id] = product
        logger.debug(
            "Sample product loaded",
            extra={
                "event": "sample_product_loaded",
                "product_id": _next_id,
                "product_name": product_data["name"],
            }
        )
        _next_id += 1 


def get_all_products() -> List[Product]:
    """Retrieve all products from the in-memory database."""
    products = list(products_db.values())
    logger.debug(
        "All products retrieved",
        extra={
            "event": "all_products_retrieved",
            "product_count": len(products),
        }
    )
    return products


def get_product_by_id(product_id: int) -> Optional[Product]:
    """Retrieve a product by its ID from the in-memory database."""
    product = products_db.get(product_id)
    logger.debug(
        "Product retrieved",
        extra={
            "event": "product_retrieved",
            "product_id": product_id,
            "found": product is not None,
        }
    )
    return product


def create_product(name: str, description: str, price: float, stock_quantity: int) -> Product:
    """Create a new product and add it to the in-memory database.
    """
    global _next_id
    
    product = Product(id=_next_id, name=name, description=description, price=price, stock_quantity=stock_quantity)
    products_db[_next_id] = product
    logger.debug(
        "Product created in database",
        extra={
            "event": "product_created",
            "product_id": _next_id,
            "product_name": name,
        }
    )
    _next_id += 1
    return product