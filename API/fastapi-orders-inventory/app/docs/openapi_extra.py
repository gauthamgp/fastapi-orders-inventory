# Centralized OpenAPI extras (tags, descriptions, external docs)
tags_metadata = [
    {
        "name": "products",
        "description": "Product catalog CRUD. Use for creating, listing, and maintaining inventory.",
        "externalDocs": {
            "description": "CRUD basics",
            "url": "https://developer.mozilla.org/en-US/docs/Glossary/CRUD"
        },
    },
    {
        "name": "orders",
        "description": "Order lifecycle. Create pending orders, update status (PAID, SHIPPED, CANCELED).",
    },
    {
        "name": "meta",
        "description": "Service health and meta endpoints.",
    },
]
