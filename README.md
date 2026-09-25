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

Before writing any transformation logic, we established a quantitative data-quality baseline exported to [`reports/data_quality_before.csv`](reports/data_quality_before.csv).

| Metric | Baseline Value | Key Diagnostic Takeaway |
| :--- | :--- | :--- |
| **Total Rows** | 315,963 | Full administrative inspection records from 2010 to present. |
| **Total Columns** | 17 | 10 string, 5 numerical (float/int), 2 spatial coordinates. |
| **Exact Duplicate Rows** | 0 | Every record is distinct at the row level. |
| **Duplicate Inspection IDs** | 0 | `Inspection ID` serves as a reliable surrogate primary key. |
| **Total Missing Cells** | 100,409 (1.87%) | Concentrated heavily in `Violations` and `Facility Type`. |

### Key Anomaly Discoveries:
1. **Unstructured Violation Strings (`Violations`):** 89,080 rows (28.19%) are null (ordinarily indicating a clean inspection with no citations), while 225,170 rows contain multi-part concatenated free text requiring a dedicated parsing engine.
2. **Whitespace Padding:** Over 246,705 `Address` records and 31,490 `Violations` strings have leading/trailing whitespace.
3. **Casing & Categorical Explosion:**
   * `Facility Type` exhibits 527 raw categories, collapsing to 473 when stripped and lowercased.
   * `City` contains 94 distinct entries including typographical errors (`CCHICAGO`, `CHICAGOCHICAGO`, `CHICAGOO`, `CHicago`, `CHICAGO.`) and suburban jurisdictions.
4. **Data Type & Schema Flaws:**
   * `License #` and `Zip` are loaded as floating-point numbers due to missing values (`NaN`).
   * 833 records possess `License # == 0`.
   * Out-of-state / extreme ZIP codes detected (ranging from `10014.0` in NY to `91706.0` in CA).
   * `Inspection Date` is stored as an unparsed `MM/DD/YYYY` string.
5. **Non-Standard Classifications:** `Risk` contains 83 instances of `"All"`, deviating from standard Chicago food safety risk tiers (*Risk 1 High*, *Risk 2 Medium*, *Risk 3 Low*).

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
│   ├── interim/              # Intermediate transformed stages
│   └── processed/            # Validated, analysis-ready clean datasets
│
├── src/                      # Modular production source code
│   ├── __init__.py
│   └── profiling.py          # Automated baseline data profiling module
│
├── tests/                    # Automated unit and quality tests
│   └── test_profiling.py
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

### 4. Run baseline profiling & tests
```bash
# Run automated data profiling baseline:
python src/profiling.py

# Run unit tests:
pytest
```

---

## 📅 7-Day Project Roadmap

- [x] **Day 1: Project Setup, Architecture & Data Verification**
- [x] **Day 2: Exploratory Data Analysis & Data Quality Profiling**
- [ ] **Day 3: Text Parsing & Violation Extraction Engine**
- [ ] **Day 4: Categorical & Geographic Standardization**
- [ ] **Day 5: Missing Data, Outliers & Anomaly Detection**
- [ ] **Day 6: Automated Data Validation & Test Suite**
- [ ] **Day 7: Pipeline Orchestration, Documentation & Portfolio Showcase**
