from typing import Optional
from datetime import datetime
from pydantic import BaseModel, conint
from app.models.order import OrderStatus


class OrderCreate(BaseModel):
    product_id: int
    quantity: conint(ge=1)  # >= 1

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": 1,
                "quantity": 2
            }
        }
    }


class OrderRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    status: OrderStatus
    created_at: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 7,
                "product_id": 1,
                "quantity": 2,
                "status": "PENDING",
                "created_at": "2025-08-18T12:45:10.123456Z"
            }
        }
    }


# For API-driven changes (e.g., status transitions). We'll enforce rules in the router.
class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "PAID"
            }
        }
    }
