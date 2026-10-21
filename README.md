# NovaTech Industries
## Intelligent Procurement & Logistics Management Platform

**A Python, PostgreSQL, and Streamlit business analytics portfolio project**

### Project Overview

NovaTech Industries is a fictional manufacturing company used to demonstrate an integrated procurement and logistics analytics platform.

The platform supports supplier evaluation, procurement analysis, shipment monitoring, exception management, logistics risk assessment, and interactive what-if scenario analysis.

It combines structured business processes, relational data modelling, analytical scoring methods, and interactive dashboards to help analysts investigate operational performance and support evidence-based decisions.

The application was developed using **Python 3.12, PostgreSQL 17, Streamlit, Pandas, and Pytest**.

### Business Problem

Procurement and logistics teams frequently need to make decisions using information distributed across suppliers, quotations, historical delivery records, quality inspections, and shipment tracking systems.

This creates several analytical challenges:

- Comparing suppliers using consistent commercial and operational criteria.
- Evaluating delivery reliability and historical supplier performance.
- Identifying shipment delays and unresolved operational exceptions.
- Understanding how changing logistics conditions affect shipment risk.
- Maintaining traceability of procurement assessments and decisions.

### Project Objectives

The NovaTech platform was designed to:

1. Consolidate synthetic procurement and logistics data within a relational PostgreSQL database.
2. Evaluate suppliers using a weighted, rule-based scoring methodology.
3. Provide analytical visibility into procurement and delivery performance.
4. Support shipment tracking and structured exception management.
5. Assess shipment risks using transparent heuristic scoring rules.
6. Enable analysts to simulate hypothetical logistics scenarios without modifying operational records.
7. Demonstrate automated testing, data governance, and auditability.

### Project Scope and Limitations

NovaTech Industries is a **fictional company**, and all demonstration data is **synthetic and unverified**.

The platform is intended for portfolio demonstration and analytical experimentation. It is not a production procurement system.

Supplier assessments and logistics risk scores are rule-based analytical outputs, not validated predictions. The application does not authorize purchases, execute procurement transactions, or dispatch real shipments.

### Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Application logic and analytical processing |
| PostgreSQL 17 | Relational database and structured data storage |
| Psycopg 3 | PostgreSQL connectivity |
| Pandas | Data processing and analytical reporting |
| Streamlit | Interactive business intelligence dashboard |
| Pytest | Automated testing and validation |
| Git / GitHub | Version control and portfolio publication |

### Current Platform Status

**Version:** V11  
**Dashboard sections:** 10  
**Automated tests:** 238 passing  
**Development status:** Feature-complete portfolio demonstration

The platform includes analytical and governance controls intended to distinguish hypothetical assessments from real operational decisions.

## Platform Capabilities

The NovaTech Industries platform includes ten interactive dashboard sections covering procurement analysis, supplier evaluation, logistics operations, and risk management.

| Dashboard Section | Business Function |
|---|---|
| **1. Procurement Overview** | Provides visibility into procurement activity, requisitions, quotations, and supplier information. |
| **2. Supplier Comparison** | Supports supplier evaluation using weighted commercial and operational performance criteria. |
| **3. Procurement Insights** | Presents procurement KPIs and analytical insights to support sourcing decisions. |
| **4. Logistics Intelligence** | Analyzes historical delivery performance and logistics-related operational metrics. |
| **5. Shipment Tracking** | Displays shipment information, tracking events, and delivery progress. |
| **6. Shipment Exception Management** | Supports the identification, investigation, and resolution of shipment-related exceptions. |
| **7. Decision & Audit Trail** | Provides visibility into procurement assessments, decisions, and recorded audit information. |
| **8. Analyst Workspace** | Supports structured analyst assessments within the procurement evaluation workflow. |
| **9. Logistics Risk Intelligence** | Evaluates shipment risk using transparent, rule-based scoring criteria. |
| **10. Logistics Risk Scenario Analysis** | Enables analysts to compare baseline shipment risks with hypothetical scenarios without modifying database records. |

### Supplier Evaluation Methodology

The supplier evaluation model combines four weighted criteria:

| Evaluation Criterion | Weight |
|---|---:|
| Cost competitiveness | 40% |
| Delivery performance | 25% |
| Quality performance | 20% |
| Supplier reliability | 15% |
| **Total** | **100%** |

The evaluation process also applies eligibility and governance controls. A supplier's weighted score does not automatically authorize a purchasing decision.

### Logistics Risk Assessment

The logistics risk engine evaluates shipment conditions using three primary factors:

- **Delivery delays:** Risk points are assigned according to the number of overdue days.
- **Shipment status:** Shipments with an exception status receive additional risk points.
- **Unresolved exceptions:** The highest unresolved exception severity contributes to the risk assessment.

The resulting score ranges from 0 to 100 and is classified into four risk levels:

