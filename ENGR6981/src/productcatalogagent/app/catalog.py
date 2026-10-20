import json
import os

PRODUCTS_FILE = os.getenv("PRODUCTS_FILE", os.path.join(os.path.dirname(__file__), "products.json"))


class LocalCatalog:
    """In-process product catalog, same interface as ProductCatalogGrpcClient.
    Loads the Online Boutique products.json so the agent needs no backend service."""

    def __init__(self, path: str = PRODUCTS_FILE):
        with open(path) as f:
            raw = json.load(f)["products"]
        self.products = [self._to_dict(p) for p in raw]

    def _to_dict(self, p):
        price = p.get("priceUsd", {})
        return {
            "id": p["id"],
            "name": p["name"],
            "description": p["description"],
            "picture": p.get("picture", ""),
            "categories": list(p.get("categories", [])),
            "price_usd": {
                "currency_code": price.get("currencyCode", ""),
                "units": price.get("units", 0),
                "nanos": price.get("nanos", 0),
            }
        }

    def list_products(self):
        return [dict(p) for p in self.products]

    def get_product(self, product_id: str):
        for p in self.products:
            if p["id"] == product_id:
                return dict(p)
        raise KeyError(product_id)

    def search_products(self, query: str):
        q = query.lower()
        return [dict(p) for p in self.products
                if q in p["name"].lower() or q in p["description"].lower()]
