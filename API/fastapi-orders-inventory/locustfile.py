from locust import HttpUser, task, between
from uuid import uuid4
import random

class ApiUser(HttpUser):
    wait_time = between(0.5, 2.0)
    # Point Locust to your deployed base URL with -H, e.g. `-H https://<your-service>.onrender.com`

    @task(5)
    def list_products(self):
        self.client.get("/products", name="GET /products")

    @task(2)
    def create_product(self):
        # Unique SKU each time so we don't hit 409 conflicts
        sku_suffix = uuid4().hex[:8]
        payload = {"sku": f"SKU-{sku_suffix}", "name": "Load", "price": 9.99, "stock": random.randint(1, 5)}
        self.client.post("/products", json=payload, name="POST /products")

    @task(1)
    def create_order_for_random_product(self):
        # Try to order 1 unit of a random product if any exist
        r = self.client.get("/products", name="GET /products (for order)")
        if r.ok:
            items = r.json()
            if items:
                product_id = random.choice(items)["id"]
                self.client.post("/orders", json={"product_id": product_id, "quantity": 1}, name="POST /orders")