| Risk Score | Classification |
|---|---|
| 0–19 | LOW |
| 20–39 | MEDIUM |
| 40–69 | HIGH |
| 70–100 | CRITICAL |

These scores are heuristic indicators designed for analytical prioritization. They are not statistical probabilities or validated delivery forecasts.

### What-If Scenario Analysis

The Scenario Analysis module allows analysts to explore how hypothetical changes could affect shipment risk.

Supported scenarios include:

- Changing the estimated delivery date.
- Simulating a different shipment status.
- Introducing a hypothetical unresolved exception.
- Adjusting the severity of existing unresolved exceptions.

The application compares baseline and hypothetical risk scores, identifies changes in risk classification, and displays the contributing risk factors.

All scenario calculations are performed in memory. **No PostgreSQL records are modified by the scenario engine.**

### Data Governance and Validation

The platform incorporates controls to support transparent and traceable analytical workflows.

Key safeguards include:

- Synthetic and unverified data classification.
- Separation of analytical assessments from purchasing authorization.
- Structured procurement decision and audit records.
- Validation of scenario inputs and business rules.
- Automated testing of analytical calculations and service logic.
- Explicit identification of hypothetical scenario results.

The project includes **238 passing automated tests**, covering supplier evaluation, procurement insights, shipment tracking, exception management, logistics risk assessment, and scenario analysis.

## Technical Architecture

NovaTech Industries follows a modular architecture that separates data generation, database operations, analytical processing, and dashboard presentation.

### Architecture Overview

```text
Synthetic Data Generation
          |
          v
    PostgreSQL 17
          |
          v
Database Services & Queries
          |
          v
Python Analytical Engines
          |
          v
Streamlit Dashboard (V11)
          |
          v
Business Insights & What-If Analysis
```

The application uses PostgreSQL as its primary structured data store. Python modules retrieve and process procurement and logistics records, apply analytical business rules, and present the results through an interactive Streamlit interface.

The Logistics Risk Scenario Analysis module operates on in-memory copies of shipment data, ensuring hypothetical changes do not modify stored records.

### Database Architecture

The PostgreSQL database is named `novatech` and organizes information into three business-oriented schemas.

| Schema | Purpose |
|---|---|
| `procurement` | Procurement records, suppliers, quotations, assessments, and related business information |
| `logistics` | Shipment records, tracking events, and shipment exception management |
| `analytics` | Analytical and supporting data structures |

The relational model uses primary and foreign keys to support consistent relationships between business entities.

### Project Structure

```text
ai-procurement-platform/
|
|-- README.md
|-- requirements.txt
|-- .gitignore
|
|-- docs/
|   |-- business/
|   `-- data/
|
|-- sql/
|   `-- logistics/
|       |-- 001_shipment_tracking.sql
|       `-- 002_shipment_exception_management.sql
|
|-- src/
|   |-- analysis/
|   |   |-- evaluate_suppliers_v5.py
|   |   |-- procurement_insights.py
|   |   |-- logistics_delivery_performance.py
|   |   |-- shipment_monitoring.py
|   |   |-- logistics_risk_intelligence.py
|   |   `-- logistics_risk_scenarios.py
|   |
|   |-- dashboard/
|   |   |-- app.py
|   |   `-- logistics_risk_scenario_page.py
|   |
|   |-- database/
|   |   |-- connection.py
|   |   |-- assessment_service.py
|   |   |-- shipment_tracking_service.py
|   |   `-- shipment_exception_service.py
|   |
|   `-- data_generation/
|
`-- tests/
```

The directory diagram highlights the principal application components rather than every development file.

### Core Application Components

**Data Generation**

Python scripts generate synthetic procurement, supplier performance, and historical operational records for demonstration and testing.

**Database Layer**

Database services provide structured access to PostgreSQL records, including procurement assessments, shipment tracking, and exception management.

**Analytical Layer**

Independent Python modules implement supplier evaluation, procurement insights, delivery performance analysis, shipment monitoring, and logistics risk assessment.

**Presentation Layer**

Streamlit provides the interactive dashboard through which users can explore business metrics, investigate operational records, and evaluate hypothetical scenarios.

**Testing Layer**

Pytest validates analytical rules, input handling, service behavior, and scenario calculations.

### Application Entry Point

The main dashboard is launched from the project root using:

```bash
python -m streamlit run src/dashboard/app.py
```

The application requires a configured PostgreSQL database containing the expected schemas and demonstration data.

Database setup and reproducibility instructions will be documented separately before public release.

## Installation and Local Setup

### Prerequisites

- Python 3.12
- PostgreSQL 17
- Git
- A terminal and Python-compatible development environment

The application has been developed and tested locally on macOS. Other operating systems may require adjustments to the commands below.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-procurement-platform.git
cd ai-procurement-platform
```

Replace `YOUR_USERNAME` with the GitHub username associated with the published repository.

### 2. Create a Python Virtual Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Create the PostgreSQL Database

Create a dedicated demonstration database:

```bash
createdb novatech_demo
```

The database must be accessible to the PostgreSQL user running the application.

### 5. Restore the Database Schema

```bash
psql -d novatech_demo -v ON_ERROR_STOP=1 \
  -f sql/setup/novatech_schema.sql
