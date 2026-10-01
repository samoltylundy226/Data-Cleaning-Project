"""
Unit tests for anomaly detection & outlier profiling module.
Day 6 comprehensive testing for statistical and domain anomalies.
"""

import pandas as pd
import pytest
from src.anomaly_detection import (
    haversine_distance,
    detect_inspection_frequency_outliers,
    detect_violation_count_outliers,
    detect_spatial_distance_outliers,
    detect_temporal_anomalies,
    build_anomaly_registry,
)


def test_haversine_distance():
    # Distance between Chicago City Hall (41.8832, -87.6324) and O'Hare Airport (41.9742, -87.9073)
    dist = haversine_distance(41.8832, -87.6324, 41.9742, -87.9073)
    assert 24.0 < dist < 26.0  # Approx 24.89 km


def test_haversine_distance_zero():
    # Distance between identical points is 0.0
    dist = haversine_distance(41.8832, -87.6324, 41.8832, -87.6324)
    assert dist == 0.0


def test_detect_inspection_frequency_outliers():
    # Construct a distribution with 20 normal facilities (2 visits each) and 1 extreme facility (100 visits)
    licenses = [f"LIC_{i}" for i in range(20)] * 2 + ["LIC_EXTREME"] * 100
    df = pd.DataFrame({"license_num": licenses})
    result = detect_inspection_frequency_outliers(df)

    assert result["method"].startswith("Interquartile Range")
    assert result["max_value"] == 100
    assert result["outlier_count"] == 1
    assert result["total_entities"] == 21


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
    assert result["classification"].startswith("Statistical Outlier")


def test_detect_spatial_distance_outliers():
    # City Hall is ~0 km, O'Hare Terminal 5 (41.9800, -87.9100) is ~25.36 km (> 25 km threshold)
    df = pd.DataFrame({
        "latitude": [41.8832, 41.9800],
        "longitude": [-87.6324, -87.9100]
    })
    result = detect_spatial_distance_outliers(df, threshold_km=25.0)
    assert result["total_geocoded"] == 2
    assert result["outlier_count"] == 1
    assert result["classification"] == "Legitimate Unusual Observation"


def test_detect_temporal_anomalies():
    df = pd.DataFrame({
        "inspection_date": ["2023-04-17", "2023-04-22", "2023-04-23"],  # Monday, Saturday, Sunday
        "inspection_day_of_week": ["Monday", "Saturday", "Sunday"]
    })
    result = detect_temporal_anomalies(df)
    assert result["weekend_inspections"] == 2
    assert result["saturday_count"] == 1
    assert result["sunday_count"] == 1


def test_build_anomaly_registry():
    # 20 normal facilities (1 visit each) + 1 extreme facility (10 visits) + 1 far coordinate (>25km)
    df = pd.DataFrame({
        "license_num": [f"LIC_{i}" for i in range(20)] + ["LIC_EXTREME"] * 10,
        "violations": ["NO VIOLATIONS CITED"] * 29 + ["1. VIOLATION | 2. VIOLATION"],
        "latitude": [41.8832] * 29 + [41.9800],
        "longitude": [-87.6324] * 29 + [-87.9100],
        "inspection_date": ["2023-01-02"] * 29 + ["2023-01-07"],  # 29 weekdays, 1 Saturday
        "inspection_day_of_week": ["Monday"] * 29 + ["Saturday"],
        "address": ["123 MAIN ST"] * 29 + ["   "],  # 1 blank address
        "zip": ["60601"] * 29 + ["60077"]           # 1 suburban zip
    })
    registry = build_anomaly_registry(df)
    assert len(registry) == 6
    assert list(registry["anomaly_id"]) == ["ANO-001", "ANO-002", "ANO-003", "ANO-004", "ANO-005", "ANO-006"]
    assert set(registry.columns) == {
        "anomaly_id", "anomaly_type", "detection_method",
        "outlier_count", "outlier_rate", "anomaly_classification",
        "action_policy", "rationale"
    }

    # Verify ANO-005 blank address detection
    ano5 = registry[registry["anomaly_id"] == "ANO-005"].iloc[0]
    assert ano5["outlier_count"] == 1
    assert ano5["anomaly_classification"] == "Data-Entry Error"

    # Verify ANO-006 suburban zip detection
    ano6 = registry[registry["anomaly_id"] == "ANO-006"].iloc[0]
    assert ano6["outlier_count"] == 1
    assert ano6["anomaly_classification"] == "Legitimate Unusual Observation"
