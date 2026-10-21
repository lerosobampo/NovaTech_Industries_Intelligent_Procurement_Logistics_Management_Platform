#!/usr/bin/env python3
"""NovaTech 2.12: historical eligibility with explicitly synthetic evidence.

Reads v3 synthetic inputs and writes data/analysis/v4/supplier_evaluation_results.csv.
Never treats SYNTHETIC_ASSUMPTION records as verified approval.
Decision cutoff is the latest valid quotation issue date for each requisition:
a comparison proxy, NOT a documented purchasing decision.
"""
import csv
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "synthetic" / "v3"
OUT = ROOT / "data" / "analysis" / "v4" / "supplier_evaluation_results.csv"
WEIGHTS = {"cost": Decimal(".40"), "delivery": Decimal(".25"),
           "quality": Decimal(".20"), "reliability": Decimal(".15")}
MIN_INSPECTED = 100
MIN_DELIVERIES = 10
SYNTHETIC_PREFIX = "SYNTHETIC_"


def read(name, required):
    path = DATA / name
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{name}: missing columns {sorted(missing)}")
        return list(reader)


def index(rows, keys, name):
    result = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        if key in result:
            raise ValueError(f"{name}: duplicate key {key}")
        result[key] = row
    return result


def day(value, label):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: invalid date {value!r}") from exc


def number(value, label, positive=False):
    try:
        n = Decimal(value)
    except (TypeError, InvalidOperation) as exc:
        raise ValueError(f"{label}: invalid number {value!r}") from exc
    if not n.is_finite() or n < 0 or (positive and n == 0):
        raise ValueError(f"{label}: out-of-range number {value!r}")
    return n


def history_at(rows, cutoff, key, label):
    """Latest effective, recorded-by-cutoff row. Empty end = open interval.

    Returns (record, issue). A synthetic source is *never* verified provenance.
    """
    candidates = []
    for row in rows:
        start = day(row["effective_from"], f"{label}.effective_from")
        end = day(row["effective_to"], f"{label}.effective_to") if row["effective_to"] else None
        recorded = day(row["recorded_at"], f"{label}.recorded_at")
        if end is not None and end <= start:
            raise ValueError(f"{label}: invalid effective interval")
        if start <= cutoff and (end is None or cutoff < end) and recorded <= cutoff:
            candidates.append((start, recorded, row))
    if not candidates:
        return None, f"{label}_HISTORY_MISSING"
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    if len(candidates) > 1 and candidates[0][:2] == candidates[1][:2]:
        raise ValueError(f"{label}: ambiguous history for {key}")
    row = candidates[0][2]
    evidence = row["evidence_source"].strip().upper()
    if not evidence or evidence.startswith(SYNTHETIC_PREFIX):
        return row, f"{label}_SYNTHETIC_OR_UNVERIFIED"
    # A non-synthetic label is not independently verified either; requires external validation.
    return row, f"{label}_SOURCE_NOT_INDEPENDENTLY_VERIFIED"


def performance_at(supplier, cutoff, deliveries, inspections):
    start = cutoff - timedelta(days=365)
    completed = on_time = inspected = accepted = 0
    for r in deliveries:
        if r["supplier_id"] != supplier or r["status"].strip().upper() not in {"COMPLETED", "DELIVERED"}:
            continue
        actual = day(r["actual_delivery_date"], "actual_delivery_date")
        planned = day(r["planned_delivery_date"], "planned_delivery_date")
        if not start <= actual <= cutoff:
            continue
        expected = actual <= planned
        flag = r["on_time"].strip().lower()
        if flag not in {"true", "false", "1", "0", "yes", "no"}:
            raise ValueError(f"{r['delivery_id']}: invalid on_time")
        if (flag in {"true", "1", "yes"}) != expected:
            raise ValueError(f"{r['delivery_id']}: on_time disagrees with dates")
        completed += 1
        on_time += int(expected)
    for r in inspections:
        if r["supplier_id"] != supplier:
            continue
        inspected_at = day(r["inspection_date"], "inspection_date")
        if not start <= inspected_at <= cutoff:
            continue
        total = number(r["inspected_units"], "inspected_units", True)
        good = number(r["accepted_units"], "accepted_units")
        rejected = number(r["rejected_units"], "rejected_units")
        if total != good + rejected:
            raise ValueError(f"{r['inspection_id']}: inconsistent inspection units")
        inspected += int(total)
        accepted += int(good)
    return {
        "inspected_units": inspected, "completed_deliveries": completed,
        "quality_score": Decimal(100)*accepted/inspected if inspected else None,
        "reliability_score": Decimal(100)*on_time/completed if completed else None,
        "sufficient": inspected >= MIN_INSPECTED and completed >= MIN_DELIVERIES
    }


