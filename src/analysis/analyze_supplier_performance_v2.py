#!/usr/bin/env python3
"""Checkpoint 2.8: audited supplier performance and category compliance metrics."""
import csv
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / 'data' / 'synthetic' / 'v2'
OUTPUT = ROOT / 'data' / 'analysis' / 'v2'
AS_OF = date(2026, 10, 21)  # fixed case-study date; update deliberately
WINDOW_START = date(2025, 10, 21)  # inclusive 12-month reporting window
MIN_INSPECTED = 100  # proposed policy; not yet formally approved
MIN_DELIVERIES = 10  # proposed policy; not yet formally approved


def load(name, required):
    path = INPUT / name
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{name}: missing columns {sorted(missing)}')
        rows = list(reader)
    return rows


def day(value, context):
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f'{context}: invalid ISO date {value!r}') from exc


def integer(value, context):
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{context}: invalid integer {value!r}') from exc
    if result < 0:
        raise ValueError(f'{context}: negative integer {result}')
    return result


def save(name, rows, columns):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / name
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Created {path.relative_to(ROOT)}: {len(rows)} records')


def main():
    suppliers = load('suppliers.csv', ['supplier_id', 'supplier_name', 'status'])
    products = load('products.csv', ['product_id', 'category'])
    supplier_products = load('supplier_products.csv', ['supplier_id', 'product_id'])
    deliveries = load('supplier_deliveries.csv', ['delivery_id', 'supplier_id', 'planned_delivery_date', 'actual_delivery_date', 'on_time', 'status'])
    inspections = load('supplier_quality_inspections.csv', ['inspection_id', 'supplier_id', 'inspection_date', 'inspected_units', 'accepted_units', 'rejected_units'])
    compliance = load('supplier_compliance.csv', ['supplier_id', 'category', 'approval_status', 'valid_until'])

    supplier_ids = [r['supplier_id'] for r in suppliers]
    if len(set(supplier_ids)) != len(supplier_ids):
        raise ValueError('Duplicate supplier IDs')
    known = set(supplier_ids)
    product_categories = {r['product_id']: r['category'] for r in products}
    if len(product_categories) != len(products):
        raise ValueError('Duplicate product IDs')
    for r in supplier_products:
        if r['supplier_id'] not in known or r['product_id'] not in product_categories:
            raise ValueError(f'Invalid supplier-product reference: {r}')

    metrics = defaultdict(lambda: {'completed': 0, 'on_time': 0, 'inspected': 0, 'accepted': 0})
    seen_delivery = set()
    for r in deliveries:
        sid, rid = r['supplier_id'], r['delivery_id']
        if sid not in known or rid in seen_delivery:
            raise ValueError(f'Unknown supplier or duplicate delivery: {rid}')
        seen_delivery.add(rid)
        planned = day(r['planned_delivery_date'], rid)
        actual_raw = r['actual_delivery_date'].strip()
        actual = day(actual_raw, rid) if actual_raw else None
        status = r['status'].strip().lower()
        completed = status in {'completed', 'delivered'}
        if completed and actual is None:
            raise ValueError(f'{rid}: completed delivery has no actual date')
        if not completed or not actual or not WINDOW_START <= actual <= AS_OF:
            continue
        # Actual date is authoritative; on_time field is checked for consistency.
        on_time = actual <= planned
        flag = r['on_time'].strip().lower()
        if flag in {'true', 'false', '1', '0', 'yes', 'no'}:
            reported = flag in {'true', '1', 'yes'}
            if reported != on_time:
                raise ValueError(f'{rid}: on_time flag conflicts with dates')
        metrics[sid]['completed'] += 1
        metrics[sid]['on_time'] += int(on_time)

    seen_inspection = set()
    for r in inspections:
        sid, rid = r['supplier_id'], r['inspection_id']
        if sid not in known or rid in seen_inspection:
            raise ValueError(f'Unknown supplier or duplicate inspection: {rid}')
        seen_inspection.add(rid)
        inspected = integer(r['inspected_units'], rid)
        accepted = integer(r['accepted_units'], rid)
        rejected = integer(r['rejected_units'], rid)
        if inspected == 0 or accepted + rejected != inspected:
            raise ValueError(f'{rid}: inconsistent inspection quantities')
        inspected_date = day(r['inspection_date'], rid)
        if WINDOW_START <= inspected_date <= AS_OF:
            metrics[sid]['inspected'] += inspected
            metrics[sid]['accepted'] += accepted

    performance = []
    for r in suppliers:
        sid = r['supplier_id']
        m = metrics[sid]
        quality_ok = m['inspected'] >= MIN_INSPECTED
        reliability_ok = m['completed'] >= MIN_DELIVERIES
        status = 'EVIDENCE_SUFFICIENT' if quality_ok and reliability_ok else 'REVIEW_REQUIRED'
        performance.append({
            'supplier_id': sid, 'supplier_name': r['supplier_name'], 'supplier_status': r['status'],
            'report_as_of': AS_OF.isoformat(), 'window_start': WINDOW_START.isoformat(),
            'inspected_units': m['inspected'], 'accepted_units': m['accepted'],
            'completed_deliveries': m['completed'], 'on_time_deliveries': m['on_time'],
            'quality_score': f"{100*m['accepted']/m['inspected']:.2f}" if quality_ok else '',
            'reliability_score': f"{100*m['on_time']/m['completed']:.2f}" if reliability_ok else '',
            'evidence_status': status,
            'review_reason': '; '.join(x for x, fail in [
                (f'INSPECTED_UNITS_BELOW_{MIN_INSPECTED}', not quality_ok),
                (f'COMPLETED_DELIVERIES_BELOW_{MIN_DELIVERIES}', not reliability_ok)] if fail)
        })

    # Category-specific approval: report separately; never collapse to supplier-wide approval.
    provided = {(r['supplier_id'], product_categories[r['product_id']]) for r in supplier_products}
    approvals = defaultdict(list)
    for r in compliance:
        key = (r['supplier_id'], r['category'])
        if r['supplier_id'] not in known:
            raise ValueError(f'Compliance references unknown supplier: {key}')
        expiry = day(r['valid_until'], f'compliance {key}')
        approvals[key].append((r['approval_status'].strip().lower(), expiry))
    category_rows = []
    for sid, category in sorted(provided):
        records = approvals.get((sid, category), [])
        valid = [x for x in records if x[0] in {'approved', 'active'} and x[1] >= AS_OF]
        if len(valid) > 1:
            raise ValueError(f'Multiple active approvals for {sid}/{category}')
        status = 'VALID' if valid else ('REVIEW_REQUIRED' if records else 'MISSING')
        category_rows.append({'supplier_id': sid, 'category': category,
                              'compliance_status': status,
                              'valid_until': valid[0][1].isoformat() if valid else '',
                              'report_as_of': AS_OF.isoformat()})

    save('supplier_performance_metrics.csv', performance, list(performance[0]))
    save('supplier_category_compliance.csv', category_rows, list(category_rows[0]))
    print('Validation passed: supplier references, unique events, quantities, dates, and category links.')
    print('Suppliers requiring evidence review:', sum(x['evidence_status'] == 'REVIEW_REQUIRED' for x in performance))
    print('No weighted score, final quotation eligibility, or purchasing approval issued.')


if __name__ == '__main__':
    main()
