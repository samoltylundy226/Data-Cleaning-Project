"""
Unit tests for anomaly detection & outlier module (Day 4).
"""

import pandas as pd
from src.anomaly_detection import (
    haversine_distance,
    detect_inspection_frequency_outliers,
    detect_violation_count_outliers,
    detect_temporal_anomalies,
)


def test_haversine_distance():
    # Distance between Chicago City Hall (41.8832, -87.6324) and O'Hare Airport (41.9742, -87.9073)
    dist = haversine_distance(41.8832, -87.6324, 41.9742, -87.9073)
    assert 24.0 < dist < 28.0  # Approx 25-26 km


def test_detect_inspection_frequency_outliers():
    # Construct a dataset where one license has 50 inspections, others have 2
    licenses = ["LIC_COMMON"] * 50 + ["LIC_EXTREME"] * 100 + ["LIC_OTHER"] * 50
    df = pd.DataFrame({"license_num": licenses})
    result = detect_inspection_frequency_outliers(df)
    assert result["method"].startswith("Interquartile Range")
    assert result["max_value"] == 100


def test_detect_violation_count_outliers():
    df = pd.DataFrame({
        "violations": [
            "NO VIOLATIONS CITED",
            "1. VIOLATION | 2. VIOLATION",
            "1. V | 2. V | 3. V | 4. V | 5. V | 6. V | 7. V | 8. V | 9. V | 10. V"
        ]
    })
    result = detect_violation_count_outliers(df)
    assert result["max_citations"] == 10


def test_detect_temporal_anomalies():
    df = pd.DataFrame({
        "inspection_date": ["2023-04-17", "2023-04-22", "2023-04-23"],  # Monday, Saturday, Sunday
        "inspection_day_of_week": ["Monday", "Saturday", "Sunday"]
    })
    result = detect_temporal_anomalies(df)
    assert result["weekend_inspections"] == 2
    assert result["saturday_count"] == 1
    assert result["sunday_count"] == 1
