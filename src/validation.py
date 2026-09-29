"""
Data Validation & Schema Integrity Module
==========================================
Chicago Food Inspections Data Cleaning Pipeline

This module executes automated data quality checks, schema enforcement,
and business-rule validations, returning PASS, FAIL, or WARNING statuses.
"""

import os
import re
import sys
import yaml
import numpy as np
import pandas as pd
from datetime import datetime

# Official discrete domain sets
OFFICIAL_RESULTS = {
    "PASS", "FAIL", "PASS W/ CONDITIONS", "OUT OF BUSINESS",
    "NO ENTRY", "NOT READY", "BUSINESS NOT LOCATED"
}

OFFICIAL_RISKS = {
    "Risk 1 (High)", "Risk 2 (Medium)", "Risk 3 (Low)", "NOT SPECIFIED"
}

# Chicago spatial boundaries
CHICAGO_LAT_MIN, CHICAGO_LAT_MAX = 41.60, 42.10
CHICAGO_LON_MIN, CHICAGO_LON_MAX = -87.95, -87.50

# Temporal limits
EARLIEST_VALID_DATE = pd.Timestamp("2010-01-01")
LATEST_VALID_DATE = pd.Timestamp(datetime.now().strftime("%Y-%m-%d"))


def validate_schema(df: pd.DataFrame) -> dict:
    """Verifies that all required canonical columns are present."""
    required_columns = [
        "inspection_id", "dba_name", "aka_name", "license_num",
        "facility_type", "risk", "address", "city", "state", "zip",
        "inspection_date", "inspection_type", "results", "violations",
        "latitude", "longitude"
    ]
    missing_cols = [c for c in required_columns if c not in df.columns]
    status = "FAIL" if missing_cols else "PASS"
    return {
        "check_id": "VAL-001",
        "category": "Schema",
        "rule_description": "Presence of required canonical columns",
        "severity": "CRITICAL",
        "status": status,
        "failing_records_count": len(missing_cols),
        "failing_records_pct": 0.0 if not missing_cols else 100.0,
        "details": f"Missing columns: {missing_cols}" if missing_cols else "All 16 required columns present.",
        "suggested_action": "Ensure pipeline cleaning stage generates all canonical schema features." if missing_cols else "None."
    }


def validate_primary_key(df: pd.DataFrame) -> dict:
    """Validates that inspection_id is positive, non-null, and 100% unique."""
    if "inspection_id" not in df.columns:
        return {"check_id": "VAL-002", "status": "FAIL", "details": "inspection_id column missing."}

    series = df["inspection_id"]
    nulls = int(series.isnull().sum())
    non_positive = int((series <= 0).sum())
    duplicates = int(series.duplicated().sum())

    failing = nulls + non_positive + duplicates
    pct = round((failing / len(df)) * 100, 4)
    status = "FAIL" if failing > 0 else "PASS"

    details = []
    if nulls > 0: details.append(f"{nulls} nulls")
    if non_positive > 0: details.append(f"{non_positive} non-positive")
    if duplicates > 0: details.append(f"{duplicates} duplicate keys")

    return {
        "check_id": "VAL-002",
        "category": "Integrity",
        "rule_description": "Primary key (inspection_id) uniqueness and validity",
        "severity": "CRITICAL",
        "status": status,
        "failing_records_count": failing,
        "failing_records_pct": pct,
        "details": "; ".join(details) if details else "inspection_id is unique, non-null, and positive.",
        "suggested_action": "Drop or deduplicate corrupted primary keys." if failing else "None."
    }


def validate_critical_nulls(df: pd.DataFrame) -> dict:
    """Verifies that mandatory operational columns contain no null or blank values."""
    critical_columns = ["inspection_id", "dba_name", "address", "city", "state", "inspection_date", "results"]
    blank_counts = {}
    total_failing = 0

    for col in critical_columns:
        if col in df.columns:
            s = df[col]
            blanks = int(s.isnull().sum() + (s.astype(str).str.strip() == "").sum())
            if blanks > 0:
                blank_counts[col] = blanks
                total_failing += blanks

    status = "WARNING" if total_failing > 0 else "PASS"
    pct = round((total_failing / len(df)) * 100, 4)

    return {
        "check_id": "VAL-003",
        "category": "Completeness",
        "rule_description": "Mandatory operational fields must not be null or blank",
        "severity": "CRITICAL",
        "status": status,
        "failing_records_count": total_failing,
        "failing_records_pct": pct,
        "details": f"Blank entries detected: {blank_counts}" if blank_counts else "Zero blank values in critical columns.",
        "suggested_action": "Impute or flag blank addresses/names before analytics." if total_failing else "None."
    }


