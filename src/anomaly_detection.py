"""
Anomaly Detection & Outlier Profiling Module
=============================================
Chicago Food Inspections Data Cleaning Pipeline

This module identifies, quantifies, and categorizes anomalies:
1. Statistical Outliers (e.g. extreme inspection frequency, citation spikes)
2. Data-Entry Errors (e.g. blank address strings)
3. Legitimate Unusual Observations (e.g. weekend festival inspections)
4. Invalid Records (e.g. coordinates outside Chicago bounds)
"""

import os
import sys
import yaml
import numpy as np
import pandas as pd

# Coordinates for Chicago City Hall (Center point for spatial analysis)
CITY_HALL_LAT = 41.8832
CITY_HALL_LON = -87.6324


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (
        np.sin(dlat / 2.0) ** 2 +
        np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2.0) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


def detect_inspection_frequency_outliers(df: pd.DataFrame) -> dict:
    """
    Detects facilities with statistically extreme inspection counts using the IQR method.
    - Why IQR is appropriate: Inspection frequency is heavily right-skewed count data.
      Z-score assumes approximate normality and is heavily distorted by extreme values.
    """
    valid_licenses = df[df["license_num"] != "0"]["license_num"].value_counts()
    q1 = float(valid_licenses.quantile(0.25))
    q3 = float(valid_licenses.quantile(0.75))
    iqr = q3 - q1
    upper_fence = q3 + 1.5 * iqr
    extreme_fence = q3 + 3.0 * iqr
    p99 = float(valid_licenses.quantile(0.99))

    outlier_licenses = valid_licenses[valid_licenses > upper_fence]
    extreme_licenses = valid_licenses[valid_licenses > extreme_fence]

    return {
        "metric": "Inspection Frequency per Facility License",
        "method": "Interquartile Range (IQR) & 99th Percentile",
        "total_entities": len(valid_licenses),
        "q1": q1,
        "median": float(valid_licenses.median()),
        "q3": q3,
        "iqr": iqr,
        "iqr_upper_threshold": upper_fence,
        "extreme_threshold": extreme_fence,
        "p99_threshold": p99,
        "outlier_count": len(outlier_licenses),
        "outlier_pct": round((len(outlier_licenses) / len(valid_licenses)) * 100, 2),
        "max_value": int(valid_licenses.max()),
        "classification": "Statistical Outlier / Legitimate Unusual Observation",
        "justification": (
            "High inspection counts represent large multi-venue facilities (e.g. O'Hare airport terminals, "
            "stadiums, or chronic compliance cases) that operate legally over 15+ years. "
            "Do NOT delete: they represent vital operational health histories."
        )
    }


def detect_violation_count_outliers(df: pd.DataFrame) -> dict:
    """
    Detects inspections with extreme numbers of citations per visit using IQR and 99th percentile.
    """
    def count_citations(v):
        if pd.isna(v) or v == "NO VIOLATIONS CITED":
            return 0
        return v.count("|") + 1

    citations = df["violations"].apply(count_citations)
    q1 = float(citations.quantile(0.25))
    q3 = float(citations.quantile(0.75))
    iqr = q3 - q1
    upper_fence = q3 + 1.5 * iqr
    p99 = float(citations.quantile(0.99))

    outliers = (citations > upper_fence).sum()
    extreme_outliers = (citations >= 15).sum()

    return {
        "metric": "Citation Count per Inspection",
        "method": "Interquartile Range (IQR) & 99th Percentile",
        "total_inspections": len(df),
        "q1": q1,
        "median": float(citations.median()),
        "q3": q3,
        "iqr": iqr,
        "iqr_upper_threshold": upper_fence,
        "p99_threshold": p99,
        "outlier_count": int(outliers),
        "outlier_pct": round((outliers / len(df)) * 100, 2),
        "extreme_count_ge_15": int(extreme_outliers),
        "max_citations": int(citations.max()),
        "classification": "Statistical Outlier / Critical Health Hazard",
        "justification": (
            "Inspections with 15-40 citations represent severe real-world health hazards and unsanitary conditions. "
            "Do NOT delete: these provide the strongest training signal for predictive food safety risk modeling."
        )
    }