```

This restores the procurement, logistics, and analytics schemas and their associated database structures.

### 6. Import Synthetic Data

First, validate the datasets:

```bash
python scripts/load_synthetic_data.py --dry-run
```

Then import the demonstration data:

```bash
DB_NAME=novatech_demo python scripts/load_synthetic_data.py
```

The importer loads **481 synthetic records across 15 datasets**.

It refuses to import into populated destination tables and only permits the explicitly named `novatech_demo` database.

### 7. Initialize Shipment Demonstration Records

Validate the configuration:

```bash
python scripts/initialize_demo_shipments.py --dry-run
```

Initialize the demonstration shipment and exception history:

```bash
DB_NAME=novatech_demo python scripts/initialize_demo_shipments.py
```

This creates a simulated shipment with three tracking events and a completed exception workflow containing six audit events.

The initializer is designed for a fresh demonstration database. It should not be rerun against partially initialized records.

### 8. Launch the Dashboard

```bash
DB_NAME=novatech_demo python -m streamlit run src/dashboard/app.py
```

Open the local Streamlit address displayed in your terminal, normally:

`http://localhost:8501`

The application provides ten dashboard sections covering procurement, supplier evaluation, logistics intelligence, shipment tracking, exception management, and risk scenario analysis.

### 9. Run Automated Tests

```bash
python -m pytest tests/ -q
```

The development version has previously passed **238 automated tests**. Results may vary if dependencies, application code, or test configurations change.

### PostgreSQL Connection Configuration

The database connection module supports the following environment variables:

| Variable | Purpose |
|---|---|
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL username |
| `DB_HOST` | PostgreSQL host |
| `DB_PORT` | PostgreSQL port |
| `DB_PASSWORD` | PostgreSQL password |

If connection details are not supplied, Psycopg uses PostgreSQL's available connection defaults.

**Security:** Never commit database passwords, local `.env` files, or other credentials to the repository.

### Reproducibility Notes

The demonstration environment has been successfully initialized in an isolated PostgreSQL database using the exported schema, 15 synthetic datasets, and shipment initialization services.

The platform is intended for local analytical demonstration. It does not connect to live procurement systems, authorize purchases, or dispatch real shipments.

## Dashboard Gallery

NovaTech Industries V11 includes ten interactive dashboard sections covering procurement analytics, supplier evaluation, logistics operations, exception management, and risk intelligence.

All screenshots below show the platform operating with synthetic demonstration data.

### 1. Procurement Overview

Monitor procurement activity and key performance indicators through a centralized analytical dashboard.

![Procurement Overview](docs/screenshots/Procurement%20Overview.png)

### 2. Supplier Comparison

Compare suppliers using weighted evaluation scores, operational performance indicators, and eligibility criteria.

![Supplier Comparison](docs/screenshots/Supplier%20Comparison.png)

### 3. Procurement Insights

Explore procurement patterns and analytical insights to support data-driven decision-making.

![Procurement Insights](docs/screenshots/Procurement%20Insights.png)

### 4. Logistics Intelligence

Analyze logistics performance and operational indicators across the supply chain.

![Logistics Intelligence](docs/screenshots/Logistics%20Intelligence.png)

### 5. Shipment Tracking

Monitor simulated shipment statuses, delivery timelines, and chronological tracking events.

![Shipment Tracking](docs/screenshots/Shipment%20Tracking.png)

### 6. Shipment Exception Management

Manage simulated shipment exceptions through structured workflows, corrective actions, and auditable status transitions.

![Shipment Exception Management](docs/screenshots/Shipment%20Exception%20Management.png)

### 7. Decision & Audit Trail

Review procurement decisions and supporting audit records to improve transparency and traceability.

![Decision and Audit Trail](docs/screenshots/Decision%20%26%20Audit%20Trail.png)

### 8. Analyst Workspace

Explore procurement and logistics information through a dedicated analytical workspace.

![Analyst Workspace](docs/screenshots/Analyst%20Workspace.png)

### 9. Logistics Risk Intelligence

Identify and prioritize simulated shipment risks using explainable scoring rules and operational indicators.

![Logistics Risk Intelligence](docs/screenshots/Logistics%20Risk%20Intelligence.png)

### 10. Logistics Risk Scenario Analysis

Explore hypothetical logistics risk scenarios and evaluate how changes in shipment conditions affect risk scores.

![Logistics Risk Scenario Analysis](docs/screenshots/Logistics%20Risk%20Scenario%20Analysis.png)

---

**Demonstration disclaimer:** All displayed records are synthetic and unverified. The platform is designed for analytical demonstration and decision support, not autonomous procurement authorization or real-world shipment execution.