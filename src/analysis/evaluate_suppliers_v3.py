#!/usr/bin/env python3
"""NovaTech Checkpoint 2.11: conservative, point-in-time supplier evaluation.

Run from any directory; reads v2 inputs, writes a separate v3 output.
The requisition's latest quotation date is a comparison cutoff proxy, NOT a
verified purchasing decision timestamp. Missing historical approval evidence
forces manual review rather than an automatic ranking.
"""
import csv
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'synthetic' / 'v2'
ANALYSIS = ROOT / 'data' / 'analysis' / 'v2'
OUT = ROOT / 'data' / 'analysis' / 'v3' / 'supplier_evaluation_results.csv'
WEIGHTS = {'cost': Decimal('.40'), 'delivery': Decimal('.25'), 'quality': Decimal('.20'), 'reliability': Decimal('.15')}
MIN_INSPECTED = 100
MIN_DELIVERIES = 10


def read(path, required):
    if not path.is_file():
        raise FileNotFoundError(f'Missing input: {path}')
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{path.name}: missing columns {sorted(missing)}')
        return list(reader)


def unique(rows, keys, label):
    result = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        if key in result:
            raise ValueError(f'{label}: duplicate {key}')
        result[key] = row
    return result


def day(value, label):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError(f'{label}: invalid date {value!r}')


def num(value, label, positive=False):
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError(f'{label}: invalid number {value!r}')
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise ValueError(f'{label}: out of range {value!r}')
    return result


def performance_at(supplier, cutoff, deliveries, inspections):
    """Only historical records dated within 12 months through cutoff."""
    start = cutoff - timedelta(days=365)
    completed = on_time = 0
    inspected = accepted = 0
    for row in deliveries:
        if row['supplier_id'] != supplier:
            continue
        status = row['status'].strip().upper()
        if status not in {'COMPLETED', 'DELIVERED'}:
            continue
        actual = day(row['actual_delivery_date'], 'actual_delivery_date')
        planned = day(row['planned_delivery_date'], 'planned_delivery_date')
        if not start <= actual <= cutoff:
            continue
        expected = actual <= planned
        flag = row['on_time'].strip().lower()
        if flag not in {'true', 'false', '1', '0', 'yes', 'no'}:
            raise ValueError(f"{row['delivery_id']}: invalid on_time flag")
        recorded = flag in {'true', '1', 'yes'}
        if recorded != expected:
            raise ValueError(f"{row['delivery_id']}: on_time disagrees with dates")
        completed += 1
        on_time += int(expected)
    for row in inspections:
        if row['supplier_id'] != supplier:
            continue
        inspection_date = day(row['inspection_date'], 'inspection_date')
        if not start <= inspection_date <= cutoff:
            continue
        total = num(row['inspected_units'], 'inspected_units', positive=True)
        good = num(row['accepted_units'], 'accepted_units')
        rejected = num(row['rejected_units'], 'rejected_units')
        if good + rejected != total:
            raise ValueError(f"{row['inspection_id']}: inspection quantities disagree")
        inspected += int(total)
        accepted += int(good)
    enough = inspected >= MIN_INSPECTED and completed >= MIN_DELIVERIES
    quality = Decimal(100) * accepted / inspected if inspected else None
    reliability = Decimal(100) * on_time / completed if completed else None
    return {'inspected_units': inspected, 'completed_deliveries': completed,
            'quality_score': quality, 'reliability_score': reliability,
            'evidence_sufficient': enough}


