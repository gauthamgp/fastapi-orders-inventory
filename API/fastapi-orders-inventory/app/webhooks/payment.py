import hmac, hashlib, json, time
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlmodel import Session

from app.api.deps import get_db
from app.core.config import settings
from app.models.order import Order, OrderStatus

router = APIRouter()

# ----- helpers -----
def _verify_signature(timestamp: str | None, signature: str | None, body: bytes) -> None:
    if not timestamp or not signature:
        raise HTTPException(status_code=400, detail="Missing signature headers")

    # Timestamp replay guard
    try:
        ts = int(timestamp)
    except Exception:
        raise HTTPException(status_code=400, detail="Bad timestamp header")

    if abs(int(time.time()) - ts) > settings.WEBHOOK_MAX_SKEW_SECONDS:
        raise HTTPException(status_code=400, detail="Stale webhook")

    # Compute HMAC over "{timestamp}.{raw_body}"
    msg = f"{timestamp}.".encode("utf-8") + body
    digest = hmac.new(
        key=settings.PAYMENT_WEBHOOK_SECRET.encode("utf-8"),
        msg=msg,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(digest, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")


def _mark_paid(order: Order, db: Session) -> Order:
    if order.status == OrderStatus.PENDING:
        order.status = OrderStatus.PAID
        db.add(order)
        db.commit()
        db.refresh(order)
    # idempotent: if already PAID/SHIPPED/CANCELED we just return current state
    return order


# ----- route -----
@router.post(
    "/payment",
    summary="Payment webhook: verify HMAC, mark order as PAID",
    responses={
        200: {"description": "Processed (idempotent)"},
        400: {"description": "Bad request / stale webhook / missing headers"},
        401: {"description": "Signature invalid"},
        404: {"description": "Order not found"},
        422: {"description": "Validation error"},
    },
)
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    x_signature_timestamp: str | None = Header(default=None, alias="X-Signature-Timestamp"),
):
    # 1) read raw body
    raw = await request.body()

    # 2) verify signature & timestamp
    _verify_signature(x_signature_timestamp, x_signature, raw)

    # 3) parse JSON
    try:
        payload = json.loads(raw.decode("utf-8"))
        event_type = payload.get("type")
        data = payload.get("data") or {}
        order_id = int(data["order_id"])
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed payload")

    if event_type != "payment.succeeded":
        # For the assignment, we accept only one event type.
        raise HTTPException(status_code=400, detail="Unsupported event type")

    # 4) find order & update status (idempotent)
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order = _mark_paid(order, db)

    return {
        "detail": "ok",
        "order": {"id": order.id, "status": order.status},
    }
