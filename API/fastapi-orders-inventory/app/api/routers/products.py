from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter()


@router.post(
    "/",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    responses={
        201: {
            "description": "Product created",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1, "sku": "SKU-123", "name": "Widget", "price": 9.99, "stock": 25
                    }
                }
            },
        },
        409: {
            "description": "Duplicate SKU",
            "content": {
                "application/json": {
                    "example": {"detail": "SKU already exists"}
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Validation error",
                        "errors": [
                            {"loc": ["body", "price"], "msg": "Input should be greater than 0", "type": "greater_than"}
                        ]
                    }
                }
            },
        },
    },
)

def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    """
    Flow:
    1) FastAPI validates the body against ProductCreate (Pydantic) → 422 on bad data.
    2) We build a Product DB object and try to insert.
    3) If SKU already exists, DB raises IntegrityError → we return 409 Conflict.
    """
    product = Product(**payload.model_dump())
    db.add(product)
    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="SKU already exists"
        )
    return product


@router.get(
    "/",
    response_model=List[ProductRead],
    summary="List products",
    responses={200: {"description": "List of products"}},
)
def list_products(
    db: Session = Depends(get_db),
    # Simple, optional pagination. The assignment says pagination can be skipped;
    # we'll include light support: limit/offset with bounds to keep it safe.
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[ProductRead]:
    """
    Returns products with optional limit/offset.
    Keep it tiny for the assignment; we don't need cursor-based pagination here.
    """
    stmt = select(Product).offset(offset).limit(limit)
    return list(db.exec(stmt))


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Get a single product by ID",
    responses={404: {"description": "Product not found"}},
)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    """
    404 if the product does not exist.
    """
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put(
    "/{product_id}",
    response_model=ProductRead,
    summary="Update a product (partial allowed)",
    responses={
        200: {"description": "Product updated"},
        404: {"description": "Product not found"},
        409: {"description": "Duplicate SKU"},
        422: {"description": "Validation error"},
    },
)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
) -> ProductRead:
    """
    - We support *partial* updates using exclude_unset=True.
    - If SKU is changed to an existing one, DB throws IntegrityError → 409.
    """
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        db.add(product)
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="SKU already exists"
        )

    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    responses={204: {"description": "Product deleted"}, 404: {"description": "Not found"}},
)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> None:
    """
    204 No Content on success (no response body).
    """
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return None  # FastAPI will send an empty body with 204
