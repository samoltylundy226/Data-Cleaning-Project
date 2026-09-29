"""
Unit tests for data validation module (Day 4).
"""

import pandas as pd
from src.validation import (
    validate_schema,
    validate_primary_key,
    validate_dates,
    validate_geographic_coordinates,
    validate_zip_codes,
    validate_results_categories,
    validate_risk_categories,
    validate_business_logic,
)


def test_validate_schema():
    valid_df = pd.DataFrame(columns=[
        "inspection_id", "dba_name", "aka_name", "license_num",
        "facility_type", "risk", "address", "city", "state", "zip",
        "inspection_date", "inspection_type", "results", "violations",
        "latitude", "longitude"
    ])
    result = validate_schema(valid_df)
    assert result["status"] == "PASS"

    invalid_df = pd.DataFrame(columns=["inspection_id", "dba_name"])
    result_fail = validate_schema(invalid_df)
    assert result_fail["status"] == "FAIL"


def test_validate_primary_key():
    clean_df = pd.DataFrame({"inspection_id": [101, 102, 103]})
    assert validate_primary_key(clean_df)["status"] == "PASS"

    dup_df = pd.DataFrame({"inspection_id": [101, 101, 102]})
    assert validate_primary_key(dup_df)["status"] == "FAIL"

    null_df = pd.DataFrame({"inspection_id": [101, None, 102]})
    assert validate_primary_key(null_df)["status"] == "FAIL"


def test_validate_dates():
    valid_dates_df = pd.DataFrame({"inspection_date": ["2015-05-10", "2023-11-20"]})
    assert validate_dates(valid_dates_df)["status"] == "PASS"

    future_dates_df = pd.DataFrame({"inspection_date": ["2099-01-01"]})
    assert validate_dates(future_dates_df)["status"] == "FAIL"


def test_validate_geographic_coordinates():
    valid_coords_df = pd.DataFrame({
        "latitude": [41.88, 41.90],
        "longitude": [-87.62, -87.65],
    })
    assert validate_geographic_coordinates(valid_coords_df)["status"] == "PASS"

    invalid_coords_df = pd.DataFrame({
        "latitude": [10.0, 41.90],  # Out of bounds
        "longitude": [-87.62, -87.65],
    })
    assert validate_geographic_coordinates(invalid_coords_df)["status"] == "FAIL"


def test_validate_zip_codes():
    valid_zips_df = pd.DataFrame({"zip": ["60601", "60615"]})
    assert validate_zip_codes(valid_zips_df)["status"] == "PASS"

    malformed_zips_df = pd.DataFrame({"zip": ["606", "INVALID"]})
    assert validate_zip_codes(malformed_zips_df)["status"] == "FAIL"


def test_validate_results_categories():
    valid_res_df = pd.DataFrame({"results": ["PASS", "FAIL", "PASS W/ CONDITIONS"]})
    assert validate_results_categories(valid_res_df)["status"] == "PASS"

    invalid_res_df = pd.DataFrame({"results": ["UNKNOWN_STATUS"]})
    assert validate_results_categories(invalid_res_df)["status"] == "FAIL"


def test_validate_business_logic():
    df_clean = pd.DataFrame({
        "results": ["PASS", "FAIL"],
        "violations": ["NO VIOLATIONS CITED", "1. SOURCE VIOLATION"],
    })
    assert validate_business_logic(df_clean)["status"] == "PASS"

    df_warn = pd.DataFrame({
        "results": ["FAIL"],
        "violations": ["NO VIOLATIONS CITED"],
    })
    assert validate_business_logic(df_warn)["status"] == "WARNING"
