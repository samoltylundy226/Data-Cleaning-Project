"""
Unit tests for data validation module.
Day 6 comprehensive test suite for validation and integrity rules.
"""

import pandas as pd
import pytest
from src.validation import (
    validate_schema,
    validate_primary_key,
    validate_critical_nulls,
    validate_dates,
    validate_geographic_coordinates,
    validate_zip_codes,
    validate_results_categories,
    validate_risk_categories,
    validate_business_logic,
    run_all_validations,
)


def test_validate_schema_pass():
    valid_df = pd.DataFrame(columns=[
        "inspection_id", "dba_name", "aka_name", "license_num",
        "facility_type", "risk", "address", "city", "state", "zip",
        "inspection_date", "inspection_type", "results", "violations",
        "latitude", "longitude"
    ])
    result = validate_schema(valid_df)
    assert result["status"] == "PASS"
    assert result["check_id"] == "VAL-001"
    assert result["failing_records_count"] == 0


def test_validate_schema_fail():
    invalid_df = pd.DataFrame(columns=["inspection_id", "dba_name"])
    result = validate_schema(invalid_df)
    assert result["status"] == "FAIL"
    assert result["check_id"] == "VAL-001"
    assert result["failing_records_count"] > 0


def test_validate_primary_key_pass():
    clean_df = pd.DataFrame({"inspection_id": [101, 102, 103]})
    result = validate_primary_key(clean_df)
    assert result["status"] == "PASS"
    assert result["check_id"] == "VAL-002"
    assert result["failing_records_count"] == 0


def test_validate_primary_key_fail_duplicates():
    dup_df = pd.DataFrame({"inspection_id": [101, 101, 102]})
    result = validate_primary_key(dup_df)
    assert result["status"] == "FAIL"
    assert "duplicate keys" in result["details"]


def test_validate_primary_key_fail_nulls():
    null_df = pd.DataFrame({"inspection_id": [101, None, 102]})
    result = validate_primary_key(null_df)
    assert result["status"] == "FAIL"
    assert "nulls" in result["details"]


def test_validate_primary_key_fail_non_positive():
    neg_df = pd.DataFrame({"inspection_id": [101, -5, 0]})
    result = validate_primary_key(neg_df)
    assert result["status"] == "FAIL"
    assert "non-positive" in result["details"]


def test_validate_critical_nulls_pass():
    df_clean = pd.DataFrame({
        "inspection_id": [1],
        "dba_name": ["CAFE"],
        "address": ["123 MAIN"],
        "city": ["CHICAGO"],
        "state": ["IL"],
        "inspection_date": ["2023-01-01"],
        "results": ["PASS"]
    })
    result = validate_critical_nulls(df_clean)
    assert result["status"] == "PASS"
    assert result["failing_records_count"] == 0


def test_validate_critical_nulls_warning():
    df_blank = pd.DataFrame({
        "inspection_id": [1],
        "dba_name": ["CAFE"],
        "address": ["   "],  # Whitespace-only address
        "city": ["CHICAGO"],
        "state": ["IL"],
        "inspection_date": ["2023-01-01"],
        "results": ["PASS"]
    })
    result = validate_critical_nulls(df_blank)
    assert result["status"] == "WARNING"
    assert result["failing_records_count"] == 1


def test_validate_dates_pass():
    valid_dates_df = pd.DataFrame({"inspection_date": ["2015-05-10", "2023-11-20"]})
    result = validate_dates(valid_dates_df)
    assert result["status"] == "PASS"
    assert result["check_id"] == "VAL-004"


def test_validate_dates_fail_future():
    future_dates_df = pd.DataFrame({"inspection_date": ["2099-01-01"]})
    result = validate_dates(future_dates_df)
    assert result["status"] == "FAIL"
    assert "future dates" in result["details"]


def test_validate_dates_fail_unparseable():
    bad_dates_df = pd.DataFrame({"inspection_date": ["NOT_A_DATE"]})
    result = validate_dates(bad_dates_df)
    assert result["status"] == "FAIL"
    assert "unparseable/null" in result["details"]