def compliance_at(record, cutoff):
    """No inferred approval start date: absence of provenance requires review."""
    if record is None:
        return 'BLOCKED', 'CATEGORY_COMPLIANCE_MISSING'
    expiry = day(record['valid_until'], 'compliance valid_until')
    if expiry < cutoff:
        return 'BLOCKED', 'CATEGORY_COMPLIANCE_EXPIRED'
    if record['approval_status'].strip().upper() != 'APPROVED':
        return 'BLOCKED', 'CATEGORY_COMPLIANCE_NOT_APPROVED'
    # Optional provenance fields supported for future enhanced source data.
    approved_on = record.get('approved_on', '').strip()
    status_as_of = record.get('status_as_of', '').strip()
    if not approved_on or not status_as_of:
        return 'REVIEW_REQUIRED', 'HISTORICAL_COMPLIANCE_PROVENANCE_MISSING'
    if day(approved_on, 'approved_on') > cutoff or day(status_as_of, 'status_as_of') > cutoff:
        return 'REVIEW_REQUIRED', 'COMPLIANCE_NOT_VERIFIED_AT_CUTOFF'
    return 'VALID', ''


def evaluate():
    quotes = read(ANALYSIS / 'quotation_eligibility_results.csv',
                  ['quotation_id','requisition_id','supplier_id','product_id','total_cost_eur','preliminary_status','reasons'])
    requisitions = unique(read(DATA / 'purchase_requisitions.csv', ['requisition_id','request_date']), ['requisition_id'], 'requisitions')
    quotation_headers = unique(read(DATA / 'quotations.csv', ['quotation_id','requisition_id','quotation_date','valid_until']), ['quotation_id'], 'quotations')
    products = unique(read(DATA / 'products.csv', ['product_id','category']), ['product_id'], 'products')
    items = unique(read(DATA / 'quotation_items.csv', ['quotation_id','lead_time_days']), ['quotation_id'], 'quotation items')
    deliveries = read(DATA / 'supplier_deliveries.csv', ['delivery_id','supplier_id','planned_delivery_date','actual_delivery_date','on_time','status'])
    inspections = read(DATA / 'supplier_quality_inspections.csv', ['inspection_id','supplier_id','inspection_date','inspected_units','accepted_units','rejected_units'])
    compliance = unique(read(DATA / 'supplier_compliance.csv', ['supplier_id','category','approval_status','valid_until']), ['supplier_id','category'], 'compliance')
    unique(deliveries, ['delivery_id'], 'deliveries')
    unique(inspections, ['inspection_id'], 'inspections')
    unique(quotes, ['quotation_id'], 'analysis quotations')
    # Compare valid-chronology quotations at a shared cutoff per requisition.
    # Malformed quotations are blocked individually, not allowed to shift the cutoff.
    cutoffs = {}
    chronology_errors = set()
    for q in quotes:
        qid, rid = q['quotation_id'], q['requisition_id']
        if (rid,) not in requisitions or (qid,) not in quotation_headers or (qid,) not in items or (q['product_id'],) not in products:
            raise ValueError(f'{qid}: missing required foreign key')
        header = quotation_headers[(qid,)]
        if header['requisition_id'] != rid:
            raise ValueError(f'{qid}: requisition mismatch')
        quoted = day(header['quotation_date'], f'{qid} quotation_date')
        requested = day(requisitions[(rid,)]['request_date'], f'{rid} request_date')
        if quoted < requested:
            chronology_errors.add(qid)
            continue
        cutoffs[rid] = max(cutoffs.get(rid, quoted), quoted)
    results = []
    for q in quotes:
        qid, rid, sid = q['quotation_id'], q['requisition_id'], q['supplier_id']
        cutoff = cutoffs.get(rid, day(requisitions[(rid,)]['request_date'], f'{rid} request_date'))
        header = quotation_headers[(qid,)]
        category = products[(q['product_id'],)]['category']
        metrics = performance_at(sid, cutoff, deliveries, inspections)
        compliance_status, compliance_reason = compliance_at(compliance.get((sid, category)), cutoff)
        preliminary = q['preliminary_status']
        if preliminary not in {'BLOCKED', 'PENDING_REVIEW'}:
            raise ValueError(f'{qid}: unexpected preliminary status {preliminary}')
        reasons = [x for x in q['reasons'].split(';') if x] if preliminary == 'BLOCKED' else []
        if qid in chronology_errors:
            reasons.append('QUOTATION_PREDATES_REQUISITION')
        if day(header['valid_until'], f'{qid} valid_until') < cutoff:
            reasons.append('QUOTATION_EXPIRED_AT_CUTOFF')
        if compliance_reason:
            reasons.append(compliance_reason)
        if not metrics['evidence_sufficient']:
            reasons.append('INSUFFICIENT_PERFORMANCE_HISTORY')
        # Prior eligibility analysis lacks historical provenance for supplier status,
        # quantities, and quote validity. Do not promote its snapshot to an as-of approval.
        reasons.append('PRELIMINARY_ELIGIBILITY_PROVENANCE_MISSING')
        cost = num(q['total_cost_eur'], f'{qid} cost', positive=True)
        lead = num(items[(qid,)]['lead_time_days'], f'{qid} lead time', positive=True)
        blocked = (preliminary == 'BLOCKED' or compliance_status == 'BLOCKED'
                   or 'QUOTATION_EXPIRED_AT_CUTOFF' in reasons
                   or 'QUOTATION_PREDATES_REQUISITION' in reasons)
        status = 'BLOCKED' if blocked else 'REVIEW_REQUIRED' if reasons else 'ELIGIBLE_FOR_ANALYSIS'
        results.append({'quotation_id': qid, 'requisition_id': rid, 'supplier_id': sid,
                        'product_id': q['product_id'], 'category': category, 'evaluation_as_of': cutoff.isoformat(),
                        'cutoff_basis': 'LATEST_QUOTATION_DATE_PROXY',
                        'total_cost_eur': f'{cost:.2f}', 'lead_time_days': str(int(lead)),
                        'inspected_units': str(metrics['inspected_units']),
                        'completed_deliveries': str(metrics['completed_deliveries']),
                        'quality_score': f"{metrics['quality_score']:.2f}" if metrics['quality_score'] is not None else '',
                        'reliability_score': f"{metrics['reliability_score']:.2f}" if metrics['reliability_score'] is not None else '',
                        'evaluation_status': status, 'reasons': ';'.join(dict.fromkeys(reasons)),
                        'cost_score': '', 'delivery_score': '', 'weighted_score': '',
                        'recommendation_status': 'NO_AUTOMATIC_APPROVAL'})
    groups = defaultdict(list)
    for r in results:
        if r['evaluation_status'] == 'ELIGIBLE_FOR_ANALYSIS':
            groups[r['requisition_id']].append(r)
    for group in groups.values():
        min_cost = min(Decimal(r['total_cost_eur']) for r in group)
        min_lead = min(Decimal(r['lead_time_days']) for r in group)
        for r in group:
            c = Decimal(100) * min_cost / Decimal(r['total_cost_eur'])
            d = Decimal(100) * min_lead / Decimal(r['lead_time_days'])
            total = WEIGHTS['cost']*c + WEIGHTS['delivery']*d + WEIGHTS['quality']*Decimal(r['quality_score']) + WEIGHTS['reliability']*Decimal(r['reliability_score'])
            r['cost_score'], r['delivery_score'], r['weighted_score'] = f'{c:.2f}', f'{d:.2f}', f'{total:.2f}'
        ranked = sorted(group, key=lambda r: (-Decimal(r['weighted_score']), Decimal(r['total_cost_eur']), int(r['lead_time_days']), r['quotation_id']))
        ranked[0]['recommendation_status'] = 'TOP_RANKED_PENDING_HUMAN_APPROVAL'
        for r in ranked[1:]:
            r['recommendation_status'] = 'RANKED_ALTERNATIVE'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]) if results else ['quotation_id'])
        writer.writeheader()
        writer.writerows(results)
    print(f'Created {OUT.relative_to(ROOT)}: {len(results)} records')
    for status in ('ELIGIBLE_FOR_ANALYSIS', 'REVIEW_REQUIRED', 'BLOCKED'):
        print(f'{status}: {sum(r["evaluation_status"] == status for r in results)}')
    print('Point-in-time protection: no approval or ranking without historical provenance.')
    return results


if __name__ == '__main__':
    evaluate()
