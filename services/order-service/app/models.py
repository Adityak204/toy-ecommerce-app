from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderRequest(BaseModel):
    product_id: int = Field(gt=0, description="Product ID must be a positive integer")
    quantity: int = Field(gt=0, description="Quantity must be a positive integer")
    customer_email: EmailStr


class Order(BaseModel):
    id: int
    product_id: int
    quantity: int
    customer_email: EmailStr
    status: OrderStatus
    created_at: datetime

class OrderResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    customer_email: str
    status: str
    created_at: datetime
    message: str