def test_validate_geographic_coordinates_pass():
    valid_coords_df = pd.DataFrame({
        "latitude": [41.88, 41.90],
        "longitude": [-87.62, -87.65],
    })
    result = validate_geographic_coordinates(valid_coords_df)
    assert result["status"] == "PASS"
    assert result["failing_records_count"] == 0


def test_validate_geographic_coordinates_fail_bounds():
    invalid_coords_df = pd.DataFrame({
        "latitude": [10.0, 41.90],  # 10.0 is outside Chicago
        "longitude": [-87.62, -87.65],
    })
    result = validate_geographic_coordinates(invalid_coords_df)
    assert result["status"] == "FAIL"
    assert result["failing_records_count"] == 1


def test_validate_geographic_coordinates_warning_missing():
    missing_coords_df = pd.DataFrame({
        "latitude": [41.88, None],
        "longitude": [-87.62, None],
    })
    result = validate_geographic_coordinates(missing_coords_df)
    assert result["status"] == "WARNING"
    assert "missing/null" in result["details"]


def test_validate_zip_codes_pass():
    valid_zips_df = pd.DataFrame({"zip": ["60601", "60615", "60620"]})
    result = validate_zip_codes(valid_zips_df)
    assert result["status"] == "PASS"


def test_validate_zip_codes_fail_malformed():
    malformed_zips_df = pd.DataFrame({"zip": ["606", "INVALID", "60601"]})
    result = validate_zip_codes(malformed_zips_df)
    assert result["status"] == "FAIL"
    assert result["failing_records_count"] == 2


def test_validate_zip_codes_warning_suburban():
    suburban_zips_df = pd.DataFrame({"zip": ["60077", "60601"]})
    result = validate_zip_codes(suburban_zips_df)
    assert result["status"] == "WARNING"
    assert "suburban/regional" in result["details"]


def test_validate_results_categories_pass():
    valid_res_df = pd.DataFrame({
        "results": ["PASS", "FAIL", "PASS W/ CONDITIONS", "OUT OF BUSINESS"]
    })
    result = validate_results_categories(valid_res_df)
    assert result["status"] == "PASS"


def test_validate_results_categories_fail():
    invalid_res_df = pd.DataFrame({"results": ["UNKNOWN_STATUS", "PASS"]})
    result = validate_results_categories(invalid_res_df)
    assert result["status"] == "FAIL"
    assert result["failing_records_count"] == 1


def test_validate_risk_categories_pass():
    valid_risk_df = pd.DataFrame({
        "risk": ["Risk 1 (High)", "Risk 2 (Medium)", "Risk 3 (Low)", "NOT SPECIFIED"]
    })
    result = validate_risk_categories(valid_risk_df)
    assert result["status"] == "PASS"


def test_validate_risk_categories_fail():
    invalid_risk_df = pd.DataFrame({"risk": ["Risk 99 (Extreme)"]})
    result = validate_risk_categories(invalid_risk_df)
    assert result["status"] == "FAIL"


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


def test_run_all_validations():
    df = pd.DataFrame({
        "inspection_id": [1, 2],
        "dba_name": ["CAFE A", "CAFE B"],
        "aka_name": ["CAFE A", "CAFE B"],
        "license_num": ["100", "200"],
        "facility_type": ["RESTAURANT", "RESTAURANT"],
        "risk": ["Risk 1 (High)", "Risk 2 (Medium)"],
        "address": ["123 MAIN ST", "456 STATE ST"],
        "city": ["CHICAGO", "CHICAGO"],
        "state": ["IL", "IL"],
        "zip": ["60601", "60602"],
        "inspection_date": ["2023-01-01", "2023-02-01"],
        "inspection_type": ["CANVASS", "CANVASS"],
        "results": ["PASS", "PASS"],
        "violations": ["NO VIOLATIONS CITED", "NO VIOLATIONS CITED"],
        "latitude": [41.88, 41.89],
        "longitude": [-87.62, -87.63]
    })
    scorecard = run_all_validations(df)
    assert len(scorecard) == 9
    assert set(scorecard["status"].unique()).issubset({"PASS", "WARNING"})
