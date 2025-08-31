from typing import Optional
from sqlmodel import SQLModel, Field


class ProductBase(SQLModel):
    # DB-level constraints (unique SKU, indexes) + basic value guards
    sku: str = Field(
        index=True,
        sa_column_kwargs={"unique": True},  # enforce uniqueness in the DB
        description="Unique stock keeping unit",
    )
    name: str = Field(min_length=1, description="Human-readable name")
    price: float = Field(gt=0, description="Unit price; must be > 0")
    stock: int = Field(ge=0, description="Units in stock; must be >= 0")


class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
