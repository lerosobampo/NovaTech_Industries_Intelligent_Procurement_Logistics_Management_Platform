# Business Requirements Document (BRD)

## NovaTech Industries — Intelligent Procurement & Logistics Management Platform

| Document control | Value |
|---|---|
| Document ID | NTI-BRD-001 |
| Version | 1.0 |
| Status | Working baseline — subject to stakeholder review |
| Date | 21 October 2026 |
| Business sponsor | Director of Operations |
| Business owner | Procurement & Operations |
| Related documents | `business-case.md`; `supplier-evaluation-requirements.md`; `supplier-score-normalization-validation.md`; `supplier-evaluation-data-dictionary.md` |

> **Case-study notice:** NovaTech Industries is a fictional company. All business figures, roles, and operational scenarios are simulated for training and portfolio development.

---

## 1. Executive Summary

NovaTech Industries requires a centralized procurement and logistics management platform to reduce manual work, standardize purchasing decisions, improve inventory visibility, and provide reliable operational reporting. The solution will integrate supplier records, product catalogs, purchase requisitions, supplier quotations, purchase orders, warehouse inventory, shipment tracking, business intelligence, and controlled automation. AI assistance will be introduced after deterministic business rules and core data processes are validated.

This BRD defines **what** the business needs, **who** uses the system, and **how success will be accepted**. Technical implementation choices belong in the system architecture document.

## 2. Business Context and Objectives

NovaTech operates a simulated network of 50 suppliers, 200 SKUs, and three warehouses. Procurement, logistics, and inventory information is currently fragmented across spreadsheets and manual communications.

### 2.1 Business objectives

| ID | Objective | Proposed measurement |
|---|---|---|
| BO-001 | Reduce procurement cycle time | Average requisition-to-order processing time |
| BO-002 | Improve supplier delivery performance | On-time delivery rate |
| BO-003 | Reduce administrative effort | Manual minutes per purchasing transaction |
| BO-004 | Improve inventory availability | Stockout incidents per quarter |
| BO-005 | Improve quotation evaluation efficiency | Minutes per quotation evaluation |
| BO-006 | Increase purchasing data accuracy | Percentage of purchase orders passing validation |

### 2.2 Illustrative baseline and targets

| KPI | Simulated baseline | Proposed target |
|---|---:|---:|
| Requisition processing time | 3.5 days | 1.5 days |
| On-time supplier deliveries | 87% | 95% |
| Manual procurement processing time | 100% baseline | 40% reduction |
| Stockout incidents | 24 per quarter | 12 per quarter |
| Quotation evaluation time | 90 minutes | 20 minutes |
| Purchase order data accuracy | 93% | 99% |

These values are assumptions for the case study, **not observed company results**. Targets will be assessed against synthetic scenarios during testing.

## 3. Scope

### 3.1 In scope

- Supplier master data, approval status, product offerings, and supplier performance.
- Product catalog and purchasing information.
- Purchase requisitions, quotation capture and comparison, purchase order creation, and approval controls.
- Inventory balances, stock movements, and reorder alerts.
- Shipment tracking, milestones, exceptions, and delivery confirmation.
- Management dashboards and KPI calculations.
- Workflow automation and AI-assisted recommendations with human oversight.
- Synthetic data generation, validation, and local demonstration.

### 3.2 Out of scope for initial release

- Real supplier or carrier integrations and live commercial transactions.
- Payments, invoicing, tax filing, and full accounting ledger.
- Enterprise ERP replacement.
- Autonomous purchase order approval or dispatch by AI.
- Production-grade multi-tenant hosting and external customer access.

These may be evaluated in later phases, but are not prerequisites for the first working release.

## 4. Stakeholders and User Roles

| Role | Primary responsibilities | Required access |
|---|---|---|
| Procurement Officer | Maintain sourcing activity, requisitions, quotations, and orders | Suppliers, products, procurement |
| Procurement Manager | Review exceptions, approve orders, oversee supplier performance | Procurement, approvals, reports |
| Warehouse Operator | Receive goods and record stock movements | Warehouse, inventory |
| Logistics Coordinator | Update shipment status and investigate delays | Shipments, delivery events |
| Operations Manager | Review operational performance and trends | Dashboards and reporting |
| System Administrator | Maintain user access and business configurations | Administrative settings |

Permissions will follow the principle of least privilege. A user should access only the capabilities needed for their role.

## 5. End-to-End Business Process

