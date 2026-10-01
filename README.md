# 🧼 Chicago Food Inspections — End-to-End Data Cleaning & Data Quality Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An end-to-end, production-style data cleaning, standardization, data validation, and data quality assurance pipeline built on the City of Chicago Food Inspections dataset.

---

## 📌 Project Overview

This repository demonstrates professional data engineering, data cleaning, and data quality practices applied to complex real-world municipal administrative data. Rather than relying on ad-hoc cleaning in one-off notebooks, this project implements a modular, reproducible, test-driven pipeline.

* **Data Source:** [City of Chicago Data Portal - Food Inspections](https://data.cityofchicago.org/Health-Human-Services/Food-Inspections/4ijn-s7e5)
* **Dataset Identifier:** `4ijn-s7e5`
* **Volume:** **315,963** inspection records (2010 to Present) across 17 raw features (~330.8 MB CSV).
* **Core Challenges Addressed:**
  * Free-text violation log parsing (extracting violation codes, descriptions, and inspector comments).
  * High-cardinality categorical standardization (`Facility Type` standardization and risk classification).
  * Address parsing and geographic anomaly resolution (ZIP code, street standardization, coordinate validation).
  * Strict schema enforcement and automated data quality checks.

---

## 📊 Baseline Data Quality Findings (Day 2 Pre-Cleaning Audit)

Before writing transformation logic, we established a quantitative data-quality baseline exported to [`reports/data_quality_before.csv`](reports/data_quality_before.csv).

| Metric | Baseline Value | Key Diagnostic Takeaway |
| :--- | :--- | :--- |
| **Total Rows** | 315,963 | Full administrative inspection records from 2010 to present. |
| **Total Columns** | 17 | 10 string, 5 numerical (float/int), 2 spatial coordinates. |
| **Exact Duplicate Rows** | 0 | Every record is distinct at the row level. |
| **Duplicate Inspection IDs** | 0 | `Inspection ID` serves as a reliable surrogate primary key. |
| **Total Missing Cells** | 100,409 (1.87%) | Concentrated heavily in `Violations` and `Facility Type`. |

---

## 🧹 Core Data Cleaning Engine (Day 3 Transformations)

Implemented in [`src/cleaning.py`](src/cleaning.py), the cleaning engine enforces strict domain rules without destroying data integrity:

* **Zero Rows Blindly Deleted:** All **315,963 records** are retained; missing values are imputed through domain-appropriate policies.
* **Column Name Normalization:** Raw headers converted to standardized snake_case identifiers.
* **Whitespace & Casing Normalization:** Over **246,705 addresses** and text fields stripped of padding and standardized to uppercase.
* **Missing Value Imputations:**
  * `aka_name`: **2,424 records** filled using the legal `dba_name`.
  * `facility_type`: **5,347 records** imputed with `'UNKNOWN'`.
  * `violations`: **89,080 records** (clean inspections with no citations) imputed with `'NO VIOLATIONS CITED'`.
  * `risk`: **87 records** imputed with `'NOT SPECIFIED'`.
* **Geographic & Regex Standardization:**
  * **315,683 records** unified to `'CHICAGO'`, correcting typographical variations (`CCHICAGO`, `CHICAGOCHICAGO`, `CHICAGOO`, etc.) while preserving distinct municipalities (`CHICAGO HEIGHTS`, `EVANSTON`).
  * **315,921 ZIP codes** converted from float (`60601.0`) to standard 5-digit zero-padded strings (`60601`).
  * Spatial coordinates validated against the Chicago bounding box (lat `[41.60, 42.10]`, lon `[-87.95, -87.50]`).
* **Category Normalization:**
  * `Facility Type`: Consolidated from **527 raw categories** to **293 standard categories** using regex grouping.
  * `Risk`: Standardized non-standard `'All'` entries to `'Risk 1 (High)'`.
* **Datatypes & Temporal Features:**
  * `inspection_date`: Parsed to `datetime64[ns]` across all 315,963 records.
  * Derived features added: `inspection_year`, `inspection_month`, `inspection_day_of_week`.
  * Output exported to: `data/interim/food_inspections_interim.csv` (336.90 MB, 20 columns).

---

## 🛡️ Data Validation & Anomaly Detection Layer (Day 4)

Implemented in [`src/validation.py`](src/validation.py) and [`src/anomaly_detection.py`](src/anomaly_detection.py), this layer executes automated business-rule validations and statistical outlier profiling.

### 1. Automated Validation Scorecard ([`reports/validation_report.csv`](reports/validation_report.csv))
* **Evaluation Result:** **5 PASS | 4 WARNING | 0 FAIL** across all 9 automated integrity checks.
* **Primary Key & Schema:** `inspection_id` is 100% unique, positive, and non-null; all canonical schema features verified.
* **Temporal Integrity:** 100% of inspection dates fall strictly within the valid operational window (`2010-01-04` to `2026-09-23`) with zero future or corrupted timestamps.
* **Category Compliance:** 100% compliance with official Chicago `Results` (7 discrete categories) and `Risk` tiers.
* **Monitored Warnings:**
  * `VAL-003`: 3 records flagged with empty address strings (`'   '`).
  * `VAL-005`: 1,051 records lack geographic coordinates (retained for inspection record integrity).
  * `VAL-006`: 2,334 suburban/regional non-606xx ZIP codes (valid border-overlap food establishments).
  * `VAL-009`: 3,648 inspections resulted in `FAIL` without text violations (administrative/access closures).

### 2. Anomaly Taxonomy & Outlier Principles ([`reports/anomaly_report.csv`](reports/anomaly_report.csv))
In professional data science, **statistical outliers must not be blindly deleted**:

| Anomaly Type | Classification | Detection Method | Policy & Rationale |
| :--- | :--- | :--- | :--- |
| **Inspection Frequency per License** | Statistical Outlier | IQR Upper Fence (21 visits) & 99th Pct | **RETAIN:** High-frequency licenses (max 198 visits) represent long-lived airport terminals (O'Hare) and stadiums. Deleting them would erase the city's largest dining hubs. |
| **Citation Spikes per Inspection** | Statistical Outlier | IQR Upper Fence (12.5 citations) | **RETAIN:** Single inspections with 15–40 citations represent critical unsanitary emergencies, providing the primary signal for food-safety risk modeling. |
| **Distance from City Hall (> 25 km)** | Legitimate Unusual Observation | Haversine Distance Threshold | **RETAIN:** Legitimate peripheral jurisdictions like O'Hare Airport (26 km NW) and far southern wards (Hegewisch). |
| **Weekend Inspections (Sat/Sun)** | Legitimate Unusual Observation | Day-of-Week Profiling (136 records) | **RETAIN:** Off-hour inspections for special summer food festivals (Taste of Chicago) and urgent complaint investigations. |
| **Blank Address Strings (`'   '`)** | Data-Entry Error | Whitespace Strip & Length Check (3 records) | **IMPUTE:** Source clerical error; repair with `'ADDRESS UNKNOWN'` to maintain record integrity. |

---

## ⚙️ End-to-End Pipeline Orchestration (Day 5)

Implemented in [`src/pipeline.py`](src/pipeline.py) and [`src/ingestion.py`](src/ingestion.py), the master pipeline orchestrator automates the complete data engineering lifecycle into a reproducible, single-command workflow:

```text
RAW DATA  ──►  INGESTION  ──►  PROFILING  ──►  CLEANING  ──►  ANOMALY DETECTION  ──►  VALIDATION  ──►  PROCESSED DATA  ──►  QUALITY REPORT
```

### 1. Architectural Stages
1. **Ingestion & Validation (`src/ingestion.py`):** Loads centralized configuration (`config/config.yaml`), verifies raw file checksum/existence, and streams downloads on demand without mutating source data.
2. **Pre-Cleaning Profiling (`src/profiling.py`):** Computes pre-transformation baseline statistics and exports [`reports/data_quality_before.csv`](reports/data_quality_before.csv).
3. **Data Cleaning & Standardization (`src/cleaning.py`):** Executes all casing, whitespace, ZIP code, facility type, temporal, and missing-value transformations; writes the interim dataset to `data/interim/food_inspections_interim.csv`.
4. **Anomaly Detection & Outlier Flagging (`src/anomaly_detection.py`):** Computes statistical bounds (IQR fences, Haversine spatial radii, calendar distributions) and exports [`reports/anomaly_report.csv`](reports/anomaly_report.csv).
5. **Quality Gating & Validation (`src/validation.py`):** Asserts 9 business and schema rules. If any `CRITICAL` rule fails, execution halts immediately; non-critical findings are recorded in [`reports/validation_report.csv`](reports/validation_report.csv).
6. **Processed Data Export:** Exports the validated, analysis-ready dataset to `data/processed/food_inspections_cleaned.csv` (336.90 MB, 315,963 rows, 20 columns).
7. **Post-Cleaning Quality Reporting:** Generates [`reports/data_quality_after.csv`](reports/data_quality_after.csv) providing a comparative post-cleaning audit.
8. **Structured Dual-Output Logging:** Records all pipeline events with millisecond timestamps to console and `pipeline.log`.

---

## 🧪 Automated Testing & Continuous Verification (Day 6)

Reliability and reproducibility require test-driven data engineering. Day 6 implements a comprehensive, ultra-fast `pytest` test suite (**46 passing tests in < 1 second**) utilizing isolated, synthetic micro-datasets without unneeded dependencies on heavy raw data files.

### 1. Test Suite Architecture

| Test Module | Test Focus | Count | Key Test Assertions |
| :--- | :--- | :---: | :--- |
| [`tests/test_cleaning.py`](tests/test_cleaning.py) | Cleaning Engine | 9 | Missing value fallbacks (`aka_name` $\to$ `dba_name`, clean inspection text), whitespace stripping, duplicate key dropping, ZIP zero-padding, datetime conversion, facility classification. |
| [`tests/test_validation.py`](tests/test_validation.py) | Data Validation & Gates | 23 | Schema conformance, primary key uniqueness and non-null enforcement, date window clamping, Chicago bounding box spatial rules, 5-digit ZIP structure, official results/risk categories. |
| [`tests/test_anomalies.py`](tests/test_anomalies.py) | Anomaly Profiling | 7 | Haversine distance accuracy, IQR fence outlier thresholding, citation count spike detection, weekend inspection capture, whitespace address detection, anomaly registry generation. |
| [`tests/test_pipeline.py`](tests/test_pipeline.py) | Master Orchestration | 5 | Configuration resolution, raw data availability checks, Windows-safe logger lifecycle, after-report generation, comparison report generation. |
| [`tests/test_profiling.py`](tests/test_profiling.py) | Baseline Profiling | 2 | Dataset overview metrics, column-level profile generation and diagnostic rule checks. |

### 2. Programmatic Before vs. After Data Quality Scorecard ([`reports/data_quality_comparison.csv`](reports/data_quality_comparison.csv))

Generated programmatically via `src/quality_report.py` directly from `data/raw/food_inspections_raw.csv` and `data/processed/food_inspections_cleaned.csv` with zero hardcoded estimates:

| Dimension | Metric | Raw Baseline (Before) | Cleaned Pipeline (After) | Net Impact | Real-World Domain Significance |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Dataset Volume** | Total Inspection Rows | 315,963 | 315,963 | **+0 (100% Retained)** | **Zero rows blindly deleted.** Every historic inspection record is preserved. |
| **Schema Structure** | Feature Columns | 17 columns | 20 columns | **+3 columns** | 17 normalized snake_case features + 3 engineered temporal features (`year`, `month`, `day_of_week`). |
| **Completeness** | Missing Data Cells | 100,409 (1.87%) | 3,199 (0.05%) | **-97,210 (-96.8%)** | Remaining nulls are strictly controlled domain nulls (1,051 missing coords, 42 unrecoverable ZIPs). |
| **Integrity** | Duplicate Rows | 0 | 0 | 0 | Every inspection row represents a distinct administrative event. |
| **Integrity** | Primary Key Duplicates | 0 | 0 | 0 | `inspection_id` verified as 100% unique, non-null surrogate primary key. |
| **Data Validity** | Invalid Values Resolved | 316,049 | 0 | **-316,049 (-100%)** | Resolved unparsed string dates (315,963), non-standard Risk 'All' (83), and blank addresses (3). |
| **Quality Gate** | Critical Validation Failures | 4 FAILURES | **0 FAILURES** | **-4 Failures (-100%)** | Pre-cleaning failed schema, dates, risk, and boundary checks; post-cleaning passes 100% of critical rules. |
| **Temporal Validity** | Unparsed Datetime Strings | 315,963 (string) | 0 (datetime64[us]) | **-315,963 (-100%)** | 100% of inspection timestamps converted to native datetime objects for time-series modeling. |
| **Missing Imputation** | Missing AKA Names | 2,424 missing | 0 missing | **-2,424 (-100%)** | Imputed missing trade names via legal DBA fallback without data loss. |
| **Missing Imputation** | Clean Inspections Missing Citations | 89,080 nulls (28.2%) | 0 nulls (0.0%) | **-89,080 (-100%)** | Imputed with domain string `"NO VIOLATIONS CITED"` to clarify clean inspection outcomes. |
| **Consistency** | Address Whitespace Padding | 246,705 records | 0 records | **-246,705 (-100%)** | Stripped leading/trailing whitespace and collapsed internal multi-spaces. |
| **Cardinality** | Facility Type Categories | 527 raw categories | 293 clean categories | **-234 (-44.4%)** | Regex grouping consolidated casing and spelling variations while preserving granular categories. |

---

## 🗂️ Project Structure

```text
chicago-food-inspections-data-quality-pipeline/
│
├── README.md                 # Project documentation and pipeline guide
├── LICENSE                   # MIT Open Source License
├── .gitignore                # Git ignore rules (raw data, logs & venvs excluded)
├── requirements.txt          # Python dependencies
├── Makefile                  # Automation commands
├── pytest.ini                # Pytest configuration
├── verify_setup.py           # Day 1 verification & ingestion script
│
├── config/
│   └── config.yaml           # Centralized pipeline configuration and paths
│
├── data/
│   ├── raw/                  # Immutable original dataset (git-ignored)
│   ├── interim/              # Intermediate cleaned data (git-ignored)
│   └── processed/            # Validated, analysis-ready clean datasets (git-ignored)
│
├── src/                      # Modular production source code
│   ├── __init__.py
│   ├── ingestion.py          # Data ingestion and source retrieval module
│   ├── profiling.py          # Automated baseline data profiling module
│   ├── cleaning.py           # Core data cleaning & standardization engine
│   ├── validation.py         # Automated data validation & integrity suite
│   ├── anomaly_detection.py  # Statistical outlier & anomaly profiling engine
│   ├── quality_report.py     # Programmatic before vs after quality comparison engine
│   └── pipeline.py           # Master end-to-end pipeline orchestrator
│
├── tests/                    # Automated test suite (46 passing unit tests)
│   ├── test_cleaning.py      # Unit tests for cleaning transformations (9 tests)
│   ├── test_validation.py    # Unit tests for validation rules (23 tests)
│   ├── test_anomalies.py     # Unit tests for anomaly & outlier methods (7 tests)
│   ├── test_pipeline.py      # Unit tests for pipeline orchestrator & reports (5 tests)
│   └── test_profiling.py     # Unit tests for profiling module (2 tests)
│
├── reports/
│   ├── figures/              # Generated quality audit charts and summaries
│   ├── data_quality_before.csv # Automated Day 2 baseline audit report
│   ├── data_quality_after.csv  # Automated Day 5 post-cleaning audit report
│   ├── data_quality_comparison.csv # Automated Day 6 before vs after scorecard
│   ├── validation_report.csv   # Automated Day 4 validation scorecard
│   └── anomaly_report.csv      # Automated Day 4 anomaly registry
│
└── notebooks/
    └── 01_exploration.ipynb  # Exploratory Data Analysis & quality audits
```

---

## 🚀 Quickstart Guide

### 1. Clone the repository
```bash
git clone https://github.com/samoltylundy226/Data-Cleaning-Project.git
cd Data-Cleaning-Project
```

### 2. Set up virtual environment
```powershell
# Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Execute master pipeline, reports & test suite
```bash
# Execute master end-to-end data quality pipeline:
python -m src.pipeline

# Generate programmatic before vs after comparison report:
python -m src.quality_report

# Run full unit test suite (46 passing tests in < 1 second):
python -m pytest
```

---

## 📅 7-Day Project Roadmap

- [x] **Day 1: Project Setup, Architecture & Data Verification**
- [x] **Day 2: Exploratory Data Analysis & Baseline Data Quality Profiling**
- [x] **Day 3: Core Data Cleaning & Standardization Engine**
- [x] **Day 4: Automated Data Validation & Anomaly Detection Layer**
- [x] **Day 5: Master Pipeline Orchestration & End-to-End Automation**
- [x] **Day 6: Automated Testing & Continuous Verification (pytest)**
- [ ] **Day 7: Pipeline Packaging, Documentation & Portfolio Showcase**

