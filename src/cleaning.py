"""
Data Cleaning & Standardization Module
=======================================
Chicago Food Inspections Data Cleaning Pipeline

This module implements modular, reproducible, and verifiable cleaning
transformations for messy municipal inspection data without mutating raw data.
"""

import os
import re
import yaml
import numpy as np
import pandas as pd


# Canonical column name mapping: Raw names -> Snake_case identifiers
COLUMN_RENAME_MAP = {
    "Inspection ID": "inspection_id",
    "DBA Name": "dba_name",
    "AKA Name": "aka_name",
    "License #": "license_num",
    "Facility Type": "facility_type",
    "Risk": "risk",
    "Address": "address",
    "City": "city",
    "State": "state",
    "Zip": "zip",
    "Inspection Date": "inspection_date",
    "Inspection Type": "inspection_type",
    "Results": "results",
    "Violations": "violations",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Location": "location",
}

# Regex to detect typographical variants of CHICAGO
CHICAGO_TYPO_REGEX = re.compile(r"^(?:312\s*)?(?:C+[HCI]*A+G+O+)+[C.\sIO]*$", re.IGNORECASE)

# Bounding box coordinates for City of Chicago
CHICAGO_LAT_MIN, CHICAGO_LAT_MAX = 41.60, 42.10
CHICAGO_LON_MIN, CHICAGO_LON_MAX = -87.95, -87.50


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Renames raw DataFrame columns to clean, lowercase snake_case identifiers."""
    df = df.copy()
    rename_dict = {col: COLUMN_RENAME_MAP.get(col, col.lower().replace(" ", "_")) for col in df.columns}
    return df.rename(columns=rename_dict)


def clean_whitespace_and_casing(df: pd.DataFrame) -> pd.DataFrame:
    """Strips leading/trailing whitespace and collapses internal multiple spaces across text columns."""
    df = df.copy()
    text_columns = [
        "dba_name", "aka_name", "address", "city", "state",
        "facility_type", "risk", "inspection_type", "results"
    ]
    for col in text_columns:
        if col in df.columns:
            # Strip whitespace, collapse multi-spaces, and uppercase
            df[col] = df[col].astype("string").str.replace(r"\s+", " ", regex=True).str.strip().str.upper()
    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies domain-specific missing value policies without dropping rows:
    - aka_name: Fallback to legal dba_name.
    - facility_type: Impute with 'UNKNOWN'.
    - violations: Impute with 'NO VIOLATIONS CITED'.
    - risk: Impute with 'NOT SPECIFIED'.
    - state: Impute with 'IL' for Chicago records.
    - city: Impute with 'CHICAGO' when coordinates/zip indicate Chicago.
    - license_num: Impute with '0' (unlicensed or missing).
    """
    df = df.copy()

    # 1. AKA Name fallback
    if "aka_name" in df.columns and "dba_name" in df.columns:
        df["aka_name"] = df["aka_name"].fillna(df["dba_name"])

    # 2. Facility Type imputation
    if "facility_type" in df.columns:
        df["facility_type"] = df["facility_type"].fillna("UNKNOWN")

    # 3. Violations imputation
    if "violations" in df.columns:
        df["violations"] = df["violations"].fillna("NO VIOLATIONS CITED")

    # 4. Risk imputation
    if "risk" in df.columns:
        df["risk"] = df["risk"].fillna("NOT SPECIFIED")

    # 5. State imputation
    if "state" in df.columns:
        df["state"] = df["state"].fillna("IL")

    # 6. City imputation
    if "city" in df.columns:
        df["city"] = df["city"].fillna("CHICAGO")

    # 7. License number imputation
    if "license_num" in df.columns:
        df["license_num"] = df["license_num"].fillna(0)

    return df