1. **Identify demand:** An inventory threshold or authorized user creates a purchase requirement.
2. **Create requisition:** Capture product, quantity, requested delivery date, requester, and justification.
3. **Request and register quotations:** Obtain offers from relevant approved suppliers.
4. **Validate eligibility:** Check supplier status, product approval, quotation validity, quantities, delivery constraints, and compliance.
5. **Evaluate offers:** Apply weighted criteria and present a ranked, explainable recommendation.
6. **Review and approve:** An authorized person confirms the sourcing decision and purchase order.
7. **Manage shipment:** Track dispatch, transit, arrival, and exceptions.
8. **Receive goods:** Record accepted quantities and inventory movements.
9. **Monitor performance:** Update supplier metrics and management dashboards.

## 6. Functional Requirements

Priority uses MoSCoW: **Must** = essential core capability; **Should** = important later capability; **Could** = optional enhancement.

| ID | Requirement | Priority | Acceptance summary |
|---|---|---|---|
| FR-001 | Create, view, and update supplier records | Must | Supplier IDs unique; required fields validated; changes traceable |
| FR-002 | Maintain product catalog and supplier-product offers | Must | Product identifiers unique; supplier-product relationships valid |
| FR-003 | Create and manage purchase requisitions | Must | Required fields validated; status changes controlled |
| FR-004 | Register and compare supplier quotations | Must | Offers linked to requisitions and products; expiry checked |
| FR-005 | Recommend suppliers using weighted scoring | Must | Eligibility applied first; scores explainable and reproducible |
| FR-006 | Generate purchase orders from approved requests | Must | Order linked to supplier and source; unauthorized creation blocked |
| FR-007 | Maintain inventory balances and movements | Must | Receipts update stock through auditable movements |
| FR-008 | Track shipments and delivery events | Must | Milestones recorded; late shipments identifiable |
| FR-009 | Calculate procurement and logistics KPIs | Must | Metrics based on defined formulas and traceable records |
| FR-010 | Generate reorder and exception alerts | Should | Alerts triggered by configured thresholds |
| FR-011 | Support configurable approval workflows | Should | Approval status, actor, and timestamp retained |
| FR-012 | Provide AI procurement assistance | Should | Outputs reference source data; no autonomous approval |
| FR-013 | Extract draft quotation details from documents | Could | Human validation before records are committed |
| FR-014 | Support demand forecasting | Could | Forecasts evaluated against historical synthetic data |

### 6.1 Detailed requirement: FR-005 — Supplier Recommendation

**Business owner:** Procurement Manager. **Trigger:** A requisition has at least one supplier quotation ready for evaluation.

**Required inputs:** Product, quantity, required delivery date, supplier status and category approval, quotation prices and currency, quotation validity, lead time, supplier quality history, and delivery reliability history.

**Stage A — Mandatory eligibility:**

| Rule ID | Condition |
|---|---|
| BR-001 | Supplier is active |
| BR-002 | Supplier is approved for the requested product category |
| BR-003 | Quotation is valid on evaluation date |
| BR-004 | Quantity and minimum-order constraints are satisfied |
| BR-005 | Promised delivery meets the required delivery date |
| BR-006 | Applicable quality and compliance requirements are satisfied |

**Stage B — Weighted scoring of eligible quotations:**

| Criterion | Weight | Scoring direction |
|---|---:|---|
| Comparable total purchasing cost | 40% | Lower is better |
| Delivery lead time | 25% | Shorter is better |
| Quality acceptance rate | 20% | Higher is better |
| On-time delivery reliability | 15% | Higher is better |

The weighted score is `S = 0.40*C + 0.25*D + 0.20*Q + 0.15*R`, where each component is normalized to 0–100. Proposed initial normalization is `C = 100 * minimum_eligible_cost / quotation_cost`, `D = 100 * minimum_eligible_lead_time / quotation_lead_time`, `Q = 100 * accepted_units / inspected_units`, and `R = 100 * on_time_deliveries / completed_deliveries`. Positive denominators and consistent units are required. Zero-day delivery, insufficient performance history, and incomparable cost components require explicit handling before implementation.

**FR-005 acceptance criteria:**

1. Ineligible offers are excluded and the reason is recorded.
2. All monetary quotations are converted to a comparable evaluation currency using a recorded exchange rate.
3. All four criterion scores fall between 0 and 100.
4. Configured weights sum to 100% before a production evaluation is run.
5. Eligible offers are ranked by descending final score.
6. The system displays underlying criterion scores and reasons for its recommendation.
7. If no eligible quotation exists, the system reports that outcome without inventing a recommendation.
8. Evaluation inputs, quotation set, weights, formulas/version, and timestamp are retained for audit.
9. A human reviewer must approve the purchasing decision before order issuance.

## 7. Business Data Requirements

The system will require logically separated datasets. The field-level specification is maintained in the supplier evaluation data dictionary and will be extended for inventory and logistics.

