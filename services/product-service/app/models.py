from pydantic import BaseModel, Field
from typing import Optional


class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float = Field(gt=0, description="Price must be greater than zero")
    stock_quantity: int = Field(ge=0, description="Stock quantity must be non-negative")


class ProductCreate(BaseModel):
    name: str
    description: str
    price: float = Field(gt=0, description="Price must be greater than zero")
    stock_quantity: int = Field(ge=0, description="Stock quantity must be non-negative")


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock_quantity: int