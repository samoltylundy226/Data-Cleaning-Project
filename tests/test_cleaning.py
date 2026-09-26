"""
Unit tests for data cleaning & standardization module (Day 3).
"""

import numpy as np
import pandas as pd
from src.cleaning import (
    standardize_column_names,
    clean_whitespace_and_casing,
    handle_missing_values,
    standardize_geographic_fields,
    standardize_categories,
    clean_dates_and_datatypes,
    clean_food_inspections,
)


def test_standardize_column_names():
    df = pd.DataFrame(columns=["Inspection ID", "DBA Name", "License #", "Facility Type"])
    cleaned = standardize_column_names(df)
    assert list(cleaned.columns) == ["inspection_id", "dba_name", "license_num", "facility_type"]


def test_clean_whitespace_and_casing():
    df = pd.DataFrame({
        "dba_name": ["  Taco   Bell  ", "subway"],
        "address": ["123   N  MICHIGAN AVE  ", "456 s state st"],
    })
    cleaned = clean_whitespace_and_casing(df)
    assert cleaned["dba_name"].iloc[0] == "TACO BELL"
    assert cleaned["dba_name"].iloc[1] == "SUBWAY"
    assert cleaned["address"].iloc[0] == "123 N MICHIGAN AVE"
    assert cleaned["address"].iloc[1] == "456 S STATE ST"


def test_handle_missing_values():
    df = pd.DataFrame({
        "dba_name": ["Corner Bakery", "Giordano's"],
        "aka_name": [None, "Giordano's Pizzeria"],
        "facility_type": [None, "Restaurant"],
        "violations": [None, "1. VIOLATION"],
        "risk": [None, "Risk 1 (High)"],
    })
    cleaned = handle_missing_values(df)
    assert cleaned["aka_name"].iloc[0] == "Corner Bakery"  # Fallback to dba_name
    assert cleaned["aka_name"].iloc[1] == "Giordano's Pizzeria"
    assert cleaned["facility_type"].iloc[0] == "UNKNOWN"
    assert cleaned["violations"].iloc[0] == "NO VIOLATIONS CITED"
    assert cleaned["risk"].iloc[0] == "NOT SPECIFIED"


def test_standardize_geographic_fields():
    df = pd.DataFrame({
        "city": ["CCHICAGO", "CHICAGOCHICAGO", "CHICAGOO", "CHICAGO HEIGHTS", "EVANSTON", None],
        "zip": [60601.0, "60615.0", 60620, "invalid", None, 60611],
        "latitude": [41.88, 0.0, 41.90, 55.00, np.nan, 41.89],
        "longitude": [-87.62, 0.0, -87.65, -120.0, np.nan, -87.63],
    })
    cleaned = standardize_geographic_fields(df)

    # City normalization
    assert cleaned["city"].iloc[0] == "CHICAGO"
    assert cleaned["city"].iloc[1] == "CHICAGO"
    assert cleaned["city"].iloc[2] == "CHICAGO"
    assert cleaned["city"].iloc[3] == "CHICAGO HEIGHTS"  # Preserved distinct city
    assert cleaned["city"].iloc[4] == "EVANSTON"         # Preserved distinct suburb
    assert cleaned["city"].iloc[5] == "CHICAGO"          # Default for missing

    # ZIP formatting
    assert cleaned["zip"].iloc[0] == "60601"
    assert cleaned["zip"].iloc[1] == "60615"
    assert cleaned["zip"].iloc[2] == "60620"
    assert pd.isna(cleaned["zip"].iloc[3])
    assert pd.isna(cleaned["zip"].iloc[4])

    # Out of bounds coordinates nulled
    assert pd.isna(cleaned["latitude"].iloc[1])   # 0.0 out of bounds
    assert pd.isna(cleaned["latitude"].iloc[3])   # 55.0 out of bounds
    assert cleaned["latitude"].iloc[0] == 41.88  # Valid preserved


def test_clean_dates_and_datatypes():
    df = pd.DataFrame({
        "inspection_id": ["12345", 67890],
        "inspection_date": ["04/18/2023", "01/05/2010"],
        "license_num": [1234.0, None],
    })
    cleaned = clean_dates_and_datatypes(df)
    assert pd.api.types.is_datetime64_any_dtype(cleaned["inspection_date"])
    assert cleaned["inspection_year"].iloc[0] == 2023
    assert cleaned["inspection_month"].iloc[0] == 4
    assert cleaned["inspection_day_of_week"].iloc[0] == "Tuesday"
    assert cleaned["inspection_id"].iloc[0] == 12345
    assert cleaned["license_num"].iloc[0] == "1234"
    assert cleaned["license_num"].iloc[1] == "0"


def test_standardize_categories():
    df = pd.DataFrame({
        "facility_type": ["RESTAURANT/BAR", "GROCERY/DELI", "PUBLIC SCHOOL", "DAYCARE (2-6)", "SPECIAL EVENT"],
        "risk": ["RISK 1 (HIGH)", "All", "Risk 2 (Medium)", "Risk 3 (Low)", None],
    })
    cleaned = standardize_categories(df)
    assert cleaned["facility_type"].iloc[0] == "RESTAURANT"
    assert cleaned["facility_type"].iloc[1] == "GROCERY STORE"
    assert cleaned["facility_type"].iloc[2] == "SCHOOL"
    assert cleaned["facility_type"].iloc[3] == "DAYCARE"
    assert cleaned["facility_type"].iloc[4] == "SPECIAL EVENT"  # Retained

    assert cleaned["risk"].iloc[0] == "Risk 1 (High)"
    assert cleaned["risk"].iloc[1] == "Risk 1 (High)"  # 'All' mapped to High
    assert cleaned["risk"].iloc[2] == "Risk 2 (Medium)"
    assert cleaned["risk"].iloc[3] == "Risk 3 (Low)"
    assert cleaned["risk"].iloc[4] == "NOT SPECIFIED"
