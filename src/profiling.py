"""
Data Profiling & Quality Baseline Module
=========================================
Chicago Food Inspections Data Cleaning Pipeline

This module provides automated data profiling functions to inspect,
diagnose, and benchmark raw dataset quality BEFORE any cleaning occurs.
"""

import os
import sys
import yaml
import numpy as np
import pandas as pd


def load_dataset(filepath: str) -> pd.DataFrame:
    """Loads raw dataset from CSV with low_memory=False for accurate dtype inference."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at: {filepath}")
    return pd.read_csv(filepath, low_memory=False)


def get_dataset_overview(df: pd.DataFrame) -> dict:
    """Calculates dataset-level baseline metrics."""
    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / (1024**2), 2),
        "exact_duplicate_rows": int(df.duplicated().sum()),
        "duplicate_inspection_ids": int(df["Inspection ID"].duplicated().sum()) if "Inspection ID" in df.columns else 0,
        "total_missing_cells": int(df.isnull().sum().sum()),
        "overall_missing_pct": round((df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100, 2),
    }


def identify_column_issues(col: str, series: pd.Series, df_len: int) -> list:
    """Identifies potential data quality issues for a single column."""
    issues = []
    n_miss = int(series.isnull().sum())
    pct_miss = (n_miss / df_len) * 100

    if pct_miss > 25.0:
        issues.append(f"High missingness ({pct_miss:.1f}%)")
    elif pct_miss > 0.0:
        issues.append(f"Missing values ({pct_miss:.2f}%)")

    # String / Categorical checks
    if pd.api.types.is_string_dtype(series) or series.dtype == "object":
        non_null = series.dropna().astype(str)
        # Leading/trailing whitespace
        whitespace_count = int((non_null != non_null.str.strip()).sum())
        if whitespace_count > 0:
            issues.append(f"Whitespace padding ({whitespace_count:,} rows)")

        # Casing inconsistency
        raw_unique = non_null.nunique()
        lower_unique = non_null.str.lower().str.strip().nunique()
        if raw_unique > lower_unique:
            issues.append(f"Inconsistent casing ({raw_unique - lower_unique} duplicate variations)")

        # Special column specific checks
        if col == "Inspection Date":
            issues.append("Stored as string instead of datetime")
        elif col == "City":
            non_chicago = int((~non_null.str.upper().str.strip().isin(["CHICAGO"])).sum())
            if non_chicago > 0:
                issues.append(f"Non-standard or suburban cities ({non_chicago:,} rows)")
        elif col == "Risk":
            all_risk_count = int((non_null.str.strip() == "All").sum())
            if all_risk_count > 0:
                issues.append(f"Non-standard risk category 'All' ({all_risk_count} rows)")
        elif col == "Violations":
            issues.append("Unstructured free-text log with multiple concatenated violations")

    # Numerical checks
    elif pd.api.types.is_numeric_dtype(series):
        zeros = int((series == 0).sum())
        if zeros > 0:
            issues.append(f"Contains zero values ({zeros:,} rows)")

        if col == "License #":
            issues.append("Stored as float due to NaNs; zero values present")
        elif col == "Zip":
            issues.append("Stored as float; contains non-Chicago / out-of-state zips")
        elif col in ["Latitude", "Longitude"]:
            null_coords = int(series.isnull().sum())
            if null_coords > 0:
                issues.append(f"Missing geospatial coordinates ({null_coords:,} rows)")

    return issues


def build_column_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Generates a comprehensive column-by-column data quality baseline table."""
    records = []
    df_len = len(df)

    for col in df.columns:
        series = df[col]
        n_miss = int(series.isnull().sum())
        pct_miss = round((n_miss / df_len) * 100, 2)
        n_unique = int(series.nunique(dropna=True))
        unique_pct = round((n_unique / df_len) * 100, 2)

        # Zeros
        if pd.api.types.is_numeric_dtype(series):
            num_zeros = int((series == 0).sum())
        else:
            num_zeros = int((series.astype(str) == "0").sum())

        # Whitespace and min/max
        if pd.api.types.is_string_dtype(series) or series.dtype == "object":
            ws_only = int(series.dropna().astype(str).str.strip().eq("").sum())
            non_null = series.dropna().astype(str)
            min_val = f"{non_null.str.len().min()} chars" if len(non_null) > 0 else "N/A"
            max_val = f"{non_null.str.len().max()} chars" if len(non_null) > 0 else "N/A"
        else:
            ws_only = 0
            clean_s = series.dropna()
            min_val = str(clean_s.min()) if not clean_s.empty else "N/A"
            max_val = str(clean_s.max()) if not clean_s.empty else "N/A"

        issues = identify_column_issues(col, series, df_len)

        records.append({
            "column_name": col,
            "data_type": str(series.dtype),
            "total_rows": df_len,
            "missing_count": n_miss,
            "missing_pct": pct_miss,
            "unique_count": n_unique,
            "unique_pct": unique_pct,
            "num_zeros": num_zeros,
            "num_whitespace_only": ws_only,
            "min_or_shortest": min_val,
            "max_or_longest": max_val,
            "suspected_data_quality_issues": "; ".join(issues) if issues else "None identified",
        })

    return pd.DataFrame(records)


def export_baseline_report(profile_df: pd.DataFrame, output_path: str = "reports/data_quality_before.csv"):
    """Saves data quality baseline report to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    profile_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[OK] Saved BEFORE data quality report to: {output_path}")


def print_executive_summary(overview: dict, profile_df: pd.DataFrame):
    """Prints a structured, professional executive summary to the console."""
    print("\n" + "=" * 80)
    print("        DAY 2: DATA PROFILING & BASELINE QUALITY REPORT")
    print("=" * 80)
    print(f"Total Records (Rows):         {overview['total_rows']:,}")
    print(f"Total Features (Columns):      {overview['total_columns']}")
    print(f"Deep Memory Usage:             {overview['memory_mb']:.2f} MB")
    print(f"Exact Duplicate Rows:          {overview['exact_duplicate_rows']:,}")
    print(f"Duplicate Inspection IDs:      {overview['duplicate_inspection_ids']:,}")
    print(f"Total Missing Values:          {overview['total_missing_cells']:,} ({overview['overall_missing_pct']}%)")
    print("=" * 80)

    print("\n[+] Column Quality Baseline:")
    display_cols = ["column_name", "data_type", "missing_count", "missing_pct", "unique_count", "suspected_data_quality_issues"]
    formatted_df = profile_df[display_cols].copy()
    formatted_df["missing_pct"] = formatted_df["missing_pct"].apply(lambda x: f"{x:.2f}%")
    print(formatted_df.to_string(index=False))
    print("=" * 80)


def run_profiling(raw_path: str = "data/raw/food_inspections_raw.csv", report_path: str = "reports/data_quality_before.csv"):
    """Main execution pipeline for Day 2 profiling."""
    print(f"[+] Loading raw dataset from: {raw_path}...")
    df = load_dataset(raw_path)

    overview = get_dataset_overview(df)
    profile_df = build_column_profile(df)

    export_baseline_report(profile_df, report_path)
    print_executive_summary(overview, profile_df)
    return overview, profile_df


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    run_profiling()
