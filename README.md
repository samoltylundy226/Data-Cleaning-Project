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
* **Volume:** ~270,000+ inspection records (2010 to Present) across 17 raw features.
* **Core Challenges Addressed:**
  * Free-text violation log parsing (extracting violation codes, descriptions, and inspector comments).
  * High-cardinality categorical standardization (`Facility Type` standardization and risk classification).
  * Address parsing and geographic anomaly resolution (ZIP code, street standardization, coordinate validation).
  * Strict schema enforcement and automated data quality checks.

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
│   └── __init__.py
│
├── tests/                    # Automated unit and quality tests
│
├── reports/
│   └── figures/              # Generated quality audit charts and summaries
│
└── notebooks/
    └── 01_exploration.ipynb  # Exploratory Data Analysis & quality audits
```

---

## 🚀 Quickstart Guide

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/chicago-food-inspections-data-quality-pipeline.git
cd chicago-food-inspections-data-quality-pipeline
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

### 4. Verify data ingestion and loading
```bash
python verify_setup.py
```

---

## 📅 7-Day Project Roadmap

- [x] **Day 1: Project Setup, Architecture & Data Verification**
- [ ] **Day 2: Exploratory Data Analysis & Data Quality Profiling**
- [ ] **Day 3: Text Parsing & Violation Extraction Engine**
- [ ] **Day 4: Categorical & Geographic Standardization**
- [ ] **Day 5: Missing Data, Outliers & Anomaly Detection**
- [ ] **Day 6: Automated Data Validation & Test Suite**
- [ ] **Day 7: Pipeline Orchestration, Documentation & Portfolio Showcase**
