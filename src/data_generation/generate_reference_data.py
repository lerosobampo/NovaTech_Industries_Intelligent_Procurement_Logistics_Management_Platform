from pathlib import Path
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic" / "v1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

suppliers = [
    {"supplier_id": "SUP001", "name": "EuroParts GmbH", "country": "Germany", "status": "active"},
    {"supplier_id": "SUP002", "name": "Shenzhen Components", "country": "China", "status": "active"},
    {"supplier_id": "SUP003", "name": "Nordic Industrial AB", "country": "Sweden", "status": "active"},
]

products = [
    {"product_id": "PRD001", "sku": "SENSOR-100", "name": "Industrial sensor", "category": "sensors"},
    {"product_id": "PRD002", "sku": "CTRL-200", "name": "Control module", "category": "controllers"},
]

supplier_products = [
    {"supplier_id": "SUP001", "product_id": "PRD001", "min_order_qty": 10, "available_qty": 150},
    {"supplier_id": "SUP002", "product_id": "PRD001", "min_order_qty": 20, "available_qty": 400},
    {"supplier_id": "SUP003", "product_id": "PRD002", "min_order_qty": 5, "available_qty": 75},
]


def write_csv(filename, rows):
    if not rows:
        raise ValueError(f"No records provided for {filename}")
    with (OUTPUT_DIR / filename).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {filename}: {len(rows)} records")


supplier_ids = {row["supplier_id"] for row in suppliers}
product_ids = {row["product_id"] for row in products}

assert len(supplier_ids) == len(suppliers), "Duplicate supplier ID"
assert len(product_ids) == len(products), "Duplicate product ID"
assert len({(r["supplier_id"], r["product_id"]) for r in supplier_products}) == len(supplier_products), "Duplicate offering"
assert all(r["supplier_id"] in supplier_ids and r["product_id"] in product_ids for r in supplier_products), "Broken foreign key"
assert all(r["min_order_qty"] > 0 and r["available_qty"] >= 0 for r in supplier_products), "Invalid quantity"

write_csv("suppliers.csv", suppliers)
write_csv("products.csv", products)
write_csv("supplier_products.csv", supplier_products)