"""
Unit tests for data cleaning & standardization module.
Day 6 comprehensive testing for cleaning transformations.
"""

import numpy as np
import pandas as pd
import pytest
from src.cleaning import (
    standardize_column_names,
    clean_whitespace_and_casing,
    handle_missing_values,
    handle_duplicates,
    standardize_geographic_fields,
    standardize_categories,
    clean_dates_and_datatypes,
    clean_food_inspections,
)


def test_standardize_column_names():
    df = pd.DataFrame(columns=["Inspection ID", "DBA Name", "License #", "Facility Type", "Inspection Date"])
    cleaned = standardize_column_names(df)
    assert list(cleaned.columns) == [
        "inspection_id", "dba_name", "license_num", "facility_type", "inspection_date"
    ]


def test_clean_whitespace_and_casing():
    df = pd.DataFrame({
        "dba_name": ["  Taco   Bell  ", "subway", "  CHIPOTLE  "],
        "address": ["123   N  MICHIGAN AVE  ", "456 s state st", " 789  w madison  st "],
    })
    cleaned = clean_whitespace_and_casing(df)
    assert cleaned["dba_name"].iloc[0] == "TACO BELL"
    assert cleaned["dba_name"].iloc[1] == "SUBWAY"
    assert cleaned["dba_name"].iloc[2] == "CHIPOTLE"
    assert cleaned["address"].iloc[0] == "123 N MICHIGAN AVE"
    assert cleaned["address"].iloc[1] == "456 S STATE ST"
    assert cleaned["address"].iloc[2] == "789 W MADISON ST"


def test_handle_missing_values():
    df = pd.DataFrame({
        "dba_name": ["Corner Bakery", "Giordano's", "Local Cafe"],
        "aka_name": [None, "Giordano's Pizzeria", np.nan],
        "facility_type": [None, "Restaurant", np.nan],
        "violations": [None, "1. VIOLATION", np.nan],
        "risk": [None, "Risk 1 (High)", np.nan],
        "state": [None, "IL", np.nan],
        "city": [None, "CHICAGO", np.nan],
        "license_num": [None, 12345, np.nan],
    })
    cleaned = handle_missing_values(df)

    # AKA name fallback to DBA name
    assert cleaned["aka_name"].iloc[0] == "Corner Bakery"
    assert cleaned["aka_name"].iloc[1] == "Giordano's Pizzeria"
    assert cleaned["aka_name"].iloc[2] == "Local Cafe"

    # Facility type imputation
    assert cleaned["facility_type"].iloc[0] == "UNKNOWN"
    assert cleaned["facility_type"].iloc[1] == "Restaurant"

    # Violations imputation
    assert cleaned["violations"].iloc[0] == "NO VIOLATIONS CITED"
    assert cleaned["violations"].iloc[1] == "1. VIOLATION"

    # Risk imputation
    assert cleaned["risk"].iloc[0] == "NOT SPECIFIED"
    assert cleaned["risk"].iloc[1] == "Risk 1 (High)"

    # State & City imputation
    assert cleaned["state"].iloc[0] == "IL"
    assert cleaned["city"].iloc[0] == "CHICAGO"

    # License imputation
    assert cleaned["license_num"].iloc[0] == 0


def test_handle_duplicates():
    df_with_dupes = pd.DataFrame({
        "inspection_id": [101, 102, 101, 103],
        "dba_name": ["First Record", "Store B", "Duplicate Record", "Store C"],
    })
    cleaned = handle_duplicates(df_with_dupes)
    assert len(cleaned) == 3
    assert list(cleaned["inspection_id"]) == [101, 102, 103]
    assert cleaned["dba_name"].iloc[0] == "First Record"  # First occurrence preserved

    df_clean = pd.DataFrame({
        "inspection_id": [201, 202, 203],
        "dba_name": ["Store X", "Store Y", "Store Z"],
    })
    cleaned_clean = handle_duplicates(df_clean)
    assert len(cleaned_clean) == 3


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

    # ZIP formatting (5-digit zero-padded strings)
    assert cleaned["zip"].iloc[0] == "60601"
    assert cleaned["zip"].iloc[1] == "60615"
    assert cleaned["zip"].iloc[2] == "60620"
    assert pd.isna(cleaned["zip"].iloc[3])
    assert pd.isna(cleaned["zip"].iloc[4])

    # Out of bounds coordinates nulled to NaN
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


def test_clean_dates_coercion_malformed():
    df = pd.DataFrame({
        "inspection_id": [99999],
        "inspection_date": ["INVALID_DATE_STRING"],
        "license_num": ["N/A"],
    })
    cleaned = clean_dates_and_datatypes(df)
    assert pd.isna(cleaned["inspection_date"].iloc[0])
    assert pd.isna(cleaned["inspection_year"].iloc[0])


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
    assert cleaned["facility_type"].iloc[4] == "SPECIAL EVENT"

    assert cleaned["risk"].iloc[0] == "Risk 1 (High)"
    assert cleaned["risk"].iloc[1] == "Risk 1 (High)"  # 'All' mapped to High
    assert cleaned["risk"].iloc[2] == "Risk 2 (Medium)"
    assert cleaned["risk"].iloc[3] == "Risk 3 (Low)"
    assert cleaned["risk"].iloc[4] == "NOT SPECIFIED"


def test_clean_food_inspections_end_to_end():
    raw_df = pd.DataFrame({
        "Inspection ID": [1001, 1002],
        "DBA Name": ["  JOE'S PIZZA  ", "TACO SPOT"],
        "AKA Name": [None, "TACO SPOT #1"],
        "License #": [9999.0, None],
        "Facility Type": ["RESTAURANT/GRILL", None],
        "Risk": ["Risk 1 (High)", "All"],
        "Address": ["100 N STATE ST", "200 S WABASH AVE"],
        "City": ["CCHICAGO", "CHICAGO"],
        "State": ["IL", None],
        "Zip": [60601.0, 60602],
        "Inspection Date": ["05/10/2021", "11/25/2022"],
        "Inspection Type": ["CANVASS", "COMPLAINT"],
        "Results": ["PASS", "FAIL"],
        "Violations": [None, "1. SOURCE VIOLATION | 2. HYGIENE"],
        "Latitude": [41.88, 41.89],
        "Longitude": [-87.62, -87.63],
        "Location": ["(41.88, -87.62)", "(41.89, -87.63)"]
    })

    cleaned_df, audit = clean_food_inspections(raw_df)

    assert len(cleaned_df) == 2
    assert "inspection_year" in cleaned_df.columns
    assert cleaned_df["aka_name"].iloc[0] == "JOE'S PIZZA"
    assert cleaned_df["violations"].iloc[0] == "NO VIOLATIONS CITED"
    assert cleaned_df["risk"].iloc[1] == "Risk 1 (High)"
    assert audit["raw_records"] == 2
    assert audit["cleaned_records"] == 2
    assert audit["missing_aka_names_filled"] == 1
    assert audit["zero_violations_imputed"] == 1
