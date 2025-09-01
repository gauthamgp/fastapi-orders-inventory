import os, sys, json, time
import requests

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

def jprint(resp):
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)

def assert_status(resp, expected):
    if resp.status_code != expected:
        print("Unexpected status:", resp.status_code)
        jprint(resp)
        sys.exit(1)

def main():
    # 1) Health
    r = requests.get(f"{BASE_URL}/health")
    assert_status(r, 200)

    # 2) Create product
    prod_payload = {"sku":"SKU-500","name":"Widget","price":9.99,"stock":3}
    r = requests.post(f"{BASE_URL}/products", json=prod_payload)
    assert_status(r, 201)
    product = r.json()
    pid = product["id"]

    # 3) Create order (2 units)
    order_payload = {"product_id": pid, "quantity": 2}
    r = requests.post(f"{BASE_URL}/orders", json=order_payload)
    assert_status(r, 201)
    order = r.json()
    oid = order["id"]

    # 4) Check order
    r = requests.get(f"{BASE_URL}/orders/{oid}")
    assert_status(r, 200)

    # 5) Transition to PAID, then SHIPPED
    r = requests.put(f"{BASE_URL}/orders/{oid}", json={"status": "PAID"})
    assert_status(r, 200)
    r = requests.put(f"{BASE_URL}/orders/{oid}", json={"status": "SHIPPED"})
    assert_status(r, 200)

    print("✅ Smoke OK. Final order:")
    jprint(r)

if __name__ == "__main__":
    main()