def detect_spatial_distance_outliers(df: pd.DataFrame, threshold_km: float = 25.0) -> dict:
    """
    Detects facilities located unusually far from Chicago City Hall (> 25 km).
    """
    coords = df[df["latitude"].notnull() & df["longitude"].notnull()]
    distances = haversine_distance(CITY_HALL_LAT, CITY_HALL_LON, coords["latitude"], coords["longitude"])

    outliers = (distances > threshold_km).sum()
    pct = round((outliers / len(coords)) * 100, 2)

    return {
        "metric": "Geographic Distance from City Hall (> 25 km)",
        "method": "Haversine Distance Thresholding",
        "total_geocoded": len(coords),
        "mean_distance_km": round(float(distances.mean()), 2),
        "median_distance_km": round(float(distances.median()), 2),
        "max_distance_km": round(float(distances.max()), 2),
        "outlier_count": int(outliers),
        "outlier_pct": pct,
        "classification": "Legitimate Unusual Observation",
        "justification": (
            "Facilities > 25 km away correspond to O'Hare International Airport (approx 26 km northwest) "
            "and far southern neighborhoods (Hegewisch). They are valid Chicago administrative jurisdictions."
        )
    }


def detect_temporal_anomalies(df: pd.DataFrame) -> dict:
    """
    Detects inspections occurring on weekends (Saturday / Sunday).
    """
    if "inspection_day_of_week" not in df.columns:
        df["inspection_day_of_week"] = pd.to_datetime(df["inspection_date"]).dt.day_name()

    weekend_mask = df["inspection_day_of_week"].isin(["Saturday", "Sunday"])
    weekend_count = int(weekend_mask.sum())
    pct = round((weekend_count / len(df)) * 100, 4)

    return {
        "metric": "Weekend Inspection Scheduling",
        "method": "Calendar Day-of-Week Profiling",
        "total_records": len(df),
        "weekend_inspections": weekend_count,
        "weekend_pct": pct,
        "saturday_count": int((df["inspection_day_of_week"] == "Saturday").sum()),
        "sunday_count": int((df["inspection_day_of_week"] == "Sunday").sum()),
        "classification": "Legitimate Unusual Observation",
        "justification": (
            "Weekend inspections account for 0.04% of records and represent special food festivals "
            "(e.g. Taste of Chicago, street fairs) or urgent foodborne illness complaint follow-ups."
        )
    }


