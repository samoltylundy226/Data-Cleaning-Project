# 🧼 Chicago Food Inspections — End-to-End Data Cleaning & Data Quality Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An end-to-end, production-style data cleaning, standardization, and data quality assurance pipeline built on the City of Chicago Food Inspections dataset.

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

## 🗂️ Project Structure

```text
chicago-food-inspections-data-quality-pipeline/
│
├── README.md                 # Project documentation and pipeline guide
├── LICENSE                   # MIT Open Source License
├── .gitignore                # Git ignore rules (raw data & venvs excluded)
├── requirements.txt          # Python dependencies
├── Makefile                  # Automation commands
├── pytest.ini                # Pytest configuration
├── verify_setup.py           # Day 1 verification & ingestion script
│
├── config/
│   └── config.yaml           # Pipeline configuration and paths
│
├── data/
│   ├── raw/                  # Immutable original dataset (git-ignored)
│   ├── interim/              # Intermediate cleaned data (git-ignored)
│   └── processed/            # Validated, analysis-ready clean datasets
│
├── src/                      # Modular production source code
│   ├── __init__.py
│   ├── profiling.py          # Automated baseline data profiling module
│   └── cleaning.py           # Core data cleaning & standardization engine
│
├── tests/                    # Automated unit and quality tests
│   ├── test_profiling.py     # Unit tests for profiling module
│   └── test_cleaning.py      # Unit tests for cleaning transformations
│
├── reports/
│   ├── figures/              # Generated quality audit charts and summaries
│   └── data_quality_before.csv # Automated Day 2 baseline audit report
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

### 4. Execute pipeline modules & test suite
```bash
# Run baseline profiling:
python src/profiling.py

# Execute core cleaning pipeline (generates data/interim/):
python src/cleaning.py

# Run test suite:
pytest
```

---

## 📅 7-Day Project Roadmap

- [x] **Day 1: Project Setup, Architecture & Data Verification**
- [x] **Day 2: Exploratory Data Analysis & Data Quality Profiling**
- [x] **Day 3: Core Data Cleaning & Standardization Engine**
- [ ] **Day 4: Text Parsing & Violation Extraction Engine**
- [ ] **Day 5: Missing Data, Outliers & Anomaly Detection**
- [ ] **Day 6: Automated Data Validation & Test Suite**
- [ ] **Day 7: Pipeline Orchestration, Documentation & Portfolio Showcase**
