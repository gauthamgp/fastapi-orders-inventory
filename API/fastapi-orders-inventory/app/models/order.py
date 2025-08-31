from typing import Optional
from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, Field


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELED = "CANCELED"


class OrderBase(SQLModel):
    product_id: int = Field(
        foreign_key="product.id",
        index=True,
        description="FK to Product.id",
    )
    quantity: int = Field(ge=1, description="Must be >= 1")
    status: OrderStatus = Field(
        default=OrderStatus.PENDING,
        description="Allowed statuses only",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        description="UTC creation time",
    )


class Order(OrderBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
