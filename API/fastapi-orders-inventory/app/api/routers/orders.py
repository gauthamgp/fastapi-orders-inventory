from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update
from sqlmodel import Session, select

from app.api.deps import get_db
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate

router = APIRouter()


# ---- Helpers ----
def _validate_status_transition(current: OrderStatus, new: OrderStatus) -> None:
    """
    Allowed transitions:
      PENDING -> PAID | CANCELED
      PAID    -> SHIPPED | CANCELED
      SHIPPED -> (no changes allowed)
      CANCELED-> (no changes allowed)
    """
    if current == new:
        return

    allowed = {
        OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELED},
        OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELED},
        OrderStatus.SHIPPED: set(),
        OrderStatus.CANCELED: set(),
    }
    if new not in allowed[current]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid status transition: {current} -> {new}",
        )


# ---- Routes ----
@router.post(
    "/",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an order and reduce product stock atomically",
    responses={
        201: {
            "description": "Order created",
            "content": {
                "application/json": {
                    "example": {
                        "id": 7, "product_id": 1, "quantity": 2, "status": "PENDING",
                        "created_at": "2025-08-18T12:45:10.123456Z"
                    }
                }
            },
        },
        404: {
            "description": "Product not found",
            "content": {
                "application/json": {"example": {"detail": "Product not found"}}
            },
        },
        409: {
            "description": "Insufficient stock",
            "content": {
                "application/json": {"example": {"detail": "Insufficient stock"}}
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Validation error",
                        "errors": [
                            {"loc": ["body", "quantity"], "msg": "Input should be greater than or equal to 1", "type": "greater_than_equal"}
                        ]
                    }
                }
            },
        },
    },
)

def create_order(payload: OrderCreate, db: Session = Depends(get_db)) -> OrderRead:
    """
    Steps:
    1) Ensure product exists.
    2) Atomically decrement stock using a single conditional UPDATE:
         UPDATE product SET stock = stock - :qty
         WHERE id = :pid AND stock >= :qty
       If no rows are affected, stock was insufficient → 409 Conflict.
    3) Insert order with status=PENDING.
    """
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Conditional atomic decrement (best-effort on SQLite; robust on most RDBMS).
    stmt = (
        update(Product)
        .where(Product.id == payload.product_id)
        .where(Product.stock >= payload.quantity)
        .values(stock=Product.stock - payload.quantity)
    )
    result = db.exec(stmt)
    if result.rowcount == 0:
        # No row updated -> insufficient stock
        db.rollback()
        raise HTTPException(status_code=409, detail="Insufficient stock")

    # Create the order now that stock is decremented
    order = Order(product_id=payload.product_id, quantity=payload.quantity)
    db.add(order)
    try:
        db.commit()
        db.refresh(order)
    except IntegrityError:
        db.rollback()
        # Extremely rare here, but keep the shape consistent
        raise HTTPException(status_code=409, detail="Order could not be created")
    return order


@router.get(
    "/{order_id}",
    response_model=OrderRead,
    summary="Get an order by ID",
    responses={404: {"description": "Order not found"}},
)
def get_order(order_id: int, db: Session = Depends(get_db)) -> OrderRead:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put(
    "/{order_id}",
    response_model=OrderRead,
    summary="Update an order (status only)",
    responses={
        200: {"description": "Order updated"},
        404: {"description": "Order not found"},
        409: {"description": "Invalid status transition"},
        422: {"description": "Validation error"},
    },
)
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)) -> OrderRead:
    """
    - Only 'status' can change via API (quantity/product_id are immutable here).
    - Enforce valid transitions with _validate_status_transition().
    """
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    data = payload.model_dump(exclude_unset=True)

    if "status" in data and data["status"] is not None:
        _validate_status_transition(order.status, data["status"])
        order.status = data["status"]

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an order (only when PENDING)",
    responses={
        204: {"description": "Order deleted"},
        404: {"description": "Order not found"},
        409: {"description": "Deletion not allowed in this state"},
    },
)
def delete_order(order_id: int, db: Session = Depends(get_db)) -> None:
    """
    Deletion policy:
      - Allowed only when the order is PENDING (no external effects yet).
      - Otherwise return 409 and suggest 'cancel' semantics via status=CANCELED.
    """
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail="Only PENDING orders can be deleted; consider status=CANCELED",
        )

    db.delete(order)
    db.commit()
    return None
