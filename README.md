# 🧼 Chicago Food Inspections — End-to-End Data Cleaning & Data Quality Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests: pytest](https://img.shields.io/badge/tests-46%20passed-brightgreen.svg)](https://docs.pytest.org/)
[![Data Quality Gate: PASSED](https://img.shields.io/badge/quality%20gate-0%20critical%20failures-success.svg)](reports/validation_report.csv)

An end-to-end, production-grade data engineering, data cleaning, automated validation, and data quality pipeline applied to the City of Chicago Food Inspections dataset (**315,963 records**, 2010 to Present, ~330.8 MB CSV).

---

## 📌 1. Project Overview

In real-world data science and machine learning, **data quality is the primary ceiling on model performance**. Municipal, healthcare, and enterprise transactional records are rarely pristine; they arrive with missing trade names, typographical errors, unparsed timestamps, out-of-bounds GPS coordinates, and unstructured free-text violation logs.

Rather than relying on fragile, one-off notebook scripts or destructive row deletion (e.g. `df.dropna()`), this project implements a **reproducible, test-driven data quality pipeline**. The system ingests raw municipal records, profiles pre-cleaning messiness, executes standardized domain-specific cleaning, flags statistical anomalies, enforces an automated 9-rule quality gate, exports analysis-ready data, and outputs programmatic before-and-after audit reports.

---

## 🎯 2. Problem Statement

Downstream predictive systems—such as public health risk scoring, inspection scheduling optimization, and compliance classification—require reliable, uniform inputs. Applying standard ML algorithms directly to the raw Chicago Food Inspections dataset fails due to:
1. **Unparsed String Dates:** Raw dates (`"04/18/2023"`) prevent temporal indexing and seasonal trend extraction.
2. **High-Cardinality Casing & Typos:** Over 80 spelling variants of Chicago (e.g., `CCHICAGO`, `CHICAGOCHICAGO`) and 527 unstandardized facility types fragment group-by aggregations.
3. **Misleading Null Values:** Over 28% of records contain nulls in the `Violations` field, which naive data cleaning deletes, inadvertently erasing thousands of clean inspections.
4. **Unregulated Primary Keys & Out-of-Bounds Coordinates:** Erroneous latitudes/longitudes and missing ZIP codes corrupt geographic spatial mapping.

This project solves these issues programmatically while guaranteeing **zero rows blindly deleted**.

---

## 🏛️ 3. Dataset Source & Business Context

* **Source Authority:** [City of Chicago Data Portal](https://data.cityofchicago.org/Health-Human-Services/Food-Inspections/4ijn-s7e5)
* **Dataset Identifier:** `4ijn-s7e5`
* **Department:** Chicago Department of Public Health (CDPH)
* **Record Scope:** **315,963** inspections across commercial food establishments (restaurants, grocery stores, school cafeterias, daycares, bakeries, mobile food trucks) conducted from **January 1, 2010 to September 23, 2026**.
* **Raw Schema:** 17 columns (~330.8 MB raw CSV file).
* **Business Purpose:** CDPH sanitarians inspect facilities to enforce Chicago Municipal Code Title 7, Chapter 42. Inspection outcomes directly dictate business licensing, pass/fail status, and public safety enforcement.

---

## 🔬 4. Why the Dataset Is Messy: Data-Quality Challenges

An initial programmatic profiling audit ([`reports/data_quality_before.csv`](reports/data_quality_before.csv)) revealed **100,409 missing cells (1.87%)** and widespread data debt:

1. **The "Clean Inspection" Null Trap (`Violations`):** 89,080 records (28.19%) had null violation fields. In this domain, a null violation does *not* indicate missing information; it means the facility passed inspection with **zero violations cited**. Deleting null rows would bias models by eliminating the best-performing businesses.
2. **Missing Brand Names (`AKA Name`):** 2,424 records lacked an "Also Known As" trade name despite having a legal "Doing Business As" (`DBA Name`).
3. **Category Proliferation (`Facility Type`):** 527 raw facility types existed due to inconsistent pluralization, punctuation, and capitalization (e.g., `RESTAURANT`, `restaurant`, `RESTAURANT/BAR`, `DINER`, `CAFE`).
4. **Geographic Inconsistencies (`City`, `Zip`, Coordinates):**
   * Over 80 typo variants of Chicago (`CCHICAGO`, `CHICAGOO`, `312 CHICAGO`).
   * ZIP codes stored as floats (`60601.0`) causing loss of string integrity.
   * 1,051 records lacking geocodes, plus sensor-error coordinates outside the state of Illinois.
5. **Non-Standard Risk Categories:** 83 historical records assigned a non-standard `'All'` risk tier instead of the official Chicago 3-tier risk system.
6. **Whitespace Padding:** Over 246,705 address strings contained trailing, leading, or multiple internal whitespaces.

---

## 🏗️ 5. Project Architecture & Workflow

The pipeline executes a deterministic, single-direction workflow orchestrated by [`src/pipeline.py`](src/pipeline.py):

```text
┌────────────────┐
│    RAW DATA    │  Chicago Open Data Portal (315,963 rows, 17 cols, ~330 MB)
└───────┬────────┘
        │
        ▼
┌────────────────┐
│   INGESTION    │  Verify local checksum, stream download on demand, validate schema
└───────┬────────┘
        │
        ▼
┌────────────────┐
│   PROFILING    │  Automated pre-cleaning quality audit (reports/data_quality_before.csv)
└───────┬────────┘
        │
        ▼
┌────────────────┐
│    CLEANING    │  Normalize casing, regex city/ZIP, facility clustering, date parsing
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ANOMALY DETECT. │  IQR fences, Haversine spatial radius (>25 km), temporal scheduling
└───────┬────────┘
        │
        ▼
┌────────────────┐
│   VALIDATION   │  Automated quality gate (9 business rules); halts on critical failures
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ PROCESSED DATA │  Validated dataset export (data/processed/food_inspections_cleaned.csv)
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ QUALITY REPORT │  Programmatic Before vs After Scorecard (reports/data_quality_comparison.csv)
└────────────────┘
```

---

## 🗂️ 6. Repository Structure

```text
chicago-food-inspections-data-quality-pipeline/
│
├── README.md                      # Comprehensive project documentation & portfolio guide
├── LICENSE                        # MIT Open Source License
├── .gitignore                     # Git rules (raw data, logs, bytecode & venvs excluded)
├── requirements.txt               # Pinned production Python dependencies
├── Makefile                       # Automation commands (pipeline, test, verify, clean)
├── pytest.ini                     # Pytest configuration & path resolution
├── verify_setup.py                # Environment verification & data check script
│
├── config/
│   └── config.yaml                # Centralized pipeline configuration, paths, and URLs
│
├── data/
│   ├── raw/                       # Immutable original dataset (git-ignored)
│   ├── interim/                   # Intermediate standardized dataset (git-ignored)
│   └── processed/                 # Validated, analysis-ready clean dataset (git-ignored)
│
├── src/                           # Modular production source code
│   ├── __init__.py
│   ├── ingestion.py               # Data retrieval, checksum verification & stream ingestion
│   ├── profiling.py               # Pre-cleaning baseline profiling & diagnostic auditor
│   ├── cleaning.py                # Core data cleaning, normalization & feature engineering
│   ├── validation.py              # Automated data validation suite & quality gating
│   ├── anomaly_detection.py       # Statistical outlier & anomaly detection engine
│   ├── quality_report.py          # Programmatic before/after quality comparison generator
│   └── pipeline.py                # Master orchestrator integrating end-to-end workflow
│
├── tests/                         # Ultra-fast automated test suite (46 passing tests in <0.6s)
│   ├── test_cleaning.py           # Unit tests for cleaning transformations (9 tests)
│   ├── test_validation.py         # Unit tests for validation rules & gates (23 tests)
│   ├── test_anomalies.py          # Unit tests for anomaly & outlier detection (7 tests)
│   ├── test_pipeline.py           # Unit tests for master pipeline & loggers (5 tests)
│   └── test_profiling.py          # Unit tests for baseline profiling (2 tests)
│
├── reports/
│   ├── figures/                   # Visual exploratory charts & distribution plots
│   ├── data_quality_before.csv    # Automated Day 2 baseline audit report
│   ├── data_quality_after.csv     # Automated Day 5 post-cleaning audit report
│   ├── data_quality_comparison.csv# Automated Day 6/7 before vs after comparison scorecard
│   ├── validation_report.csv      # Automated Day 4/5 validation scorecard
│   └── anomaly_report.csv         # Automated Day 4/5 anomaly registry
│
└── notebooks/
    └── 01_exploration.ipynb       # Exploratory Data Analysis & visual quality audits
```

---

## 🧼 7. Cleaning Methodology ([`src/cleaning.py`](src/cleaning.py))

All transformations adhere to the core principle: **Never destroy valid historical data**.

1. **Zero Blind Deletions:** All 315,963 rows are preserved.
2. **Surrogate Key Deduplication:** Deduplicates exact duplicate inspection records on `inspection_id`, preserving the initial verified record.
3. **Domain-Specific Imputations:**
   * `aka_name`: 2,424 missing values populated with legal `dba_name`.
   * `violations`: 89,080 missing values imputed with `"NO VIOLATIONS CITED"`.
   * `facility_type`: 5,347 missing entries imputed with `"UNKNOWN"`.
   * `risk`: 87 missing entries imputed with `"NOT SPECIFIED"`.
   * `state` & `city`: Defaulted to `"IL"` and `"CHICAGO"` where location confirms municipal jurisdiction.
4. **Text & Whitespace Standardization:**
   * Stripped leading and trailing whitespace across all text columns.
   * Collapsed internal multi-spaces (`"TACO    BELL"` $\to$ `"TACO BELL"`).
   * Enforced uppercase formatting across business names, addresses, and facility types.
5. **Geographic & Regular Expression Normalization:**
   * Unified 80+ city variations to `"CHICAGO"` via regex pattern matching (`^(?:312\s*)?(?:C+[HCI]*A+G+O+)+[C.\sIO]*$`) while preserving distinct municipalities (`CHICAGO HEIGHTS`, `EVANSTON`).
   * Standardized float ZIP codes (`60601.0`) into 5-digit zero-padded strings (`"60601"`).
   * Validated coordinates against Chicago bounding box (`[41.60, 42.10]`, `[-87.95, -87.50]`); clipped out-of-bounds coordinates to controlled `NaN`s.
6. **Categorical Consolidation:**
   * Reduced `Facility Type` cardinality from **527 raw categories** to **293 clean categories** (-44.4%) using regex keyword clustering (grouping variations of restaurants, grocery stores, daycares, schools, and bakeries).
   * Standardized non-standard `'All'` risk records to `'Risk 1 (High)'` per CDPH standards.
7. **Datatypes & Temporal Feature Engineering:**
   * Converted `Inspection Date` from raw `object` string to native `datetime64[us]`.
   * Engineered 3 temporal features: `inspection_year`, `inspection_month`, and `inspection_day_of_week`.

---

## 🛡️ 8. Validation Methodology ([`src/validation.py`](src/validation.py))

The validation layer acts as a production **quality gate**. The pipeline executes 9 automated integrity checks and halts execution if any `CRITICAL` check fails:

| Check ID | Category | Severity | Rule Description | Status |
| :--- | :--- | :---: | :--- | :---: |
| **VAL-001** | Schema | CRITICAL | All 16 canonical schema columns must be present. | **PASS** |
| **VAL-002** | Integrity | CRITICAL | `inspection_id` must be 100% unique, non-null, and positive. | **PASS** |
| **VAL-003** | Completeness | WARNING | Mandatory operational fields must not contain blank strings (`'   '`). Flagged 3 source errors. | **WARNING** |
| **VAL-004** | Temporal | CRITICAL | Dates must be parseable and fall within operational range (2010 to present). | **PASS** |
| **VAL-005** | Geospatial | WARNING | Non-null coordinates must fall within Chicago bounding box. Flagged 1,051 missing coords. | **WARNING** |
| **VAL-006** | Geospatial | WARNING | ZIP codes must be 5-digit strings. Flagged 2,334 suburban non-606xx ZIPs. | **WARNING** |
| **VAL-007** | Categorical | CRITICAL | Results must strictly match the official 7 Chicago outcome types. | **PASS** |
| **VAL-008** | Categorical | CRITICAL | Risk tiers must conform to official Risk 1, Risk 2, Risk 3, or NOT SPECIFIED. | **PASS** |
| **VAL-009** | Business Logic | WARNING | Inspections resulting in `FAIL` should document violation citations. Flagged 3,648 administrative closures. | **WARNING** |

**Scorecard Result:** **5 PASS | 4 WARNING | 0 FAIL**. Non-critical warnings are monitored in [`reports/validation_report.csv`](reports/validation_report.csv) without blocking clean data generation.

---

## 📈 9. Anomaly Detection Methodology ([`src/anomaly_detection.py`](src/anomaly_detection.py))

A key principle of professional data engineering is: **Statistical outliers are not always errors.** Blindly deleting them removes critical real-world signal.

| Anomaly ID | Anomaly Metric | Detection Method | Classification | Action Policy & Domain Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **ANO-001** | Facility Inspection Frequency | Interquartile Range (IQR Upper Fence: 21 visits) & 99th Pct | Statistical Outlier | **RETAIN:** High-frequency licenses (up to 198 visits) represent long-lived airport terminals (O'Hare) and stadiums. Deleting them removes Chicago's largest food venues. |
| **ANO-002** | Citation Spikes per Inspection | IQR Upper Fence (12.5 citations) | Critical Hazard Signal | **RETAIN:** Inspections with 15–40 citations represent critical sanitation emergencies. These provide the strongest training signal for risk classification models. |
| **ANO-003** | Spatial Distance from City Hall (> 25 km) | Haversine Distance Calculation | Legitimate Unusual Observation | **RETAIN:** Facilities > 25 km away correspond to O'Hare International Airport (~25.4 km NW) and far southern neighborhoods (Hegewisch). |
| **ANO-004** | Weekend Inspection Scheduling | Calendar Day-of-Week Profiling (136 records) | Legitimate Event | **RETAIN:** Saturday/Sunday inspections represent special summer food festivals (Taste of Chicago) and emergency foodborne illness complaint follow-ups. |
| **ANO-005** | Blank Address Strings (`'   '`) | Whitespace Strip & Length Check (3 records) | Data-Entry Error | **IMPUTE:** Source clerical error; repair with `'ADDRESS UNKNOWN'` to maintain record integrity. |
| **ANO-006** | Suburban Non-606xx ZIP Codes | Regex Prefix Matching (`^606`) | Legitimate Overlap | **RETAIN:** Valid municipal border-overlap establishments inspected by CDPH. |

---

## 📊 10. Programmatic Before vs. After Data Quality Scorecard

Every figure in this table is computed programmatically via [`src/quality_report.py`](src/quality_report.py) by directly reading `data/raw/food_inspections_raw.csv` and `data/processed/food_inspections_cleaned.csv`:

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

## 🛠️ 11. Technologies Used

* **Language:** Python 3.10+ (tested on Python 3.14)
* **Data Processing & Transformation:** `pandas`, `numpy`
* **Configuration & File I/O:** `PyYAML`, `requests`, `pathlib`
* **Testing & Quality Assurance:** `pytest` (46 unit tests)
* **Automation:** `Makefile`
* **Exploratory Data Analysis:** `JupyterLab`, `matplotlib`, `seaborn`
* **Version Control:** Git & GitHub

---

## 🚀 12. Quickstart & Installation Instructions

### Step 1: Clone the repository
```bash
git clone https://github.com/samoltylundy226/Data-Cleaning-Project.git
cd Data-Cleaning-Project
```

### Step 2: Set up a virtual environment
```powershell
# Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install production dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Verify environment and data
```bash
python verify_setup.py
# or using Make:
make verify
```

---

## 💻 13. Usage & Execution Instructions

### Run the Master End-to-End Pipeline
Executes ingestion, profiling, cleaning, anomaly detection, validation gating, dataset export, and quality metrics reporting in one command:
```bash
python -m src.pipeline
# or using Make:
make pipeline
```
* **Execution Time:** ~52 seconds.
* **Output Data:** `data/processed/food_inspections_cleaned.csv` (336.90 MB).
* **Execution Log:** `pipeline.log`.

### Generate Before vs. After Quality Scorecard
```bash
python -m src.quality_report
# or using Make:
make report
```
* **Generated Report:** [`reports/data_quality_comparison.csv`](reports/data_quality_comparison.csv).

### Execute Modular Stages Independently
```bash
python -m src.ingestion           # Ingest raw dataset
python -m src.profiling           # Baseline data profiling
python -m src.cleaning            # Core data cleaning engine
python -m src.anomaly_detection   # Statistical outlier profiling
python -m src.validation          # Validation checks & quality gate
```

---

## 🧪 14. Testing Instructions

The test suite runs 46 isolated unit tests against synthetic micro-datasets without requiring the 330 MB raw data file:

```bash
python -m pytest -v
# or using Make:
make test
```

Expected output:
```text
============================= 46 passed in 0.58s ==============================
```

---

## 🔁 15. Reproducibility Guarantee

1. **Centralized Configuration:** Paths, URLs, and boundary limits are externalized in [`config/config.yaml`](config/config.yaml).
2. **Immutable Raw Data:** Raw input data is stored in `data/raw/` in read-only mode and is never mutated by cleaning functions.
3. **Deterministic Transformations:** All cleaning logic uses explicit mappings, regex rules, and fixed seed boundaries.
4. **Automated Validation Gate:** If any canonical schema column is missing or an invalid date is detected, the pipeline immediately halts with a descriptive error message.

---

## 💡 16. Lessons Learned

1. **Domain Knowledge Trumps Generic Imputation:** Applying generic median/mode imputations or `dropna()` would have deleted 28% of clean food inspections. Understanding that "null violations" means "zero health hazards" was essential to preserving data integrity.
2. **Outliers Are Often Critical Signal:** Facilities with 25+ citations or 100+ lifetime visits were statistical outliers, but in municipal health they represent O'Hare airport terminals or severe sanitation hazards. Deleting them would have destroyed the primary training signal for risk forecasting models.
3. **Test with Fast Synthetic Fixtures:** Decoupling unit tests from the 330 MB raw CSV allowed 46 tests to run in under 600 milliseconds, enabling rapid CI/CD cycles and immediate regression feedback.

---

## 🔮 17. Future Improvements (Version 2 Roadmap)

1. **Automated Geocoding API Fallback:** Integrate an asynchronous OpenStreetMap (Nominatim) or Census geocoding fallback to populate coordinates for the 1,051 records currently lacking geocodes.
2. **NLP Free-Text Violation Parsing:** Extract individual violation codes (e.g., Code 38: Rodents/Insects) and sanitarian comments into a separate one-to-many normalized relational table for text mining.
3. **Parquet & DuckDB Integration:** Add automated export to Apache Parquet with Snappy compression to reduce storage footprint from 336 MB to ~45 MB and enable sub-second OLAP querying with DuckDB.
4. **GitHub Actions CI/CD Pipeline:** Add automated GitHub Actions workflows to run `pytest` and linter checks on every pull request.

---

## 📅 7-Day Project Development History

- [x] **Day 1: Project Architecture, Environment Setup & Data Ingestion**
- [x] **Day 2: Exploratory Data Analysis & Baseline Data Quality Profiling**
- [x] **Day 3: Core Data Cleaning & Standardization Engine**
- [x] **Day 4: Automated Data Validation & Anomaly Detection Layer**
- [x] **Day 5: Master Pipeline Orchestration & End-to-End Automation**
- [x] **Day 6: Automated Testing Suite (pytest) & Quality Verification**
- [x] **Day 7: Production Packaging, Comprehensive Documentation & Portfolio Release**

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
