# NovaTech Industries
## Checkpoint 2.4 - Supplier Evaluation Data Dictionary

**Document ID:** NTI-DATA-002  
**Version:** 1.0 (proposed design)  
**Status:** Draft - pending business approval  
**Related requirements:** FR-005, BR-001 to BR-006, DV-001 to DV-010  
**Owner:** Business Transformation & Analytics Team  
**Date:** 21 October 2026

> **Case-study notice:** NovaTech Industries, its suppliers, transactions, and operational figures are fictional. This document specifies a synthetic training environment, not a production system.

## 1. Purpose and scope

This data dictionary specifies the minimum relational data model required to evaluate supplier quotations, enforce mandatory eligibility rules, calculate weighted scores, and preserve an auditable recommendation. It is the design baseline for synthetic CSV generation and later PostgreSQL implementation. The wider procurement, inventory, and logistics schema will be designed in subsequent checkpoints.

**In scope:** suppliers, products, supplier capabilities, requisitions, quotations, quotation lines, historical supplier performance, exchange rates, scoring policies, evaluation runs, and per-quotation results.

**Out of scope for this checkpoint:** purchase-order execution, invoice matching, inventory movement posting, shipment event history, user authentication, and AI agent orchestration.

## 2. Core data concepts

- **Entity/table:** a collection of records about one business concept, such as suppliers.
- **Row/record:** one instance, such as supplier `SUP-0001`.
- **Column/field:** one property, such as `supplier_status`.
- **Primary key (PK):** a unique identifier for a row.
- **Foreign key (FK):** a reference to another table's primary key.
- **Cardinality:** how many records can relate to each other (one-to-many or many-to-many).
- **Nullable:** whether a field may be absent; a missing value is not the same as zero.
- **Snapshot:** a stored copy of values used in a decision, retained so historical evaluations remain reproducible.

## 3. Data model and relationships

| Parent entity | Child entity | Relationship | Purpose |
|---|---|---|---|
| suppliers | supplier_products | 1-to-many | Approved products and supply capabilities |
| products | supplier_products | 1-to-many | Product can be offered by multiple suppliers |
| purchase_requisitions | requisition_items | 1-to-many | A requisition may request several products |
| suppliers | quotations | 1-to-many | Supplier can issue many quotations |
| quotations | quotation_items | 1-to-many | Each quotation has one or more priced lines |
| products | quotation_items | 1-to-many | Each quotation line references a product |
| suppliers | supplier_performance | 1-to-many | Period-based performance history |
| scoring_policies | evaluation_runs | 1-to-many | Each run uses one policy version |
| requisition_items | evaluation_runs | 1-to-many | One requisition line can be evaluated repeatedly |
| evaluation_runs | evaluation_results | 1-to-many | One result per assessed quotation line |
| quotation_items | evaluation_results | 1-to-many | Quotation line can appear in later evaluation runs |

**Design rule:** one evaluation run compares quotations for **one requisition item**, one product, one requested quantity, and one required delivery date. A multi-line requisition therefore produces separate evaluation runs for each line. A later optimization phase may consider bundled purchasing across lines.

## 4. Field-level data dictionary

### 4.1 suppliers

**Grain:** one row per supplier. **Primary key:** `supplier_id`.

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| supplier_id | VARCHAR(20) | Yes | PK; format `SUP-0001` |
| supplier_name | VARCHAR(150) | Yes | Nonblank display name |
| country_code | CHAR(2) | Yes | ISO 3166-1 alpha-2 code |
| supplier_status | VARCHAR(20) | Yes | `active`, `inactive`, `suspended` |
| created_at | TIMESTAMP | Yes | Record creation timestamp in UTC |

### 4.2 products

**Grain:** one row per catalog product. **Primary key:** `product_id`.

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| product_id | VARCHAR(20) | Yes | PK; format `PRD-0001` |
| sku | VARCHAR(40) | Yes | Unique stock-keeping unit |
| product_name | VARCHAR(150) | Yes | Nonblank description |
| category_code | VARCHAR(30) | Yes | Controlled product category |
| unit_of_measure | VARCHAR(12) | Yes | Example: `unit`, `box`, `kg` |
| product_status | VARCHAR(20) | Yes | `active` or `discontinued` |

### 4.3 supplier_products

