from typing import Optional
from pydantic import BaseModel, constr, conint, confloat


# Input when creating a product (API boundary)
class ProductCreate(BaseModel):
    sku: constr(min_length=1)          # not empty
    name: constr(min_length=1)         # not empty
    price: confloat(gt=0)              # > 0
    stock: conint(ge=0)                # >= 0

    model_config = {
        "json_schema_extra": {
            "example": {
                "sku": "SKU-123",
                "name": "Widget",
                "price": 9.99,
                "stock": 25
            }
        }
    }


# Output when returning a product
class ProductRead(BaseModel):
    id: int
    sku: str
    name: str
    price: float
    stock: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "sku": "SKU-123",
                "name": "Widget",
                "price": 9.99,
                "stock": 25
            }
        }
    }


# Partial update allowed (invalid/missing fields will be ignored)
class ProductUpdate(BaseModel):
    sku: Optional[constr(min_length=1)] = None
    name: Optional[constr(min_length=1)] = None
    price: Optional[confloat(gt=0)] = None
    stock: Optional[conint(ge=0)] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "price": 12.5,
                "stock": 30
            }
        }
    }

