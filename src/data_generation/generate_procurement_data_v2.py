"""NovaTech Industries — Checkpoint 2.6 Step 3.
Create reproducible purchasing requests and supplier quotations from v2 reference data.
Run from the project root: python3 src/data_generation/generate_procurement_data_v2.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 2027
EVALUATION_DATE = date(2026, 10, 15)
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / 'data' / 'synthetic' / 'v2'
rng = random.Random(SEED)


def read_csv(name):
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f'Missing {path}. Run the v2 reference generator first.')
    with path.open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def write_csv(name, rows):
    path = DATA_DIR / name
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'Created {name}: {len(rows)} records')


def generate():
    suppliers = read_csv('suppliers.csv')
    products = read_csv('products.csv')
    listings = read_csv('supplier_products.csv')
    supplier_by_id = {s['supplier_id']: s for s in suppliers}
    product_ids = {p['product_id'] for p in products}
    eligible_products = sorted({r['product_id'] for r in listings if supplier_by_id[r['supplier_id']]['status'] == 'ACTIVE'})
    if len(eligible_products) < 6:
        raise ValueError('Need at least six products with active suppliers.')

    requisitions, quotations, quotation_items = [], [], []
    quote_number = 0
    # One requisition per selected product; use its real supplier-product links.
    for index, product_id in enumerate(rng.sample(eligible_products, 6), start=1):
        request_id = f'REQ{index:03d}'
        quantity = rng.choice([10, 20, 30])
        requisitions.append({
            'requisition_id': request_id,
            'product_id': product_id,
            'requested_quantity': quantity,
            'request_date': EVALUATION_DATE.isoformat(),
            'required_delivery_date': (EVALUATION_DATE + timedelta(days=45)).isoformat(),
            'status': 'OPEN',
        })
        options = [r for r in listings if r['product_id'] == product_id]
        # Select up to three real supplier-product relationships.
        for listing in sorted(options, key=lambda r: r['supplier_id'])[:3]:
            quote_number += 1
            quote_id = f'QUO{quote_number:03d}'
            # First quote is deliberately expired, to exercise future eligibility rules.
            expiry = EVALUATION_DATE - timedelta(days=1) if quote_number == 1 else EVALUATION_DATE + timedelta(days=20)
            quotations.append({
                'quotation_id': quote_id,
                'requisition_id': request_id,
                'supplier_id': listing['supplier_id'],
                'quotation_date': (EVALUATION_DATE - timedelta(days=10)).isoformat(),
                'valid_until': expiry.isoformat(),
                'currency': 'EUR',
                'status': 'RECEIVED',
            })
            quoted_quantity = max(quantity, int(listing['minimum_order_quantity']))
            quotation_items.append({
                'quotation_id': quote_id,
                'product_id': product_id,
                'quoted_quantity': quoted_quantity,
                'unit_price_eur': f'{rng.uniform(30, 250):.2f}',
                'freight_eur': f'{rng.uniform(20, 180):.2f}',
                'duties_eur': '0.00',
                'other_fees_eur': f'{rng.uniform(0, 35):.2f}',
                'lead_time_days': rng.randint(3, 40),
            })

    requisition_ids = {r['requisition_id'] for r in requisitions}
    quotation_ids = {q['quotation_id'] for q in quotations}
    assert len(requisition_ids) == len(requisitions) == 6
    assert len(quotation_ids) == len(quotations) == len(quotation_items)
    assert all(q['requisition_id'] in requisition_ids for q in quotations)
    assert all(q['supplier_id'] in supplier_by_id for q in quotations)
    assert all(i['quotation_id'] in quotation_ids and i['product_id'] in product_ids for i in quotation_items)
    req_by_id = {r['requisition_id']: r for r in requisitions}
    item_by_quote = {i['quotation_id']: i for i in quotation_items}
    listing_pairs = {(r['supplier_id'], r['product_id']) for r in listings}
    assert all((q['supplier_id'], item_by_quote[q['quotation_id']]['product_id']) in listing_pairs for q in quotations)
    assert all(item_by_quote[q['quotation_id']]['product_id'] == req_by_id[q['requisition_id']]['product_id'] for q in quotations)
    assert all(int(i['quoted_quantity']) >= int(req_by_id[next(q['requisition_id'] for q in quotations if q['quotation_id'] == i['quotation_id'])]['requested_quantity']) for i in quotation_items)
    assert all(float(i['unit_price_eur']) > 0 and int(i['lead_time_days']) > 0 for i in quotation_items)

    write_csv('purchase_requisitions.csv', requisitions)
    write_csv('quotations.csv', quotations)
    write_csv('quotation_items.csv', quotation_items)
    print('Validation passed: IDs, references, product matching, quantities, and prices.')
    print(f'Reproducible generation seed: {SEED}')
    print('Scenario: QUO001 has an expired validity date (intentional test case).')


if __name__ == '__main__':
    generate()