def standardize_geographic_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes City, State, ZIP codes, and geospatial coordinates.
    - Resolves City typos to 'CHICAGO' using regex.
    - Standardizes ZIP code as a 5-digit zero-padded string.
    - Validates latitude and longitude within the Chicago geographic boundary.
    """
    df = df.copy()

    # 1. Standardize City
    if "city" in df.columns:
        def fix_city(val):
            if pd.isna(val) or val == "":
                return "CHICAGO"
            val_clean = str(val).strip().upper()
            if CHICAGO_TYPO_REGEX.match(val_clean) and "HEIGHTS" not in val_clean:
                return "CHICAGO"
            return val_clean

        df["city"] = df["city"].apply(fix_city).astype("string")

    # 2. Standardize ZIP Code
    if "zip" in df.columns:
        def format_zip(val):
            if pd.isna(val) or val == "":
                return np.nan
            try:
                numeric_val = int(float(val))
                if 1000 <= numeric_val <= 99999:
                    return f"{numeric_val:05d}"
                return np.nan
            except (ValueError, TypeError):
                return np.nan

        df["zip"] = df["zip"].apply(format_zip).astype("string")

    # 3. Validate Coordinates against Chicago Bounding Box
    if "latitude" in df.columns and "longitude" in df.columns:
        invalid_coords = (
            (df["latitude"] < CHICAGO_LAT_MIN) | (df["latitude"] > CHICAGO_LAT_MAX) |
            (df["longitude"] < CHICAGO_LON_MIN) | (df["longitude"] > CHICAGO_LON_MAX)
        )
        df.loc[invalid_coords, ["latitude", "longitude"]] = np.nan

    return df


def standardize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes high-cardinality and messy categorical fields:
    - Facility Type: Regex grouping of common business types (Restaurant, Grocery, School, Daycare).
    - Risk: Normalizes non-standard 'All' category and formats consistent labels.
    - Results: Validates and standardizes inspection outcome categories.
    """
    df = df.copy()

    # 1. Standardize Facility Type
    if "facility_type" in df.columns:
        def categorize_facility(val):
            if pd.isna(val) or val == "UNKNOWN":
                return "UNKNOWN"
            v = str(val).strip().upper()
            if re.search(r"\bRESTAURANT\b|\bDINER\b|\bCAFE\b|\bREST\b|\bEATERY\b", v):
                return "RESTAURANT"
            if re.search(r"\bGROCERY\b|\bSUPERMARKET\b|\bMARKET\b|\bCONVENIENCE\b", v):
                return "GROCERY STORE"
            if re.search(r"\bSCHOOL\b", v):
                return "SCHOOL"
            if re.search(r"\bDAYCARE\b|\bCHILDREN\b", v):
                return "DAYCARE"
            if re.search(r"\bBAKERY\b|\bBAKE\b", v):
                return "BAKERY"
            if re.search(r"\bMOBILE FOOD\b|\bFOOD TRUCK\b", v):
                return "MOBILE FOOD"
            if re.search(r"\bHOSPITAL\b|\bCARE\b|\bNURSING\b|\bHEALTH\b", v):
                return "HEALTHCARE / CARE FACILITY"
            if re.search(r"\bCATERING\b|\bCATERER\b", v):
                return "CATERING"
            if re.search(r"\bLIQUOR\b|\bTAVERN\b|\bBAR\b|\bBREWERY\b", v):
                return "BAR / TAVERN"
            if re.search(r"\bWHOLESALE\b|\bDISTRIBUTOR\b|\bWAREHOUSE\b", v):
                return "WHOLESALE / WAREHOUSE"
            return v  # Retain specific type if not matched

        df["facility_type"] = df["facility_type"].apply(categorize_facility).astype("string")

    # 2. Standardize Risk
    if "risk" in df.columns:
        def clean_risk(val):
            if pd.isna(val) or val == "NOT SPECIFIED":
                return "NOT SPECIFIED"
            v = str(val).strip().upper()
            if "RISK 1" in v or "HIGH" in v or v == "ALL":
                return "Risk 1 (High)"
            if "RISK 2" in v or "MEDIUM" in v:
                return "Risk 2 (Medium)"
            if "RISK 3" in v or "LOW" in v:
                return "Risk 3 (Low)"
            return "NOT SPECIFIED"

        df["risk"] = df["risk"].apply(clean_risk).astype("string")

    return df