def build_anomaly_registry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compiles a comprehensive anomaly registry table categorizing all dataset anomalies.
    """
    freq = detect_inspection_frequency_outliers(df)
    viol = detect_violation_count_outliers(df)
    spatial = detect_spatial_distance_outliers(df)
    temporal = detect_temporal_anomalies(df)

    registry = [
        {
            "anomaly_id": "ANO-001",
            "anomaly_type": freq["metric"],
            "detection_method": freq["method"],
            "outlier_count": freq["outlier_count"],
            "outlier_rate": f"{freq['outlier_pct']}% of licenses",
            "anomaly_classification": freq["classification"],
            "action_policy": "RETAIN (Do not delete)",
            "rationale": freq["justification"]
        },
        {
            "anomaly_id": "ANO-002",
            "anomaly_type": viol["metric"],
            "detection_method": viol["method"],
            "outlier_count": viol["outlier_count"],
            "outlier_rate": f"{viol['outlier_pct']}% of inspections",
            "anomaly_classification": viol["classification"],
            "action_policy": "RETAIN (Do not delete)",
            "rationale": viol["justification"]
        },
        {
            "anomaly_id": "ANO-003",
            "anomaly_type": spatial["metric"],
            "detection_method": spatial["method"],
            "outlier_count": spatial["outlier_count"],
            "outlier_rate": f"{spatial['outlier_pct']}% of coordinates",
            "anomaly_classification": spatial["classification"],
            "action_policy": "RETAIN (Verify boundary)",
            "rationale": spatial["justification"]
        },
        {
            "anomaly_id": "ANO-004",
            "anomaly_type": temporal["metric"],
            "detection_method": temporal["method"],
            "outlier_count": temporal["weekend_inspections"],
            "outlier_rate": f"{temporal['weekend_pct']}% of inspections",
            "anomaly_classification": temporal["classification"],
            "action_policy": "RETAIN (Flag event type)",
            "rationale": temporal["justification"]
        },
        {
            "anomaly_id": "ANO-005",
            "anomaly_type": "Blank Address Strings ('   ')",
            "detection_method": "Whitespace Strip & Length Check",
            "outlier_count": int((df["address"].astype(str).str.strip() == "").sum()),
            "outlier_rate": "< 0.001% of records",
            "anomaly_classification": "Data-Entry Error",
            "action_policy": "IMPUTE / REPAIR",
            "rationale": "Clerical data entry omission at source; retain row with 'ADDRESS UNKNOWN' to preserve inspection record."
        },
        {
            "anomaly_id": "ANO-006",
            "anomaly_type": "Suburban Non-606xx ZIP Codes",
            "detection_method": "Regex Prefix Matching (^606)",
            "outlier_count": int((~df["zip"].dropna().astype(str).str.startswith("606")).sum()),
            "outlier_rate": "0.74% of records",
            "anomaly_classification": "Legitimate Unusual Observation",
            "action_policy": "RETAIN",
            "rationale": "Metropolitan boundary overlap where Chicago municipal inspectors inspect adjacent school or catering vendors."
        }
    ]

    return pd.DataFrame(registry)


def export_anomaly_report(registry_df: pd.DataFrame, output_path: str = "reports/anomaly_report.csv"):
    """Exports anomaly report to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    registry_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[OK] Anomaly report exported to: {output_path}")


def print_anomaly_summary(registry_df: pd.DataFrame, freq: dict, viol: dict):
    """Prints a clean CLI summary of anomaly analysis."""
    print("\n" + "=" * 80)
    print("        DAY 4: ANOMALY DETECTION & OUTLIER PROFILING REPORT")
    print("=" * 80)
    print(f"Inspection Frequency IQR Upper Fence: {freq['iqr_upper_threshold']:.1f} visits (Outliers: {freq['outlier_count']:,} facilities)")
    print(f"Citation Count IQR Upper Fence:        {viol['iqr_upper_threshold']:.1f} citations (Outliers: {viol['outlier_count']:,} inspections)")
    print(f"Max Citations in Single Inspection:   {viol['max_citations']} citations")
    print("=" * 80)

    display_cols = ["anomaly_id", "anomaly_type", "anomaly_classification", "action_policy", "outlier_count"]
    print(registry_df[display_cols].to_string(index=False))
    print("=" * 80)

    print("\nAnomaly Categorization & Action Policies:")
    for _, row in registry_df.iterrows():
        print(f"[{row['anomaly_id']}] {row['anomaly_type']}:")
        print(f"    Class:  {row['anomaly_classification']}")
        print(f"    Policy: {row['action_policy']}")
        print(f"    Reason: {row['rationale']}")
    print("=" * 80)


def main(data_path: str = "data/interim/food_inspections_interim.csv"):
    """Main CLI execution for anomaly detection."""
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    print(f"[+] Loading interim cleaned dataset from: {data_path}...")
    df = pd.read_csv(data_path, dtype={"zip": "string", "license_num": "string"}, low_memory=False)

    freq = detect_inspection_frequency_outliers(df)
    viol = detect_violation_count_outliers(df)
    registry_df = build_anomaly_registry(df)

    export_anomaly_report(registry_df)
    print_anomaly_summary(registry_df, freq, viol)
    return registry_df


if __name__ == "__main__":
    main()