def validate_dates(df: pd.DataFrame) -> dict:
    """Checks for unparseable dates, future dates, or dates prior to 2010."""
    if "inspection_date" not in df.columns:
        return {"check_id": "VAL-004", "status": "FAIL", "details": "inspection_date missing."}

    dates = pd.to_datetime(df["inspection_date"], errors="coerce")
    null_dates = int(dates.isnull().sum())
    future_dates = int((dates > LATEST_VALID_DATE).sum())
    ancient_dates = int((dates < EARLIEST_VALID_DATE).sum())

    failing = null_dates + future_dates + ancient_dates
    pct = round((failing / len(df)) * 100, 4)
    status = "FAIL" if (null_dates + future_dates) > 0 else ("WARNING" if ancient_dates > 0 else "PASS")

    details = []
    if null_dates > 0: details.append(f"{null_dates} unparseable/null")
    if future_dates > 0: details.append(f"{future_dates} future dates")
    if ancient_dates > 0: details.append(f"{ancient_dates} pre-2010 dates")

    return {
        "check_id": "VAL-004",
        "category": "Temporal",
        "rule_description": "Inspection dates must be valid, within 2010 to present",
        "severity": "CRITICAL",
        "status": status,
        "failing_records_count": failing,
        "failing_records_pct": pct,
        "details": "; ".join(details) if details else f"Dates span {dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')} with zero violations.",
        "suggested_action": "Clamp future dates or investigate source system clock drift." if failing else "None."
    }


def validate_geographic_coordinates(df: pd.DataFrame) -> dict:
    """Validates that non-null coordinates fall within the Chicago bounding box."""
    if "latitude" not in df.columns or "longitude" not in df.columns:
        return {"check_id": "VAL-005", "status": "FAIL", "details": "Coordinates missing."}

    lat = df["latitude"]
    lon = df["longitude"]

    # Coordinates outside Chicago bounds (excluding nulls)
    out_of_bounds = int((
        (lat.notnull() & ((lat < CHICAGO_LAT_MIN) | (lat > CHICAGO_LAT_MAX))) |
        (lon.notnull() & ((lon < CHICAGO_LON_MIN) | (lon > CHICAGO_LON_MAX)))
    ).sum())

    null_coords = int(lat.isnull().sum())
    status = "FAIL" if out_of_bounds > 0 else ("WARNING" if null_coords > 0 else "PASS")
    pct = round((out_of_bounds / len(df)) * 100, 4)

    return {
        "check_id": "VAL-005",
        "category": "Geospatial",
        "rule_description": "Coordinates must fall within Chicago bounding box [41.6-42.1, -87.95--87.50]",
        "severity": "WARNING",
        "status": status,
        "failing_records_count": out_of_bounds,
        "failing_records_pct": pct,
        "details": f"{out_of_bounds} coordinates out of bounds; {null_coords:,} coordinates missing/null." if (out_of_bounds or null_coords) else "All non-null coordinates within bounds.",
        "suggested_action": "Geocode missing or out-of-bounds coordinates from Address." if (out_of_bounds or null_coords) else "None."
    }


def validate_zip_codes(df: pd.DataFrame) -> dict:
    """Validates ZIP code structure (5-digit numeric string) and regional consistency."""
    if "zip" not in df.columns:
        return {"check_id": "VAL-006", "status": "FAIL", "details": "zip column missing."}

    zips = df["zip"].dropna().astype(str).str.strip()
    malformed_zips = int((~zips.str.match(r"^\d{5}$")).sum())
    non_chicago_zips = int((~zips.str.startswith("606")).sum())

    status = "FAIL" if malformed_zips > 0 else ("WARNING" if non_chicago_zips > 0 else "PASS")
    pct = round((malformed_zips / len(df)) * 100, 4)

    return {
        "check_id": "VAL-006",
        "category": "Geospatial",
        "rule_description": "ZIP codes must be 5-digit strings matching Illinois/Chicago patterns",
        "severity": "WARNING",
        "status": status,
        "failing_records_count": malformed_zips,
        "failing_records_pct": pct,
        "details": f"{malformed_zips} malformed ZIP strings; {non_chicago_zips:,} suburban/regional non-606xx ZIPs.",
        "suggested_action": "Standardize non-standard ZIPs and cross-reference with municipal boundaries." if malformed_zips else "None."
    }


def validate_results_categories(df: pd.DataFrame) -> dict:
    """Validates that all inspection outcomes belong to official Chicago result categories."""
    if "results" not in df.columns:
        return {"check_id": "VAL-007", "status": "FAIL", "details": "results column missing."}

    results = df["results"].dropna().astype(str).str.upper().str.strip()
    invalid_results = int((~results.isin(OFFICIAL_RESULTS)).sum())
    status = "FAIL" if invalid_results > 0 else "PASS"
    pct = round((invalid_results / len(df)) * 100, 4)

    return {
        "check_id": "VAL-007",
        "category": "Categorical",
        "rule_description": "Results must strictly belong to official 7 Chicago outcome types",
        "severity": "CRITICAL",
        "status": status,
        "failing_records_count": invalid_results,
        "failing_records_pct": pct,
        "details": f"{invalid_results} unexpected result categories detected." if invalid_results else f"100% compliant with official categories: {sorted(list(OFFICIAL_RESULTS))}",
        "suggested_action": "Map unexpected results to closest standard status." if invalid_results else "None."
    }