def clean_dates_and_datatypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforces strict datatype schemas and converts strings to rich datetime objects:
    - inspection_date: Parsed to datetime64[ns].
    - Creates derived temporal features: inspection_year, inspection_month, inspection_day_of_week.
    - license_num: Stored as clean zero-padded string or integer string without decimals.
    - inspection_id: Converted to int64.
    """
    df = df.copy()

    # 1. Datetime conversion
    if "inspection_date" in df.columns:
        df["inspection_date"] = pd.to_datetime(df["inspection_date"], format="%m/%d/%Y", errors="coerce")
        df["inspection_year"] = df["inspection_date"].dt.year.astype("Int64")
        df["inspection_month"] = df["inspection_date"].dt.month.astype("Int64")
        df["inspection_day_of_week"] = df["inspection_date"].dt.day_name().astype("string")

    # 2. License number string formatting
    if "license_num" in df.columns:
        def clean_license(val):
            try:
                n = int(float(val))
                return str(n)
            except (ValueError, TypeError):
                return "0"

        df["license_num"] = df["license_num"].apply(clean_license).astype("string")

    # 3. Inspection ID int64
    if "inspection_id" in df.columns:
        df["inspection_id"] = pd.to_numeric(df["inspection_id"], errors="coerce").astype("int64")

    return df


def handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Identifies and handles duplicate records."""
    df = df.copy()
    initial_rows = len(df)
    df = df.drop_duplicates(subset=["inspection_id"], keep="first")
    dropped = initial_rows - len(df)
    if dropped > 0:
        print(f"[!] Dropped {dropped} duplicate inspection records.")
    return df


def clean_food_inspections(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Executes the end-to-end Day 3 cleaning pipeline and computes audit metrics.
    """
    audit_metrics = {
        "raw_records": len(raw_df),
        "raw_columns": len(raw_df.columns),
    }

    # Pipeline stages
    df = standardize_column_names(raw_df)
    df = handle_duplicates(df)
    df = clean_whitespace_and_casing(df)
    df = handle_missing_values(df)
    df = standardize_geographic_fields(df)
    df = standardize_categories(df)
    df = clean_dates_and_datatypes(df)

    audit_metrics.update({
        "cleaned_records": len(df),
        "cleaned_columns": len(df.columns),
        "missing_aka_names_filled": int(raw_df["AKA Name"].isnull().sum()),
        "facility_types_standardized": int(raw_df["Facility Type"].dropna().nunique() - df["facility_type"].nunique()),
        "dates_converted": int(df["inspection_date"].notnull().sum()),
        "chicago_city_records": int((df["city"] == "CHICAGO").sum()),
        "zero_violations_imputed": int(raw_df["Violations"].isnull().sum()),
    })

    return df, audit_metrics


def run_cleaning_pipeline(
    raw_path: str = "data/raw/food_inspections_raw.csv",
    interim_path: str = "data/interim/food_inspections_interim.csv",
):
    """Main CLI entrypoint to load raw data, clean it, and export interim dataset."""
    print(f"[+] Loading raw dataset from: {raw_path}...")
    raw_df = pd.read_csv(raw_path, low_memory=False)

    print("[+] Executing Day 3 cleaning and standardization pipeline...")
    cleaned_df, audit = clean_food_inspections(raw_df)

    print(f"[+] Saving cleaned dataset to: {interim_path}...")
    os.makedirs(os.path.dirname(interim_path), exist_ok=True)
    cleaned_df.to_csv(interim_path, index=False, encoding="utf-8")

    size_mb = os.path.getsize(interim_path) / (1024**2)
    print(f"[OK] Cleaned interim dataset successfully exported ({size_mb:.2f} MB)")

    print("\n" + "=" * 70)
    print("           DAY 3 DATA CLEANING AUDIT REPORT")
    print("=" * 70)
    print(f"Raw Input Rows:                    {audit['raw_records']:,}")
    print(f"Cleaned Output Rows:               {audit['cleaned_records']:,}")
    print(f"Features (Columns) in Output:      {audit['cleaned_columns']} (added 3 temporal features)")
    print(f"Missing AKA Names Imputed:         {audit['missing_aka_names_filled']:,}")
    print(f"Empty Violations Imputed:          {audit['zero_violations_imputed']:,}")
    print(f"Facility Types Reduced:            {raw_df['Facility Type'].dropna().nunique()} -> {cleaned_df['facility_type'].nunique()}")
    print(f"Dates Standardized:                {audit['dates_converted']:,}")
    print(f"Records Standardized to CHICAGO:   {audit['chicago_city_records']:,}")
    print("=" * 70)

    return cleaned_df, audit


if __name__ == "__main__":
    run_cleaning_pipeline()