| Data domain | Key entities | Main purpose |
|---|---|---|
| Supplier | Suppliers, supplier-product offers, supplier performance | Identify suppliers and sourcing conditions |
| Product | Products, categories | Describe purchasable items |
| Procurement | Requisitions, requisition items, quotations, quotation items | Capture demand and commercial offers |
| Purchasing | Purchase orders, order items | Record approved commitments |
| Inventory | Warehouses, inventory balances, inventory movements | Monitor available stock and goods receipts |
| Logistics | Shipments, shipment events | Track physical delivery |
| Decision support | Evaluation criteria, evaluation results | Reproduce and explain recommendations |

### 7.1 Core data principles

- Use unique stable identifiers for each business entity.
- Enforce referential integrity across related datasets.
- Keep monetary amount and currency together; retain exchange-rate source and effective date.
- Record transaction timestamps and statuses consistently.
- Distinguish missing information from measured zero values.
- Preserve source records and decision history rather than overwriting audit evidence.
- Generate synthetic data with realistic business relationships and controlled exceptions.

## 8. Non-Functional Requirements

| ID | Requirement | Proposed verification |
|---|---|---|
| NFR-001 | Data integrity | Invalid foreign keys and duplicate unique IDs are rejected |
| NFR-002 | Traceability | Key transactions and recommendations retain audit details |
| NFR-003 | Security | Role-based permissions for sensitive actions |
| NFR-004 | Reliability | Core workflows handle invalid or incomplete inputs without silent failure |
| NFR-005 | Maintainability | Modular components, tests, and documented interfaces |
| NFR-006 | Usability | Users can understand statuses, errors, and recommendation rationale |
| NFR-007 | Local operability | Initial demonstrator runs on the project's local development environment |
| NFR-008 | Reproducibility | Synthetic data can be regenerated from documented seeds and parameters |

Numeric performance thresholds will be agreed during technical design and testing, rather than invented in this BRD.

## 9. Business Rules and Controls

- Purchase orders require the appropriate human approval.
- Inventory balances change only through validated stock transactions.
- Shipment receipt quantities cannot silently exceed documented quantities.
- Expired or unapproved quotations cannot be recommended.
- Supplier recommendations are decision support, not autonomous purchasing authority.
- Data quality issues must be visible and must not be concealed by default scores.
- Exceptions and overrides require a reason and an authorized actor.

## 10. Reporting and KPIs

The initial reporting scope includes procurement spend, quotation processing time, requisition-to-order cycle time, supplier on-time delivery, quality acceptance rate, stockout frequency, open purchase orders, and delayed shipments. Each KPI will require an explicit numerator, denominator, reporting period, and treatment of incomplete records in a separate KPI specification.

## 11. Assumptions, Dependencies, and Open Decisions

### 11.1 Assumptions

- The organization and all transactions are fictional.
- The project begins with a small dataset and scales to a larger connected synthetic environment.
- Initial development and demonstration occur locally.
- AI capabilities are introduced after the deterministic workflow is reliable.

### 11.2 Open decisions

| ID | Decision needed | Current position |
|---|---|---|
| OD-001 | Minimum history required for quality and reliability | To be agreed |
| OD-002 | Missing-history handling and manual-review thresholds | Manual review proposed |
| OD-003 | Same-day / zero-day delivery normalization | To be defined |
| OD-004 | Total landed-cost components and exchange-rate policy | To be defined |
| OD-005 | Approval thresholds by order value and risk | To be defined |
| OD-006 | Supplier scoring tie-break policy | To be defined |
| OD-007 | Detailed inventory and logistics field dictionaries | Future checkpoint |

## 12. Delivery Phases and Traceability

| Phase | Primary scope | Requirements |
|---|---|---|
| 1 | Supplier comparison prototype | FR-001, FR-002, FR-004, FR-005 |
| 2 | Procurement data and API | FR-003, FR-006 |
| 3 | Inventory and logistics | FR-007, FR-008 |
| 4 | Reporting and application UI | FR-009 |
| 5 | Workflow automation | FR-010, FR-011 |
| 6 | AI assistance and extensions | FR-012, FR-013, FR-014 |

Requirements should be traceable to test cases and the datasets used to validate them.

## 13. Acceptance and Change Control

This document is a **working baseline**, not a signed stakeholder approval. Requirements are ready for implementation only when their acceptance criteria, input fields, exception handling, and business ownership are sufficiently defined. Changes should update the document version and record the affected requirement IDs.

### Checkpoint 2.1 outcome

The project has identified business stakeholders, end-to-end process boundaries, the initial functional requirement catalog, non-functional expectations, data domains, and the weighted supplier evaluation strategy. Detailed FR-005 formulas and the first data dictionary are documented separately to avoid duplicating technical specifications.

---

**Next documentation step:** Resolve the remaining scoring-policy decisions, then begin the connected synthetic dataset design and generation exercises.