def validate_risk_categories(df: pd.DataFrame) -> dict:
    """Validates that risk classifications comply with Risk 1, 2, 3 or NOT SPECIFIED."""
    if "risk" not in df.columns:
        return {"check_id": "VAL-008", "status": "FAIL", "details": "risk column missing."}

    risks = df["risk"].dropna().astype(str).str.strip()
    invalid_risks = int((~risks.isin(OFFICIAL_RISKS)).sum())
    status = "FAIL" if invalid_risks > 0 else "PASS"
    pct = round((invalid_risks / len(df)) * 100, 4)

    return {
        "check_id": "VAL-008",
        "category": "Categorical",
        "rule_description": "Risk tiers must conform to official Chicago Risk 1, 2, 3 classifications",
        "severity": "CRITICAL",
        "status": status,
        "failing_records_count": invalid_risks,
        "failing_records_pct": pct,
        "details": f"{invalid_risks} unexpected risk labels detected." if invalid_risks else f"100% compliant with official risk categories: {sorted(list(OFFICIAL_RISKS))}",
        "suggested_action": "Standardize non-standard risk entries." if invalid_risks else "None."
    }


def validate_business_logic(df: pd.DataFrame) -> dict:
    """
    Validates logical consistency between inspection Results and Violations:
    - Flags FAIL inspections with 'NO VIOLATIONS CITED' (suspicious administrative closure).
    """
    if "results" not in df.columns or "violations" not in df.columns:
        return {"check_id": "VAL-009", "status": "FAIL", "details": "Columns missing for business logic check."}

    fail_without_violations = int((
        (df["results"].astype(str).str.upper() == "FAIL") &
        (df["violations"].astype(str).str.upper() == "NO VIOLATIONS CITED")
    ).sum())

    pct = round((fail_without_violations / len(df)) * 100, 4)
    status = "WARNING" if fail_without_violations > 0 else "PASS"

    return {
        "check_id": "VAL-009",
        "category": "Business Logic",
        "rule_description": "Inspections resulting in FAIL should document violation citations",
        "severity": "WARNING",
        "status": status,
        "failing_records_count": fail_without_violations,
        "failing_records_pct": pct,
        "details": f"{fail_without_violations:,} records marked FAIL but cite zero violations (likely administrative/access failures).",
        "suggested_action": "Audit administrative failure codes (e.g. No Entry, Not Ready) recorded under Fail." if fail_without_violations else "None."
    }


def run_all_validations(df: pd.DataFrame) -> pd.DataFrame:
    """Executes the full suite of data quality validation checks and compiles report."""
    checks = [
        validate_schema(df),
        validate_primary_key(df),
        validate_critical_nulls(df),
        validate_dates(df),
        validate_geographic_coordinates(df),
        validate_zip_codes(df),
        validate_results_categories(df),
        validate_risk_categories(df),
        validate_business_logic(df),
    ]
    return pd.DataFrame(checks)


def export_validation_report(report_df: pd.DataFrame, output_path: str = "reports/validation_report.csv"):
    """Exports validation report to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    report_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[OK] Validation report exported to: {output_path}")


def print_validation_summary(report_df: pd.DataFrame):
    """Prints a clean CLI executive scorecard for data validation."""
    print("\n" + "=" * 80)
    print("           DAY 4: DATA VALIDATION & INTEGRITY SCORECARD")
    print("=" * 80)
    passed = (report_df["status"] == "PASS").sum()
    warnings = (report_df["status"] == "WARNING").sum()
    failures = (report_df["status"] == "FAIL").sum()
    print(f"Total Rules Evaluated: {len(report_df)} | PASS: {passed} | WARNING: {warnings} | FAIL: {failures}")
    print("=" * 80)

    display_cols = ["check_id", "category", "status", "severity", "failing_records_count", "rule_description"]
    print(report_df[display_cols].to_string(index=False))
    print("=" * 80)

    print("\nDetailed Findings & Suggested Actions:")
    for _, row in report_df.iterrows():
        icon = "[PASS]" if row["status"] == "PASS" else ("[WARN]" if row["status"] == "WARNING" else "[FAIL]")
        print(f"{icon} {row['check_id']} ({row['status']}): {row['rule_description']}")
        print(f"    Details: {row['details']}")
        if row["suggested_action"] != "None.":
            print(f"    Action:  {row['suggested_action']}")
    print("=" * 80)


def main(data_path: str = "data/interim/food_inspections_interim.csv"):
    """Main CLI execution to validate cleaned interim dataset."""
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    print(f"[+] Loading interim cleaned dataset from: {data_path}...")
    df = pd.read_csv(data_path, dtype={"zip": "string", "license_num": "string"}, low_memory=False)

    report_df = run_all_validations(df)
    export_validation_report(report_df)
    print_validation_summary(report_df)
    return report_df


if __name__ == "__main__":
    main()
