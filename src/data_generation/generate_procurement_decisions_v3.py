#!/usr/bin/env python3
"""NovaTech checkpoint 2.13: create simulated, non-authorizing procurement decisions.

Run from any directory after evaluating suppliers with v4.
Inputs: data/synthetic/v3/{purchase_requisitions,quotations}.csv
        data/analysis/v4/supplier_evaluation_results.csv
Output: data/synthetic/v3/procurement_decisions.csv

All decisions are PENDING_REVIEW. No supplier is selected and no PO is issued.
"""
import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "synthetic" / "v3"
EVALUATIONS = ROOT / "data" / "analysis" / "v4" / "supplier_evaluation_results.csv"
OUTPUT = DATA / "procurement_decisions.csv"
DECISION_DATE = date(2026, 10, 17)  # Explicit synthetic scenario assumption


def load(path, required):
    if not path.is_file():
        raise FileNotFoundError(f"Missing input: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name}: missing columns {sorted(missing)}")
        return list(reader)


def parse_date(value, label):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: invalid ISO date {value!r}") from exc


def build_decisions(requisitions, quotations, evaluations, decision_date=DECISION_DATE):
    req_by_id = {}
    for r in requisitions:
        rid = r["requisition_id"]
        if rid in req_by_id:
            raise ValueError(f"Duplicate requisition: {rid}")
        req_by_id[rid] = r

    quote_by_id = {}
    quotes_by_req = defaultdict(list)
    for q in quotations:
        qid, rid = q["quotation_id"], q["requisition_id"]
        if qid in quote_by_id:
            raise ValueError(f"Duplicate quotation: {qid}")
        if rid not in req_by_id:
            raise ValueError(f"{qid}: unknown requisition {rid}")
        issued = parse_date(q["quotation_date"], f"{qid} quotation_date")
        expires = parse_date(q["valid_until"], f"{qid} valid_until")
        requested = parse_date(req_by_id[rid]["request_date"], f"{rid} request_date")
        if issued < requested or expires < issued:
            raise ValueError(f"{qid}: invalid quotation chronology")
        quote_by_id[qid] = q
        quotes_by_req[rid].append(q)

    eval_by_quote = {}
    for e in evaluations:
        qid = e["quotation_id"]
        if qid in eval_by_quote:
            raise ValueError(f"Duplicate evaluation: {qid}")
        if qid not in quote_by_id:
            raise ValueError(f"Evaluation references unknown quotation: {qid}")
        q = quote_by_id[qid]
        if e["requisition_id"] != q["requisition_id"] or e["supplier_id"] != q["supplier_id"]:
            raise ValueError(f"{qid}: evaluation relationship mismatch")
        if e["evaluation_status"] not in {"BLOCKED", "REVIEW_REQUIRED", "ELIGIBLE_FOR_ANALYSIS"}:
            raise ValueError(f"{qid}: unexpected evaluation status")
        if parse_date(e["evaluation_as_of"], f"{qid} evaluation_as_of") > decision_date:
            raise ValueError(f"{qid}: evaluation is dated after the decision")
        eval_by_quote[qid] = e

    if set(eval_by_quote) != set(quote_by_id):
        raise ValueError("Every quotation must have exactly one v4 evaluation")

    decisions = []
    for i, rid in enumerate(sorted(req_by_id), 1):
        req = req_by_id[rid]
        if parse_date(req["request_date"], f"{rid} request_date") > decision_date:
            raise ValueError(f"{rid}: requisition is dated after decision")
        related = quotes_by_req[rid]
        if not related:
            raise ValueError(f"{rid}: no quotations to evaluate")
        if any(parse_date(q["quotation_date"], f"{q['quotation_id']} quotation_date") > decision_date
               for q in related):
            raise ValueError(f"{rid}: quotation issued after decision date")
        statuses = Counter(eval_by_quote[q["quotation_id"]]["evaluation_status"] for q in related)
        valid_on_date = sum(
            parse_date(q["quotation_date"], "quotation_date") <= decision_date
            <= parse_date(q["valid_until"], "valid_until") for q in related
        )
        # v4 evaluations use a proxy cutoff, not a verified decision timestamp.
        # Even eligible quotations cannot be promoted to an operational approval here.
        decisions.append({
            "decision_id": f"DEC{i:03d}",
            "requisition_id": rid,
            "decision_date": decision_date.isoformat(),
            "decision_mode": "SIMULATION",
            "decision_status": "PENDING_REVIEW",
            "selected_quotation_id": "",
            "decision_maker": "SIMULATED_BUYER",
            "decision_reason": "HISTORICAL_EVIDENCE_UNVERIFIED;DECISION_TIMESTAMP_SIMULATED",
            "quotation_count": str(len(related)),
            "quotations_valid_on_decision_date": str(valid_on_date),
            "eligible_count": str(statuses["ELIGIBLE_FOR_ANALYSIS"]),
            "review_required_count": str(statuses["REVIEW_REQUIRED"]),
            "blocked_count": str(statuses["BLOCKED"]),
            "evaluation_source": "data/analysis/v4/supplier_evaluation_results.csv",
            "approval_status": "NOT_AUTHORIZED",
        })
    return decisions


def main():
    requisitions = load(DATA / "purchase_requisitions.csv", ["requisition_id", "request_date"])
    quotations = load(DATA / "quotations.csv",
                      ["quotation_id", "requisition_id", "supplier_id", "quotation_date", "valid_until"])
    evaluations = load(EVALUATIONS,
                       ["quotation_id", "requisition_id", "supplier_id", "evaluation_as_of", "evaluation_status"])
    decisions = build_decisions(requisitions, quotations, evaluations)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(decisions[0]))
        writer.writeheader()
        writer.writerows(decisions)
    print(f"Created {OUTPUT.relative_to(ROOT)}: {len(decisions)} records")
    print(f"Decision date (synthetic assumption): {DECISION_DATE}")
    print("All decisions: SIMULATION / PENDING_REVIEW / NOT_AUTHORIZED")
    print("No supplier selected. No purchase order created.")


if __name__ == "__main__":
    main()