def evaluate():
    suppliers = index(read("suppliers.csv", ["supplier_id"]), ["supplier_id"], "suppliers")
    products = index(read("products.csv", ["product_id", "category"]), ["product_id"], "products")
    reqs = index(read("purchase_requisitions.csv", ["requisition_id", "product_id", "requested_quantity",
                                                   "request_date", "required_delivery_date"]),
                 ["requisition_id"], "requisitions")
    quotes = read("quotations.csv", ["quotation_id", "requisition_id", "supplier_id",
                                    "quotation_date", "valid_until", "status"])
    index(quotes, ["quotation_id"], "quotations")
    items = index(read("quotation_items.csv", ["quotation_id", "product_id", "quoted_quantity",
                                               "unit_price_eur", "freight_eur", "duties_eur",
                                               "other_fees_eur", "lead_time_days"]),
                  ["quotation_id"], "quotation_items")
    links = index(read("supplier_products.csv", ["supplier_id", "product_id"]),
                  ["supplier_id", "product_id"], "supplier_products")
    status_history = read("supplier_status_history.csv",
                          ["supplier_id", "status", "effective_from", "effective_to", "recorded_at", "evidence_source"])
    compliance_history = read("supplier_compliance_history.csv",
                              ["supplier_id", "category", "approval_status", "valid_until",
                               "effective_from", "effective_to", "recorded_at", "evidence_source"])
    inventory_history = read("supplier_inventory_history.csv",
                             ["supplier_id", "product_id", "available_quantity", "minimum_order_quantity",
                              "effective_from", "effective_to", "recorded_at", "evidence_source"])
    deliveries = read("supplier_deliveries.csv",
                      ["delivery_id", "supplier_id", "planned_delivery_date", "actual_delivery_date", "on_time", "status"])
    inspections = read("supplier_quality_inspections.csv",
                       ["inspection_id", "supplier_id", "inspection_date", "inspected_units",
                        "accepted_units", "rejected_units"])
    index(deliveries, ["delivery_id"], "deliveries")
    index(inspections, ["inspection_id"], "inspections")

    # A malformed quote cannot move a requisition's shared cutoff.
    cutoffs = {}
    for q in quotes:
        qid, rid = q["quotation_id"], q["requisition_id"]
        if (rid,) not in reqs or (qid,) not in items or (q["supplier_id"],) not in suppliers:
            raise ValueError(f"{qid}: missing foreign key")
        issued = day(q["quotation_date"], f"{qid}.quotation_date")
        requested = day(reqs[(rid,)]["request_date"], f"{rid}.request_date")
        if issued >= requested:
            cutoffs[rid] = max(cutoffs.get(rid, issued), issued)

    output = []
    for q in quotes:
        qid, rid, sid = q["quotation_id"], q["requisition_id"], q["supplier_id"]
        req, item = reqs[(rid,)], items[(qid,)]
        pid = req["product_id"]
        if (pid,) not in products or item["product_id"] != pid:
            raise ValueError(f"{qid}: product mismatch")
        category = products[(pid,)]["category"]
        cutoff = cutoffs.get(rid, day(req["request_date"], f"{rid}.request_date"))
        issued = day(q["quotation_date"], f"{qid}.quotation_date")
        expiry = day(q["valid_until"], f"{qid}.valid_until")
        requested = day(req["request_date"], f"{rid}.request_date")
        needed = day(req["required_delivery_date"], f"{rid}.required_delivery_date")
        qty = number(req["requested_quantity"], "requested_quantity", True)
        quoted_qty = number(item["quoted_quantity"], "quoted_quantity", True)
        lead = number(item["lead_time_days"], "lead_time_days", True)
        cost = quoted_qty * number(item["unit_price_eur"], "unit_price_eur")
        for field in ("freight_eur", "duties_eur", "other_fees_eur"):
            cost += number(item[field], field)
        if cost <= 0:
            raise ValueError(f"{qid}: nonpositive total cost")

        blocked, review = [], []
        if issued < requested:
            blocked.append("QUOTATION_PREDATES_REQUISITION")
        if expiry < issued:
            blocked.append("QUOTATION_EXPIRY_BEFORE_ISSUE")
        if expiry < cutoff:
            blocked.append("QUOTATION_EXPIRED_AT_CUTOFF")
        if q["status"].strip().upper() != "RECEIVED":
            blocked.append("INVALID_QUOTATION_STATUS")
        if quoted_qty < qty:
            blocked.append("INSUFFICIENT_QUOTED_QUANTITY")
        if issued + timedelta(days=int(lead)) > needed:
            blocked.append("DELIVERY_AFTER_REQUIRED_DATE")
        if (sid, pid) not in links:
            blocked.append("SUPPLIER_PRODUCT_RELATIONSHIP_MISSING")

        sh, sh_issue = history_at(
            [r for r in status_history if r["supplier_id"] == sid], cutoff, sid, "SUPPLIER_STATUS")
        ch, ch_issue = history_at(
            [r for r in compliance_history if r["supplier_id"] == sid and r["category"] == category],
            cutoff, (sid, category), "CATEGORY_COMPLIANCE")
        ih, ih_issue = history_at(
            [r for r in inventory_history if r["supplier_id"] == sid and r["product_id"] == pid],
            cutoff, (sid, pid), "INVENTORY")
        for row, issue in ((sh, sh_issue), (ch, ch_issue), (ih, ih_issue)):
            if issue:
                review.append(issue)
        if sh is not None and sh["status"].strip().upper() != "ACTIVE":
            blocked.append("INACTIVE_SUPPLIER")
        if ch is not None:
            if ch["approval_status"].strip().upper() != "APPROVED":
                blocked.append("CATEGORY_COMPLIANCE_NOT_APPROVED")
            if day(ch["valid_until"], "compliance.valid_until") < cutoff:
                blocked.append("CATEGORY_COMPLIANCE_EXPIRED")
        if ih is not None:
            minimum = number(ih["minimum_order_quantity"], "minimum_order_quantity", True)
            available = number(ih["available_quantity"], "available_quantity")
            if quoted_qty < minimum:
                blocked.append("BELOW_MINIMUM_ORDER")
            if quoted_qty > available:
                blocked.append("INSUFFICIENT_AVAILABLE_STOCK")
        perf = performance_at(sid, cutoff, deliveries, inspections)
        if not perf["sufficient"]:
            review.append("INSUFFICIENT_PERFORMANCE_HISTORY")
        # Latest quotation date is a proxy, not a verified purchasing decision.
        review.append("DECISION_TIMESTAMP_NOT_VERIFIED")
        reasons = list(dict.fromkeys(blocked + review))
        status = "BLOCKED" if blocked else "REVIEW_REQUIRED" if review else "ELIGIBLE_FOR_ANALYSIS"
        output.append({
            "quotation_id": qid, "requisition_id": rid, "supplier_id": sid,
            "product_id": pid, "category": category, "evaluation_as_of": cutoff.isoformat(),
            "cutoff_basis": "LATEST_QUOTATION_DATE_PROXY",
            "evidence_classification": "SYNTHETIC_UNVERIFIED",
            "total_cost_eur": f"{cost:.2f}", "lead_time_days": str(int(lead)),
            "inspected_units": str(perf["inspected_units"]),
            "completed_deliveries": str(perf["completed_deliveries"]),
            "quality_score": f"{perf['quality_score']:.2f}" if perf["quality_score"] is not None else "",
            "reliability_score": f"{perf['reliability_score']:.2f}" if perf["reliability_score"] is not None else "",
            "evaluation_status": status, "reasons": ";".join(reasons),
            "cost_score": "", "delivery_score": "", "weighted_score": "",
            "recommendation_status": "NO_AUTOMATIC_APPROVAL"
        })
    groups = defaultdict(list)
    for r in output:
        if r["evaluation_status"] == "ELIGIBLE_FOR_ANALYSIS":
            groups[r["requisition_id"]].append(r)
    for group in groups.values():
        min_cost = min(Decimal(r["total_cost_eur"]) for r in group)
        min_lead = min(Decimal(r["lead_time_days"]) for r in group)
        for r in group:
            c = Decimal(100)*min_cost/Decimal(r["total_cost_eur"])
            d = Decimal(100)*min_lead/Decimal(r["lead_time_days"])
            score = (WEIGHTS["cost"]*c + WEIGHTS["delivery"]*d
                     + WEIGHTS["quality"]*Decimal(r["quality_score"])
                     + WEIGHTS["reliability"]*Decimal(r["reliability_score"]))
            r["cost_score"], r["delivery_score"], r["weighted_score"] = f"{c:.2f}", f"{d:.2f}", f"{score:.2f}"
        ranked = sorted(group, key=lambda r: (-Decimal(r["weighted_score"]),
                                              Decimal(r["total_cost_eur"]), int(r["lead_time_days"]),
                                              r["quotation_id"]))
        ranked[0]["recommendation_status"] = "TOP_RANKED_PENDING_HUMAN_APPROVAL"
        for r in ranked[1:]:
            r["recommendation_status"] = "RANKED_ALTERNATIVE"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0]) if output else ["quotation_id"])
        writer.writeheader()
        writer.writerows(output)
    print(f"Created {OUT.relative_to(ROOT)}: {len(output)} records")
    for status in ("ELIGIBLE_FOR_ANALYSIS", "REVIEW_REQUIRED", "BLOCKED"):
        print(f"{status}: {sum(r['evaluation_status'] == status for r in output)}")
    print("Historical source labels are unverified; no purchasing approval is issued.")
    return output


if __name__ == "__main__":
    evaluate()
