"""
Unit tests for data profiling module (Day 2).
"""

import os
import pandas as pd
from src.profiling import get_dataset_overview, build_column_profile, identify_column_issues


def test_get_dataset_overview():
    sample_df = pd.DataFrame({
        "Inspection ID": [101, 102, 103],
        "DBA Name": ["A Cafe", "B Diner", "C Grill"],
        "Results": ["Pass", "Fail", "Pass"],
    })
    overview = get_dataset_overview(sample_df)
    assert overview["total_rows"] == 3
    assert overview["total_columns"] == 3
    assert overview["exact_duplicate_rows"] == 0
    assert overview["duplicate_inspection_ids"] == 0
    assert overview["total_missing_cells"] == 0


def test_build_column_profile():
    sample_df = pd.DataFrame({
        "City": ["Chicago", "CHICAGO", None],
        "Zip": [60601.0, 60602.0, None],
    })
    profile_df = build_column_profile(sample_df)
    assert len(profile_df) == 2
    assert "column_name" in profile_df.columns
    assert "missing_count" in profile_df.columns

    city_row = profile_df[profile_df["column_name"] == "City"].iloc[0]
    assert city_row["missing_count"] == 1
    assert "Inconsistent casing" in city_row["suspected_data_quality_issues"]
