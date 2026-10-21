#!/usr/bin/env python3
"""Checkpoint 2.12: generate explicitly SYNTHETIC point-in-time evidence.

Reads the existing v3 reference tables and creates three additional history CSVs.
The source tables contain current-state values only. Generated effective dates
are simulation assumptions, NOT recovered historical facts.

Run from anywhere:
    python3 src/data_generation/generate_historical_evidence_v3.py

Use --overwrite to replace previously generated history files.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "synthetic" / "v3"
ASSUMED_EFFECTIVE_FROM = date(2026, 1, 1)
ASSUMED_RECORDED_AT = date(2026, 1, 2)
SOURCE_NOTE = "SYNTHETIC_ASSUMPTION_FROM_V3_SNAPSHOT"


def load_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing source file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path.name}: missing columns {sorted(required - set(reader.fieldnames or []))}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path.name} is empty")
    return rows


def unique(rows: list[dict[str, str]], columns: tuple[str, ...], filename: str) -> None:
    seen = set()
    for row in rows:
        key = tuple(row[c] for c in columns)
        if not all(key) or key in seen:
            raise ValueError(f"{filename}: missing or duplicate key {key}")
        seen.add(key)


def generate(data_dir: Path = DATA, overwrite: bool = False) -> dict[str, int]:
    suppliers = load_csv(data_dir / "suppliers.csv", {"supplier_id", "status"})
    compliance = load_csv(data_dir / "supplier_compliance.csv", {"supplier_id", "category", "approval_status", "valid_until"})
    inventory = load_csv(data_dir / "supplier_products.csv", {"supplier_id", "product_id", "minimum_order_quantity", "available_quantity"})
    unique(suppliers, ("supplier_id",), "suppliers.csv")
    unique(compliance, ("supplier_id", "category"), "supplier_compliance.csv")
    unique(inventory, ("supplier_id", "product_id"), "supplier_products.csv")
    known_suppliers = {r["supplier_id"] for r in suppliers}
    for row in compliance + inventory:
        if row["supplier_id"] not in known_suppliers:
            raise ValueError(f"Unknown supplier ID: {row['supplier_id']}")

    effective = ASSUMED_EFFECTIVE_FROM.isoformat()
    recorded = ASSUMED_RECORDED_AT.isoformat()
    status_rows = [
        {"supplier_id": r["supplier_id"], "status": r["status"],
         "effective_from": effective, "effective_to": "", "recorded_at": recorded,
         "evidence_source": SOURCE_NOTE}
        for r in suppliers
    ]
    compliance_rows = []
    for r in compliance:
        expiration = date.fromisoformat(r["valid_until"])
        # A past expiration date is retained; it does not prove a later approval.
        compliance_rows.append({
            "supplier_id": r["supplier_id"], "category": r["category"],
            "approval_status": r["approval_status"],
            "effective_from": effective, "effective_to": "",
            "valid_until": expiration.isoformat(), "recorded_at": recorded,
            "evidence_source": SOURCE_NOTE,
        })
    inventory_rows = []
    for r in inventory:
        qty = int(r["available_quantity"])
        moq = int(r["minimum_order_quantity"])
        if qty < 0 or moq < 0:
            raise ValueError(f"Negative inventory or MOQ for {r['supplier_id']}/{r['product_id']}")
        inventory_rows.append({
            "supplier_id": r["supplier_id"], "product_id": r["product_id"],
            "available_quantity": str(qty), "minimum_order_quantity": str(moq),
            "effective_from": effective, "effective_to": "", "recorded_at": recorded,
            "evidence_source": SOURCE_NOTE,
        })

    outputs = {
        "supplier_status_history.csv": (status_rows, ["supplier_id", "status", "effective_from", "effective_to", "recorded_at", "evidence_source"]),
        "supplier_compliance_history.csv": (compliance_rows, ["supplier_id", "category", "approval_status", "effective_from", "effective_to", "valid_until", "recorded_at", "evidence_source"]),
        "supplier_inventory_history.csv": (inventory_rows, ["supplier_id", "product_id", "available_quantity", "minimum_order_quantity", "effective_from", "effective_to", "recorded_at", "evidence_source"]),
    }
    for name in outputs:
        if (data_dir / name).exists() and not overwrite:
            raise FileExistsError(f"{name} exists. Re-run with --overwrite to regenerate it.")
    for name, (rows, fields) in outputs.items():
        with (data_dir / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Created {data_dir / name}: {len(rows)} records")
    print("WARNING: Historical effective dates are synthetic assumptions, not verified provenance.")
    print("Do not use these records to approve real purchasing decisions.")
    return {name: len(rows) for name, (rows, _) in outputs.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true", help="Replace previously generated history files")
    args = parser.parse_args()
    generate(overwrite=args.overwrite)


if __name__ == "__main__":
    main()
