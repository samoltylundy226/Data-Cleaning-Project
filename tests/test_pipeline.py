"""
Unit tests for pipeline orchestrator and reporting (Day 5).
"""

import os
import tempfile
import pandas as pd
import pytest
from src.pipeline import setup_logger, generate_after_report
from src.quality_report import generate_quality_comparison
from src.ingestion import load_config, verify_raw_data_exists


def test_load_config():
    config = load_config("config/config.yaml")
    assert "project" in config
    assert "data" in config
    assert config["data"]["raw_path"] == "data/raw/food_inspections_raw.csv"
    assert config["data"]["processed_path"] == "data/processed/food_inspections_cleaned.csv"


def test_verify_raw_data_exists():
    assert verify_raw_data_exists("data/raw/food_inspections_raw.csv") is True
    assert verify_raw_data_exists("data/raw/non_existent_file.csv") is False


def test_setup_logger():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_log = os.path.join(tmpdir, "test_pipeline.log")
        logger = setup_logger(test_log)
        logger.info("Test logging message")

        assert os.path.exists(test_log)
        with open(test_log, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Test logging message" in content

        # Close and remove handlers to release Windows file locks before rmtree
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


def test_generate_after_report():
    sample_df = pd.DataFrame({
        "inspection_id": [1, 2, 3],
        "dba_name": ["RESTAURANT A", "RESTAURANT B", "RESTAURANT C"],
        "facility_type": ["Restaurant", "Grocery Store", None],
        "risk": ["Risk 1 (High)", "Risk 2 (Medium)", "Risk 1 (High)"]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        out_csv = os.path.join(tmpdir, "data_quality_after.csv")
        report_df = generate_after_report(sample_df, output_path=out_csv)

        assert os.path.exists(out_csv)
        assert len(report_df) == 4
        assert set(report_df.columns) == {
            "column_name", "data_type", "total_rows",
            "missing_count", "missing_pct", "unique_count", "status"
        }

        # Check facility_type has controlled nulls
        fac_row = report_df[report_df["column_name"] == "facility_type"].iloc[0]
        assert fac_row["missing_count"] == 1
        assert fac_row["status"] == "CONTROLLED_NULLS"

        # Check clean column
        id_row = report_df[report_df["column_name"] == "inspection_id"].iloc[0]
        assert id_row["missing_count"] == 0
        assert id_row["status"] == "CLEAN"


def test_generate_quality_comparison():
    raw_df = pd.DataFrame({
        "Inspection ID": [1, 2],
        "DBA Name": ["CAFE A", "CAFE B"],
        "AKA Name": [None, "CAFE B"],
        "Violations": [None, "1. VIOLATION"],
        "Risk": ["Risk 1 (High)", "All"],
        "Inspection Date": ["01/01/2023", "02/01/2023"],
        "Address": ["  123 MAIN ST  ", "456 STATE ST"],
        "Facility Type": ["RESTAURANT", "BAR"]
    })
    clean_df = pd.DataFrame({
        "inspection_id": [1, 2],
        "dba_name": ["CAFE A", "CAFE B"],
        "aka_name": ["CAFE A", "CAFE B"],
        "violations": ["NO VIOLATIONS CITED", "1. VIOLATION"],
        "risk": ["Risk 1 (High)", "Risk 1 (High)"],
        "inspection_date": pd.to_datetime(["2023-01-01", "2023-02-01"]),
        "address": ["123 MAIN ST", "456 STATE ST"],
        "facility_type": ["RESTAURANT", "BAR"]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        out_csv = os.path.join(tmpdir, "data_quality_comparison.csv")
        comp_df = generate_quality_comparison(raw_df, clean_df, output_path=out_csv)

        assert os.path.exists(out_csv)
        assert len(comp_df) > 5
        assert "dimension" in comp_df.columns
        assert "metric_name" in comp_df.columns
        assert "before_cleaning" in comp_df.columns
        assert "after_cleaning" in comp_df.columns
        assert "net_change" in comp_df.columns

        # Verify exact counts
        row_metric = comp_df[comp_df["metric_name"] == "Rows Before vs After"].iloc[0]
        assert "2" in row_metric["before_cleaning"]
        assert "2" in row_metric["after_cleaning"]