**Grain:** one supplier-product capability record. **Primary key:** (`supplier_id`, `product_id`).

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| supplier_id | VARCHAR(20) | Yes | PK part; FK -> suppliers |
| product_id | VARCHAR(20) | Yes | PK part; FK -> products |
| category_approved | BOOLEAN | Yes | Supplier approved for this product/category |
| minimum_order_qty | INTEGER | Yes | Greater than zero |
| maximum_supply_qty | INTEGER | Yes | Greater than or equal to minimum_order_qty |
| compliance_status | VARCHAR(20) | Yes | `approved`, `pending`, `rejected` |
| capability_updated_at | TIMESTAMP | Yes | Last capability confirmation, UTC |

### 4.4 purchase_requisitions

**Grain:** one purchasing request header. **Primary key:** `requisition_id`.

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| requisition_id | VARCHAR(20) | Yes | PK; format `REQ-0001` |
| requested_by_department | VARCHAR(60) | Yes | Example: Operations |
| requested_at | TIMESTAMP | Yes | Creation timestamp, UTC |
| requisition_status | VARCHAR(20) | Yes | `draft`, `submitted`, `approved`, `cancelled` |

### 4.5 requisition_items

**Grain:** one requested product line. **Primary key:** `requisition_item_id`.

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| requisition_item_id | VARCHAR(25) | Yes | PK; format `REQITEM-0001` |
| requisition_id | VARCHAR(20) | Yes | FK -> purchase_requisitions |
| product_id | VARCHAR(20) | Yes | FK -> products |
| requested_quantity | INTEGER | Yes | Greater than zero |
| required_delivery_date | DATE | Yes | Not before evaluation date for new runs |
| receiving_location_code | VARCHAR(30) | Yes | Warehouse/site destination identifier |

### 4.6 quotations

**Grain:** one supplier quotation header. **Primary key:** `quotation_id`.

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| quotation_id | VARCHAR(20) | Yes | PK; format `QUO-0001` |
| supplier_id | VARCHAR(20) | Yes | FK -> suppliers |
| quotation_date | DATE | Yes | Date supplier issued quotation |
| valid_until | DATE | Yes | On or after quotation_date |
| currency_code | CHAR(3) | Yes | ISO 4217, e.g. EUR or USD |
| quotation_status | VARCHAR(20) | Yes | `received`, `withdrawn`, `accepted`, `expired` |

### 4.7 quotation_items

**Grain:** one product line on a quotation. **Primary key:** `quotation_item_id`.

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| quotation_item_id | VARCHAR(25) | Yes | PK; format `QUOITEM-0001` |
| quotation_id | VARCHAR(20) | Yes | FK -> quotations |
| product_id | VARCHAR(20) | Yes | FK -> products |
| quoted_quantity | INTEGER | Yes | Greater than zero |
| unit_price | DECIMAL(14,4) | Yes | Strictly positive, quotation currency |
| freight_cost | DECIMAL(14,2) | Yes | Nonnegative, quotation currency |
| duty_cost | DECIMAL(14,2) | Yes | Nonnegative, quotation currency |
| other_cost | DECIMAL(14,2) | Yes | Nonnegative, quotation currency |
| lead_time_days | INTEGER | Yes | At least 1 in initial model |
| promised_delivery_date | DATE | Yes | Must be consistent with quoted delivery basis |

**Cost policy:** `line_total = requested_quantity * unit_price + freight_cost + duty_cost + other_cost` for a quotation that can fulfill the requested quantity. All costs are per quotation line and must be consistently allocated; taxes recoverable by the buyer are excluded unless business policy states otherwise.

### 4.8 supplier_performance

**Grain:** one supplier, product category, and rolling evaluation period. **Primary key:** `performance_id`.

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| performance_id | VARCHAR(25) | Yes | PK |
| supplier_id | VARCHAR(20) | Yes | FK -> suppliers |
| category_code | VARCHAR(30) | Yes | Product category covered |
| period_start | DATE | Yes | Beginning of observation period |
| period_end | DATE | Yes | End of observation period |
| inspected_units | INTEGER | Yes | Nonnegative |
| accepted_units | INTEGER | Yes | Between 0 and inspected_units |
| completed_deliveries | INTEGER | Yes | Nonnegative |
| on_time_deliveries | INTEGER | Yes | Between 0 and completed_deliveries |

**Derived metrics:** `quality_score = 100 * accepted_units / inspected_units`; `reliability_score = 100 * on_time_deliveries / completed_deliveries`. A zero denominator produces an **unavailable** metric, not zero. No overlapping performance windows for the same supplier/category and evaluation snapshot.

### 4.9 exchange_rates

