"""NovaTech checkpoint 2.6 step 4: deterministic quotation eligibility and EUR cost review.
Run: python3 src/analysis/analyze_quotation_eligibility_v2.py
"""
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'synthetic' / 'v2'
OUTPUT = ROOT / 'data' / 'analysis' / 'v2'


def load(name):
    with (DATA / name).open(newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))


def money(value):
    amount = Decimal(value)
    if not amount.is_finite() or amount < 0:
        raise ValueError(f'Invalid monetary amount: {value}')
    return amount


def analyze():
    suppliers = {r['supplier_id']: r for r in load('suppliers.csv')}
    listings = {(r['supplier_id'], r['product_id']): r for r in load('supplier_products.csv')}
    requisitions = {r['requisition_id']: r for r in load('purchase_requisitions.csv')}
    quotations = load('quotations.csv')
    items = load('quotation_items.csv')
    items_by_quote = {r['quotation_id']: r for r in items}
    if len(items_by_quote) != len(items) or len({q['quotation_id'] for q in quotations}) != len(quotations):
        raise ValueError('Duplicate quotation or quotation item ID')
    if set(items_by_quote) != {q['quotation_id'] for q in quotations}:
        raise ValueError('Every quotation must have exactly one item for this dataset version')

    rows = []
    for quote in quotations:
        qid = quote['quotation_id']
        req = requisitions[quote['requisition_id']]
        item = items_by_quote[qid]
        supplier = suppliers[quote['supplier_id']]
        listing = listings[(quote['supplier_id'], item['product_id'])]
        if item['product_id'] != req['product_id']:
            raise ValueError(f'Product mismatch for {qid}')
        if quote['currency'] != 'EUR':
            raise ValueError(f'No exchange rate available for {qid}; only EUR is supported in this step')
        requested = int(req['requested_quantity'])
        quoted = int(item['quoted_quantity'])
        minimum = int(listing['minimum_order_quantity'])
        available = int(listing['available_quantity'])
        lead_days = int(item['lead_time_days'])
        if min(requested, quoted, minimum, lead_days) <= 0 or available < 0:
            raise ValueError(f'Invalid quantities or lead time for {qid}')
        unit = money(item['unit_price_eur'])
        freight = money(item['freight_eur'])
        duties = money(item['duties_eur'])
        fees = money(item['other_fees_eur'])
        total = unit * quoted + freight + duties + fees
        request_date = date.fromisoformat(req['request_date'])
        quotation_date = date.fromisoformat(quote['quotation_date'])
        # No decision timestamp exists in v2. Use issuance as a provisional
        # evaluation date; do not claim this establishes later validity.
        evaluation_date = quotation_date
        expected_date = evaluation_date + timedelta(days=lead_days)
        required_date = date.fromisoformat(req['required_delivery_date'])
        expiry = date.fromisoformat(quote['valid_until'])
        reasons = []
        if quotation_date < request_date:
            reasons.append('QUOTATION_PREDATES_REQUISITION')
        if expiry < quotation_date:
            reasons.append('QUOTATION_EXPIRES_BEFORE_ISSUANCE')
        if supplier['status'] != 'ACTIVE':
            reasons.append('INACTIVE_SUPPLIER')
        if quote['status'] != 'RECEIVED':
            reasons.append('INVALID_QUOTATION_STATUS')
        if expiry < evaluation_date:
            reasons.append('EXPIRED_QUOTATION')
        if quoted < requested:
            reasons.append('INSUFFICIENT_QUOTED_QUANTITY')
        if quoted < minimum:
            reasons.append('BELOW_MINIMUM_ORDER')
        if quoted > available:
            reasons.append('INSUFFICIENT_AVAILABLE_STOCK')
        if expected_date > required_date:
            reasons.append('LATE_DELIVERY')
        # Category approval, quality/compliance and performance evidence not yet modeled.
        # Therefore passing checks is preliminary, never an approval or recommendation.
        rows.append({
            'quotation_id': qid, 'requisition_id': quote['requisition_id'],
            'supplier_id': quote['supplier_id'], 'product_id': item['product_id'],
            'requested_quantity': requested, 'quoted_quantity': quoted,
            'unit_price_eur': f'{unit:.2f}', 'total_cost_eur': f'{total:.2f}',
            'expected_delivery_date': expected_date.isoformat(),
            'required_delivery_date': required_date.isoformat(),
            'preliminary_status': 'BLOCKED' if reasons else 'PENDING_REVIEW',
            'reasons': ';'.join(reasons) if reasons else 'CATEGORY_COMPLIANCE_AND_PERFORMANCE_NOT_VERIFIED',
        })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / 'quotation_eligibility_results.csv'
    with destination.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    blocked = sum(r['preliminary_status'] == 'BLOCKED' for r in rows)
    print(f'Analyzed quotations: {len(rows)}')
    print(f'Blocked by available checks: {blocked}')
    print(f'Pending manual/compliance review: {len(rows) - blocked}')
    print(f'Created {destination.relative_to(ROOT)}')
    print('No supplier recommendation issued: weighted scoring and full eligibility are not implemented.')
    print('Expiration is checked at quotation issuance; a later purchasing decision date is not modeled in v2.')
    return rows


if __name__ == '__main__':
    analyze()
