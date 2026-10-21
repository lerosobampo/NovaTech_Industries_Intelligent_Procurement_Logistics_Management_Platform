"""NovaTech Industries - Checkpoint 2.6, Step 2.
Generate reproducible, related synthetic reference datasets.
Run from the project root:
    python3 src/data_generation/generate_reference_data_v2.py
"""

import csv
import random
from pathlib import Path

SEED = 2026
rng = random.Random(SEED)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic" / "v2"

SUPPLIER_NAMES = [
    "EuroParts GmbH", "Shenzhen Components", "Nordic Industrial AB",
    "GlobalTech Mexico", "Delta Controls BV", "Alpine Systems AG",
    "Baltic Automation OÜ", "Pacific Circuit Ltd", "Iberian Drives SL",
    "Rhein Mechanical GmbH", "Orion Electronics Inc", "Polaris Supply AS",
]
COUNTRIES = [
    "Germany", "China", "Sweden", "Mexico", "Netherlands", "Switzerland",
    "Estonia", "Taiwan", "Spain", "Germany", "United States", "Norway",
]
CATEGORIES = ["Sensors", "Motors", "Controllers", "Connectors"]


def write_csv(filename, fieldnames, rows):
    path = OUTPUT_DIR / filename
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {filename}: {len(rows)} records")


def generate():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    suppliers = [
        {
            "supplier_id": f"SUP{i:03d}",
            "supplier_name": name,
            "country": COUNTRIES[i - 1],
            "status": "ACTIVE" if i <= 10 else "INACTIVE",
        }
        for i, name in enumerate(SUPPLIER_NAMES, start=1)
    ]

    products = [
        {
            "product_id": f"PRD{i:03d}",
            "sku": f"NT-{i:04d}",
            "product_name": f"Industrial Component {i:02d}",
            "category": CATEGORIES[(i - 1) % len(CATEGORIES)],
            "unit_of_measure": "EA",
        }
        for i in range(1, 21)
    ]

    # Guarantee every product is linked to at least one supplier.
    pairs = {(i % 12, i) for i in range(20)}
    all_pairs = [(s, p) for s in range(12) for p in range(20)]
    remaining = [pair for pair in all_pairs if pair not in pairs]
    pairs.update(rng.sample(remaining, 45 - len(pairs)))

    supplier_products = []
    for supplier_index, product_index in sorted(pairs):
        supplier_products.append({
            "supplier_id": suppliers[supplier_index]["supplier_id"],
            "product_id": products[product_index]["product_id"],
            "minimum_order_quantity": rng.choice([1, 5, 10, 20]),
            "available_quantity": rng.randint(20, 500),
        })

    # Validate data BEFORE writing it to disk.
    supplier_ids = {row["supplier_id"] for row in suppliers}
    product_ids = {row["product_id"] for row in products}
    relationships = {
        (row["supplier_id"], row["product_id"])
        for row in supplier_products
    }
    assert len(suppliers) == len(supplier_ids) == 12
    assert len(products) == len(product_ids) == 20
    assert len(supplier_products) == len(relationships) == 45
    assert all(row["supplier_id"] in supplier_ids for row in supplier_products)
    assert all(row["product_id"] in product_ids for row in supplier_products)
    assert all(row["minimum_order_quantity"] > 0 for row in supplier_products)
    assert all(row["available_quantity"] >= 0 for row in supplier_products)
    assert {row["product_id"] for row in supplier_products} == product_ids

    write_csv("suppliers.csv", list(suppliers[0]), suppliers)
    write_csv("products.csv", list(products[0]), products)
    write_csv("supplier_products.csv", list(supplier_products[0]), supplier_products)
    print("Validation passed: unique IDs, valid relationships, valid quantities.")
    print(f"Reproducible generation seed: {SEED}")


if __name__ == "__main__":
    generate()
