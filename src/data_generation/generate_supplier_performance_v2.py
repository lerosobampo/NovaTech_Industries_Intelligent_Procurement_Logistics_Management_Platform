"""NovaTech Industries | Checkpoint 2.7: synthetic supplier performance.

Run: python3 src/data_generation/generate_supplier_performance_v2.py
Reads the existing v2 reference datasets and writes three new CSVs to v2.
Standard-library only. Reproducible with seed 2028.
"""
import csv
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

SEED = 2028
AS_OF_DATE = date(2026, 10, 21)  # fixed date for repeatable demonstrations
LOOKBACK_START = date(2025, 10, 21)
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "synthetic" / "v2"
RNG = random.Random(SEED)


def read_csv(filename, required):
    path = DATA / filename
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}; generate reference v2 data first")
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{filename}: missing columns {sorted(missing)}")
        return list(reader)


def write_csv(filename, columns, rows):
    with (DATA / filename).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {filename}: {len(rows)} records")


def generate():
    suppliers = read_csv("suppliers.csv", ["supplier_id", "status"])
    products = read_csv("products.csv", ["product_id", "category"])
    links = read_csv("supplier_products.csv", ["supplier_id", "product_id"])
    supplier_ids = [r["supplier_id"] for r in suppliers]
    supplier_status = {r["supplier_id"]: r["status"].upper() for r in suppliers}
    product_category = {r["product_id"]: r["category"] for r in products}
    if len(supplier_ids) != len(set(supplier_ids)):
        raise ValueError("Duplicate supplier IDs")
    if len(product_category) != len(products):
        raise ValueError("Duplicate product IDs")
    if not suppliers or not links:
        raise ValueError("Expected nonempty suppliers and supplier_products")

    categories_by_supplier = defaultdict(set)
    for link in links:
        sid, pid = link["supplier_id"], link["product_id"]
        if sid not in supplier_status or pid not in product_category:
            raise ValueError(f"Broken supplier_products relationship: {sid}/{pid}")
        categories_by_supplier[sid].add(product_category[pid])

    deliveries, inspections, compliance = [], [], []
    # Intentional edge case: final supplier has too little history for reliable scoring.
    low_history_supplier = supplier_ids[-1]
    for index, sid in enumerate(supplier_ids):
        low_history = sid == low_history_supplier
        n_deliveries = 3 if low_history else 14 + (index % 5)
        for number in range(1, n_deliveries + 1):
            # All dates fall within the fixed trailing 12-month reporting window.
            planned = LOOKBACK_START + timedelta(days=25 + RNG.randint(0, 325))
            delay = RNG.choice([-2, -1, 0, 0, 0, 0, 1, 2, 4])
            actual = planned + timedelta(days=delay)
            # Cap to reporting date so there are no future completed deliveries.
            if actual > AS_OF_DATE:
                actual = AS_OF_DATE
            deliveries.append({
                "delivery_id": f"DEL{len(deliveries)+1:04d}",
                "supplier_id": sid,
                "planned_delivery_date": planned.isoformat(),
                "actual_delivery_date": actual.isoformat(),
                "on_time": "YES" if actual <= planned else "NO",
                "status": "COMPLETED",
            })
        n_inspections = 1 if low_history else 5 + (index % 3)
        for number in range(n_inspections):
            inspected = RNG.randint(8, 25) if low_history else RNG.randint(25, 60)
            rejected = RNG.randint(0, min(4, inspected))
            inspection_date = LOOKBACK_START + timedelta(days=25 + RNG.randint(0, 325))
            inspections.append({
                "inspection_id": f"INS{len(inspections)+1:04d}",
                "supplier_id": sid,
                "inspection_date": inspection_date.isoformat(),
                "inspected_units": inspected,
                "accepted_units": inspected - rejected,
                "rejected_units": rejected,
            })
        for category in sorted(categories_by_supplier[sid]):
            # Deliberate compliance edge cases for eligibility tests.
            if sid == supplier_ids[-2]:
                approval, expiry = "EXPIRED", date(2026, 8, 31)
            elif sid == supplier_ids[-3]:
                approval, expiry = "PENDING", date(2027, 6, 30)
            else:
                approval, expiry = "APPROVED", date(2027, 6, 30)
            compliance.append({
                "supplier_id": sid,
                "category": category,
                "approval_status": approval,
                "valid_until": expiry.isoformat(),
            })

    # Integrity and business-rule checks before any output is written.
    assert len({r["delivery_id"] for r in deliveries}) == len(deliveries)
    assert len({r["inspection_id"] for r in inspections}) == len(inspections)
    assert len({(r["supplier_id"], r["category"]) for r in compliance}) == len(compliance)
    assert all(r["supplier_id"] in supplier_status for r in deliveries + inspections + compliance)
    assert all(r["inspected_units"] == r["accepted_units"] + r["rejected_units"] for r in inspections)
    assert all(r["inspected_units"] > 0 and r["rejected_units"] >= 0 for r in inspections)
    assert all(r["on_time"] == ("YES" if r["actual_delivery_date"] <= r["planned_delivery_date"] else "NO") for r in deliveries)
    assert all(LOOKBACK_START <= date.fromisoformat(r["actual_delivery_date"]) <= AS_OF_DATE for r in deliveries)
    assert all(LOOKBACK_START <= date.fromisoformat(r["inspection_date"]) <= AS_OF_DATE for r in inspections)
    assert all(r["category"] in categories_by_supplier[r["supplier_id"]] for r in compliance)

    write_csv("supplier_deliveries.csv", ["delivery_id", "supplier_id", "planned_delivery_date", "actual_delivery_date", "on_time", "status"], deliveries)
    write_csv("supplier_quality_inspections.csv", ["inspection_id", "supplier_id", "inspection_date", "inspected_units", "accepted_units", "rejected_units"], inspections)
    write_csv("supplier_compliance.csv", ["supplier_id", "category", "approval_status", "valid_until"], compliance)
    print("Validation passed: identifiers, foreign keys, dates, quantities, and compliance categories.")
    print(f"Seed: {SEED}; reporting date: {AS_OF_DATE}; intentional low-history supplier: {low_history_supplier}")
    print("Note: performance and compliance evidence is generated; no supplier score or PO approval is issued.")


if __name__ == "__main__":
    generate()