**Grain:** one source currency, target currency, and effective date. **Primary key:** (`rate_date`, `from_currency`, `to_currency`).

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| rate_date | DATE | Yes | Rate's effective business date |
| from_currency | CHAR(3) | Yes | ISO 4217 source currency |
| to_currency | CHAR(3) | Yes | ISO 4217 target currency; EUR initially |
| conversion_rate | DECIMAL(18,8) | Yes | Strictly positive; multiply source amount by rate |
| rate_source | VARCHAR(80) | Yes | Synthetic reference source identifier |

### 4.10 scoring_policies

**Grain:** one immutable scoring configuration version. **Primary key:** `policy_id`.

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| policy_id | VARCHAR(25) | Yes | PK; e.g. `POLICY-001-V1` |
| cost_weight | DECIMAL(5,4) | Yes | Default 0.4000 |
| delivery_weight | DECIMAL(5,4) | Yes | Default 0.2500 |
| quality_weight | DECIMAL(5,4) | Yes | Default 0.2000 |
| reliability_weight | DECIMAL(5,4) | Yes | Default 0.1500 |
| normalization_version | VARCHAR(30) | Yes | `relative-ratio-v1` |
| effective_from | DATE | Yes | Policy start date |
| policy_status | VARCHAR(20) | Yes | `draft`, `active`, `retired` |

**Validation:** each weight is between 0 and 1, and all four weights sum to exactly 1.0000. Policies referenced by evaluations cannot be edited in place; create a new version.

### 4.11 evaluation_runs

**Grain:** one supplier-comparison event for a requisition item. **Primary key:** `evaluation_run_id`.

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| evaluation_run_id | VARCHAR(25) | Yes | PK; e.g. `EVAL-0001` |
| requisition_item_id | VARCHAR(25) | Yes | FK -> requisition_items |
| policy_id | VARCHAR(25) | Yes | FK -> scoring_policies |
| evaluated_at | TIMESTAMP | Yes | UTC evaluation timestamp |
| base_currency | CHAR(3) | Yes | `EUR` for initial release |
| run_status | VARCHAR(20) | Yes | `completed`, `review_required`, `no_eligible_offers` |
| evaluated_by | VARCHAR(60) | Yes | `system` or simulated user identifier |

### 4.12 evaluation_results

**Grain:** one assessed quotation line within an evaluation run. **Primary key:** `evaluation_result_id`. Unique (`evaluation_run_id`, `quotation_item_id`).

| Field | Type | Required | Rules / meaning |
|---|---|---|---|
| evaluation_result_id | VARCHAR(25) | Yes | PK |
| evaluation_run_id | VARCHAR(25) | Yes | FK -> evaluation_runs |
| quotation_item_id | VARCHAR(25) | Yes | FK -> quotation_items |
| is_eligible | BOOLEAN | Yes | Whether all mandatory rules passed |
| exclusion_reasons | JSON | Yes | Array of reason codes; empty if eligible |
| total_cost_eur | DECIMAL(14,2) | No | Comparable converted total; nullable if incomplete |
| delivery_days_snapshot | INTEGER | No | Lead time used for scoring |
| quality_score | DECIMAL(6,2) | No | 0-100, nullable if insufficient history |
| reliability_score | DECIMAL(6,2) | No | 0-100, nullable if insufficient history |
| cost_score | DECIMAL(6,2) | No | 0-100; computed among eligible offers |
| delivery_score | DECIMAL(6,2) | No | 0-100; computed among eligible offers |
| final_score | DECIMAL(6,2) | No | 0-100; null for ineligible/incomplete |
| recommendation_rank | INTEGER | No | 1 is best; null when not ranked |
| requires_manual_review | BOOLEAN | Yes | True if history or data confidence inadequate |

**Auditability:** preserve the source quotation, performance period, FX effective date, scoring policy version, and eligible comparison set. The production implementation may add an immutable JSON evaluation snapshot to guarantee reproducibility when source records change.

## 5. Worked example and evaluation lineage

**Requisition:** `REQ-0001`, line `REQITEM-0001`, product `PRD-0001`, quantity 100, required delivery date 2026-11-20.

| Supplier | Comparable cost (EUR) | Lead time | Quality | Reliability |
|---|---:|---:|---:|---:|
| EuroParts GmbH | 12,000 | 5 days | 98 | 96 |
| Shenzhen Components | 10,000 | 12 days | 92 | 84 |
| Nordic Industrial AB | 11,500 | 7 days | 99 | 95 |

