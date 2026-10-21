#!/usr/bin/env python3
"""NovaTech Checkpoint 2.9: join prior outputs and evaluate quotations safely."""
import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'synthetic' / 'v2'
ANALYSIS = ROOT / 'data' / 'analysis' / 'v2'
WEIGHTS = {'cost': Decimal('0.40'), 'delivery': Decimal('0.25'),
           'quality': Decimal('0.20'), 'reliability': Decimal('0.15')}


def read(path, columns):
    if not path.is_file():
        raise FileNotFoundError(f'Missing {path}. Run the earlier checkpoint script first.')
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        missing = set(columns) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{path.name}: missing columns {sorted(missing)}')
        return list(reader)


def index(rows, fields, label):
    result = {}
    for row in rows:
        key = tuple(row[f] for f in fields)
        if key in result:
            raise ValueError(f'{label}: duplicate key {key}')
        result[key] = row
    return result


def number(value, label, positive=False):
    try:
        n = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError(f'{label}: invalid number {value!r}')
    if not n.is_finite() or n < 0 or (positive and n == 0):
        raise ValueError(f'{label}: out of range {value!r}')
    return n


def write(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Created {path.relative_to(ROOT)}: {len(rows)} records')


def main():
    quotes = read(ANALYSIS / 'quotation_eligibility_results.csv',
                  ['quotation_id','requisition_id','supplier_id','product_id','total_cost_eur','preliminary_status','reasons'])
    performance = read(ANALYSIS / 'supplier_performance_metrics.csv',
                       ['supplier_id','quality_score','reliability_score','evidence_status','report_as_of'])
    compliance = read(ANALYSIS / 'supplier_category_compliance.csv',
                      ['supplier_id','category','compliance_status','report_as_of'])
    products = read(DATA / 'products.csv', ['product_id','category'])
    items = read(DATA / 'quotation_items.csv', ['quotation_id','lead_time_days'])
    requisitions = read(DATA / 'purchase_requisitions.csv', ['requisition_id','request_date'])
    q_index = index(quotes, ['quotation_id'], 'quotations')
    p_index = index(performance, ['supplier_id'], 'performance')
    c_index = index(compliance, ['supplier_id','category'], 'compliance')
    product_index = index(products, ['product_id'], 'products')
    item_index = index(items, ['quotation_id'], 'quotation items')
    req_index = index(requisitions, ['requisition_id'], 'requisitions')
    rows = []
    for quote in quotes:
        qid, sid, rid = quote['quotation_id'], quote['supplier_id'], quote['requisition_id']
        if (sid,) not in p_index or (quote['product_id'],) not in product_index or (qid,) not in item_index or (rid,) not in req_index:
            raise ValueError(f'{qid}: missing required foreign key')
        perf = p_index[(sid,)]
        category = product_index[(quote['product_id'],)]['category']
        comp = c_index.get((sid, category))
        reasons = [] if quote['preliminary_status'] == 'PENDING_REVIEW' else [x for x in quote['reasons'].split(';') if x]
        if quote['preliminary_status'] not in {'PENDING_REVIEW','BLOCKED'}:
            raise ValueError(f'{qid}: unexpected preliminary status')
        if not comp or comp['compliance_status'] != 'VALID':
            reasons.append('CATEGORY_COMPLIANCE_NOT_VALID')
        if perf['evidence_status'] != 'EVIDENCE_SUFFICIENT':
            reasons.append('INSUFFICIENT_PERFORMANCE_HISTORY')
        # Earlier analyses are dated 2026-10-21; requests date to 2026-10-15.
        # This is a retrospective case study, not a point-in-time authorization.
        request_day = date.fromisoformat(req_index[(rid,)]['request_date'])
        report_day = date.fromisoformat(perf['report_as_of'])
        if comp and comp['report_as_of'] != perf['report_as_of']:
            raise ValueError(f'{qid}: incompatible compliance/performance reporting dates')
        if report_day < request_day:
            reasons.append('PERFORMANCE_REPORT_PREDATES_REQUEST')
        cost = number(quote['total_cost_eur'], f'{qid} cost', positive=True)
        lead = number(item_index[(qid,)]['lead_time_days'], f'{qid} lead time', positive=True)
        quality = reliability = None
        if perf['evidence_status'] == 'EVIDENCE_SUFFICIENT':
            quality = number(perf['quality_score'], f'{sid} quality')
            reliability = number(perf['reliability_score'], f'{sid} reliability')
            if quality > 100 or reliability > 100:
                raise ValueError(f'{sid}: performance score exceeds 100')
        status = 'BLOCKED' if quote['preliminary_status'] == 'BLOCKED' or 'CATEGORY_COMPLIANCE_NOT_VALID' in reasons or 'PERFORMANCE_REPORT_PREDATES_REQUEST' in reasons else ('REVIEW_REQUIRED' if reasons else 'ELIGIBLE_FOR_ANALYSIS')
        rows.append({'quotation_id': qid, 'requisition_id': rid, 'supplier_id': sid,
                     'product_id': quote['product_id'], 'category': category,
                     'total_cost_eur': f'{cost:.2f}', 'lead_time_days': str(int(lead)),
                     'quality_score': str(quality) if quality is not None else '',
                     'reliability_score': str(reliability) if reliability is not None else '',
                     'evaluation_status': status, 'reasons': ';'.join(dict.fromkeys(reasons)),
                     'cost_score': '', 'delivery_score': '', 'weighted_score': '',
                     'recommendation_status': 'NO_AUTOMATIC_APPROVAL'})

    groups = defaultdict(list)
    for row in rows:
        if row['evaluation_status'] == 'ELIGIBLE_FOR_ANALYSIS':
            groups[row['requisition_id']].append(row)
    for rid, group in groups.items():
        min_cost = min(Decimal(r['total_cost_eur']) for r in group)
        min_lead = min(Decimal(r['lead_time_days']) for r in group)
        for r in group:
            cost_score = 100 * min_cost / Decimal(r['total_cost_eur'])
            delivery_score = 100 * min_lead / Decimal(r['lead_time_days'])
            total = (WEIGHTS['cost'] * cost_score + WEIGHTS['delivery'] * delivery_score
                     + WEIGHTS['quality'] * Decimal(r['quality_score'])
                     + WEIGHTS['reliability'] * Decimal(r['reliability_score']))
            r['cost_score'] = f'{cost_score:.2f}'
            r['delivery_score'] = f'{delivery_score:.2f}'
            r['weighted_score'] = f'{total:.2f}'
        # Ranking is informational only; procurement manager approval remains mandatory.
        ranked = sorted(group, key=lambda r: (-Decimal(r['weighted_score']), Decimal(r['total_cost_eur']), int(r['lead_time_days']), r['quotation_id']))
        ranked[0]['recommendation_status'] = 'TOP_RANKED_PENDING_HUMAN_APPROVAL'
        for other in ranked[1:]:
            other['recommendation_status'] = 'RANKED_ALTERNATIVE'
    path = ANALYSIS / 'supplier_evaluation_results.csv'
    write(path, rows, list(rows[0]) if rows else ['quotation_id'])
    print('Eligible for analysis:', sum(r['evaluation_status']=='ELIGIBLE_FOR_ANALYSIS' for r in rows))
    print('Manual review required:', sum(r['evaluation_status']=='REVIEW_REQUIRED' for r in rows))
    print('Blocked:', sum(r['evaluation_status']=='BLOCKED' for r in rows))
    print('Top-ranked (not approved):', sum(r['recommendation_status']=='TOP_RANKED_PENDING_HUMAN_APPROVAL' for r in rows))
    print('Important: retrospective analysis uses performance snapshots after requisition dates.')


if __name__ == '__main__':
    main()
