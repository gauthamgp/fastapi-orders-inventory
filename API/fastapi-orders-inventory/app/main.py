from fastapi import FastAPI
from app.db.session import create_db_and_tables
from contextlib import asynccontextmanager
from app.core.errors import add_exception_handlers
from app.api.routers import products, orders
from app.docs.openapi_extra import tags_metadata
from app.webhooks import payment as payment_webhook

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables at startup."""
    create_db_and_tables()
    add_exception_handlers(app)
    yield
    # No teardown needed for SQLite


app = FastAPI(
    title="Orders & Inventory API",
    version="0.1.0",
    description=(
        "Tiny store service for **Products** and **Orders**.\n\n"
        "- Products: CRUD with validation and unique SKU\n"
        "- Orders: Atomic stock decrement, status transitions\n"
        "- Error contracts: deterministic JSON shapes"
    ),
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)



@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}

# Routers get plugged in during Part C.

app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(payment_webhook.router, prefix="/webhooks", tags=["webhooks"])