Assuming all three quotations are eligible, the minimum cost is EUR 10,000 and minimum lead time is 5 days. Using policy weights 40/25/20/15:

| Supplier | Cost score | Delivery score | Quality | Reliability | Weighted total |
|---|---:|---:|---:|---:|---:|
| EuroParts GmbH | 83.33 | 100.00 | 98 | 96 | 92.33 |
| Shenzhen Components | 100.00 | 41.67 | 92 | 84 | 81.42 |
| Nordic Industrial AB | 86.96 | 71.43 | 99 | 95 | 86.69 |

**Recommendation:** EuroParts GmbH. Values are rounded for display; scoring calculations must retain unrounded intermediate precision. The ranking is valid only for this evaluation set and policy version.

## 6. Validation and integrity controls

| Control | Enforcement |
|---|---|
| Unique IDs and SKU | PK / unique constraints |
| Valid references | Foreign-key constraints |
| Valid statuses and currencies | Controlled vocabularies / checks |
| Positive quantities and prices | Database CHECK constraints and API validation |
| Valid quotation dates | `valid_until >= quotation_date` |
| Valid performance counts | Accepted <= inspected; on-time <= completed |
| Nonnegative freight/duty/other costs | Database CHECK constraints |
| Weight sum = 100% | Policy validation before activation |
| Eligible quotation consistency | Product, quantity, date, compliance, supplier status |
| Missing historical metrics | Manual review; do not fabricate scores |
| Currency conversion | Record rate date, rate source, and applied rate |
| Reproducibility | Immutable policy version and evaluation snapshot |

## 7. Synthetic data generation plan

The first practical exercise will use small CSV files. We will expand to relational tables only after validating the basic pipeline.

| Stage | Dataset size | Learning objective |
|---|---|---|
| Starter | 3 suppliers, 10 products, 3 quotations | CSV reading and simple scoring |
| Intermediate | 20 suppliers, 50 products, 100 quotations | Foreign keys, joins, validation |
| Advanced | 50 suppliers, 200 products, 2,500 quotation headers | Multi-table data generation, history, performance |

**Generation rules:** deterministic random seed; stable unique IDs; referential integrity; plausible country/lead-time relationships; nonnegative prices; realistic quality and delivery histories; explicit missing-data scenarios; separate deliberately-invalid test fixtures; and no real personal or commercial information.

**Recommended starter files:** `suppliers.csv`, `products.csv`, `supplier_products.csv`, `requisition_items.csv`, `quotations.csv`, `quotation_items.csv`, and `supplier_performance.csv`. Additional policy and FX tables can be introduced when the exercise reaches multi-currency and historical scoring.

## 8. Open decisions for business approval

1. **Historical sufficiency:** minimum inspected units and completed deliveries before automatic scoring (proposed initial thresholds: 100 inspected units and 10 completed deliveries).
2. **Delivery basis:** confirm whether supplier lead time is measured from purchase order release or quotation acceptance; use calendar days consistently.
3. **Currency policy:** select FX rate effective on evaluation date, or the latest available rate not after that date.
4. **Tie-breaking:** proposed sequence: higher weighted score, lower total cost, shorter lead time, then stable quotation ID.
5. **Performance granularity:** category-specific historical scores are preferred; define fallback when category-level history is sparse.
6. **Approval authority:** Procurement Officer reviews all recommendations; Procurement Manager reviews missing-history cases and exceptions.

These decisions are **proposals**, not yet approved rules. They must be finalized before production-grade evaluation logic is implemented.

## 9. Acceptance criteria for the data model

- All evaluation results reference valid quotation lines and evaluation runs.
- A quotation cannot be ranked unless mandatory eligibility rules are satisfied and all required scores are available.
- Scores can be reproduced from saved inputs, policy version, and comparison set.
- Supplier quality and reliability rates derive from recorded numerators and denominators.
- Every foreign key resolves to an existing parent record.
- Synthetic datasets contain no real customer, supplier, or employee information.
- CSV exports can be imported into PostgreSQL without changing field meaning.

## 10. Repository location and next checkpoint

Save the two versions of this document as:

```text
docs/data/supplier-evaluation-data-dictionary.md
docs/data/supplier-evaluation-data-dictionary.pdf
```

**Next checkpoint 2.5:** approve the outstanding data policies, define the starter CSV schema, and generate a small coherent synthetic dataset with Python. No database or Docker installation is required yet.
