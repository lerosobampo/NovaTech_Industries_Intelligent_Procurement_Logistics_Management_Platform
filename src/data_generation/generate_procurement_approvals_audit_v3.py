#!/usr/bin/env python3
"""NovaTech checkpoint 2.13: generate simulation approval and audit CSVs.

Requires data/synthetic/v3/procurement_decisions.csv.
All outputs are simulated and non-authorizing. Does not modify decisions.
"""
import csv
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'synthetic' / 'v3'
DECISIONS = DATA / 'procurement_decisions.csv'
APPROVALS = DATA / 'procurement_approvals.csv'
AUDIT = DATA / 'procurement_decision_audit.csv'


def read_decisions():
    if not DECISIONS.exists():
        raise FileNotFoundError(f'Missing: {DECISIONS}')
    with DECISIONS.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        required = {'decision_id', 'requisition_id', 'decision_date', 'decision_mode',
                    'decision_status', 'selected_quotation_id', 'approval_status',
                    'evaluation_source', 'decision_reason'}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'Missing columns: {sorted(missing)}')
        rows = list(reader)
    if not rows:
        raise ValueError('No procurement decisions found')
    return rows


def build_records(decisions):
    approvals, audit = [], []
    seen_ids, seen_reqs = set(), set()
    for index, row in enumerate(decisions, 1):
        did, rid = row['decision_id'], row['requisition_id']
        if did in seen_ids or rid in seen_reqs:
            raise ValueError(f'Duplicate decision or requisition: {did} / {rid}')
        seen_ids.add(did)
        seen_reqs.add(rid)
        if (row['decision_mode'] != 'SIMULATION'
                or row['decision_status'] != 'PENDING_REVIEW'
                or row['approval_status'] != 'NOT_AUTHORIZED'
                or row['selected_quotation_id'].strip()):
            raise ValueError(f'{did}: unsafe or unexpected decision state')
        try:
            event_date = date.fromisoformat(row['decision_date'])
        except ValueError as exc:
            raise ValueError(f'{did}: invalid decision date') from exc
        if event_date < date(2026, 10, 16):
            raise ValueError(f'{did}: decision predates quotation issue date')
        approvals.append({
            'approval_id': f'APR{index:03d}',
            'decision_id': did,
            'requisition_id': rid,
            'approval_requested_at': event_date.isoformat(),
            'approval_stage': 'PROCUREMENT_MANAGER_REVIEW',
            'approver_role': 'SIMULATED_PROCUREMENT_MANAGER',
            'approval_status': 'PENDING_REVIEW',
            'approval_decided_at': '',
            'approved_by': '',
            'approval_notes': 'SIMULATION_ONLY;HISTORICAL_EVIDENCE_UNVERIFIED',
            'decision_mode': 'SIMULATION',
            'authorization_effect': 'NONE',
        })
        audit.append({
            'audit_id': f'AUD{index:03d}',
            'decision_id': did,
            'requisition_id': rid,
            'event_date': event_date.isoformat(),
            'event_type': 'DECISION_CREATED',
            'actor': 'SIMULATED_BUYER',
            'previous_status': '',
            'new_status': 'PENDING_REVIEW',
            'evidence_reference': row['evaluation_source'],
            'event_details': row['decision_reason'],
            'decision_mode': 'SIMULATION',
            'evidence_classification': 'SYNTHETIC_UNVERIFIED',
        })
    return approvals, audit


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    decisions = read_decisions()
    approvals, audit = build_records(decisions)
    write_csv(APPROVALS, approvals)
    write_csv(AUDIT, audit)
    print(f'Created {APPROVALS.relative_to(ROOT)}: {len(approvals)} records')
    print(f'Created {AUDIT.relative_to(ROOT)}: {len(audit)} records')
    print('All approvals pending; all events synthetic; no purchase authorization.')


if __name__ == '__main__':
    main()
