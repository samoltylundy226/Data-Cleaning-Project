"""
Master Pipeline Orchestrator
=============================
Chicago Food Inspections Data Cleaning & Data Quality Pipeline

Executes the complete end-to-end automated workflow:
Raw Data -> Ingestion -> Profiling -> Cleaning -> Anomaly Detection -> Validation -> Processed Data -> Quality Reports
"""

import os
import sys
import time
import logging
import yaml
import pandas as pd
from datetime import datetime

# Import modular components
from src.ingestion import load_config, verify_raw_data_exists, download_raw_dataset, ingest_raw_data
from src.profiling import get_dataset_overview, build_column_profile, export_baseline_report
from src.cleaning import clean_food_inspections
from src.anomaly_detection import build_anomaly_registry, export_anomaly_report
from src.validation import run_all_validations, export_validation_report
from src.quality_report import generate_quality_comparison


def setup_logger(log_file: str = "pipeline.log") -> logging.Logger:
    """Configures structured dual-output logging (console + log file)."""
    logger = logging.getLogger("DataQualityPipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def generate_after_report(cleaned_df: pd.DataFrame, output_path: str = "reports/data_quality_after.csv") -> pd.DataFrame:
    """Generates a post-cleaning data quality summary table."""
    records = []
    total_len = len(cleaned_df)

    for col in cleaned_df.columns:
        s = cleaned_df[col]
        null_count = int(s.isnull().sum())
        null_pct = round((null_count / total_len) * 100, 2)
        n_unique = int(s.nunique(dropna=True))

        records.append({
            "column_name": col,
            "data_type": str(s.dtype),
            "total_rows": total_len,
            "missing_count": null_count,
            "missing_pct": null_pct,
            "unique_count": n_unique,
            "status": "CLEAN" if null_count == 0 else "CONTROLLED_NULLS"
        })

    after_df = pd.DataFrame(records)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    after_df.to_csv(output_path, index=False, encoding="utf-8")
    return after_df


def run_pipeline(config_path: str = "config/config.yaml") -> dict:
    """
    Executes the complete Day 5 end-to-end data cleaning and quality pipeline.
    """
    start_time = time.time()
    logger = setup_logger("pipeline.log")

    logger.info("=" * 75)
    logger.info("STARTING END-TO-END DATA QUALITY PIPELINE (Day 5)")
    logger.info("=" * 75)

    # 1. Configuration Resolution
    logger.info(f"Loading pipeline configuration from: {config_path}")
    config = load_config(config_path)

    raw_path = config["data"]["raw_path"]
    interim_path = config["data"]["interim_path"]
    processed_path = config["data"]["processed_path"]
    source_url = config["data"]["source_url"]

    logger.info(f"Project: {config['project']['name']} (v{config['project']['version']})")
    logger.info(f"Input Raw Path:       {raw_path}")
    logger.info(f"Interim Output Path:  {interim_path}")
    logger.info(f"Final Processed Path: {processed_path}")

    # 2. Ingestion Stage
    logger.info("--- STAGE 1: DATA INGESTION ---")
    if not verify_raw_data_exists(raw_path):
        logger.warning(f"Raw data file missing at {raw_path}. Initiating download...")
        download_raw_dataset(source_url, raw_path)

    raw_df, raw_meta = ingest_raw_data(config)
    logger.info(f"Ingested raw dataset: {raw_meta['initial_rows']:,} rows, {raw_meta['initial_columns']} columns ({raw_meta['file_size_mb']} MB)")

    # 3. Pre-Cleaning Profiling Stage
    logger.info("--- STAGE 2: PRE-CLEANING BASELINE PROFILING ---")
    before_profile = build_column_profile(raw_df)
    export_baseline_report(before_profile, "reports/data_quality_before.csv")
    raw_overview = get_dataset_overview(raw_df)
    logger.info(f"Baseline Quality Profile Generated: {raw_overview['total_missing_cells']:,} missing cells ({raw_overview['overall_missing_pct']}%)")

    # 4. Cleaning & Standardization Stage
    logger.info("--- STAGE 3: DATA CLEANING & STANDARDIZATION ---")
    cleaned_df, clean_audit = clean_food_inspections(raw_df)

    # Save intermediate interim dataset
    os.makedirs(os.path.dirname(interim_path), exist_ok=True)
    cleaned_df.to_csv(interim_path, index=False, encoding="utf-8")
    interim_size = os.path.getsize(interim_path) / (1024**2)
    logger.info(f"Cleaned interim dataset written to: {interim_path} ({interim_size:.2f} MB)")
    logger.info(f"  - AKA Names filled: {clean_audit['missing_aka_names_filled']:,}")
    logger.info(f"  - Clean Inspections imputed: {clean_audit['zero_violations_imputed']:,}")
    logger.info(f"  - Facility types consolidated: {clean_audit['facility_types_standardized']} redundant categories removed")
    logger.info(f"  - Timestamps parsed: {clean_audit['dates_converted']:,}")

    # 5. Anomaly Detection Stage
    logger.info("--- STAGE 4: ANOMALY DETECTION & OUTLIER PROFILING ---")
    anomaly_registry = build_anomaly_registry(cleaned_df)
    export_anomaly_report(anomaly_registry, "reports/anomaly_report.csv")
    logger.info(f"Anomaly Registry compiled with {len(anomaly_registry)} monitored statistical rules.")

    # 6. Data Validation Stage
    logger.info("--- STAGE 5: DATA VALIDATION & QUALITY GATING ---")
    validation_df = run_all_validations(cleaned_df)
    export_validation_report(validation_df, "reports/validation_report.csv")

    passed_checks = int((validation_df["status"] == "PASS").sum())
    warning_checks = int((validation_df["status"] == "WARNING").sum())
    failed_checks = int((validation_df["status"] == "FAIL").sum())

    logger.info(f"Validation Scorecard: PASS={passed_checks} | WARNING={warning_checks} | FAIL={failed_checks}")

    if failed_checks > 0:
        logger.error(f"PIPELINE HALTED: {failed_checks} critical validation rules failed!")
        failing_rules = validation_df[validation_df["status"] == "FAIL"][["check_id", "rule_description", "details"]]
        logger.error(failing_rules.to_string(index=False))
        raise RuntimeError("Pipeline failed critical validation checks.")

    # 7. Final Processed Dataset Export
    logger.info("--- STAGE 6: FINAL PROCESSED DATASET EXPORT ---")
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    cleaned_df.to_csv(processed_path, index=False, encoding="utf-8")
    processed_size = os.path.getsize(processed_path) / (1024**2)
    logger.info(f"[SUCCESS] Final processed dataset exported to: {processed_path} ({processed_size:.2f} MB)")

    # 8. Post-Cleaning Quality Report Generation
    logger.info("--- STAGE 7: QUALITY METRICS REPORTING ---")
    after_df = generate_after_report(cleaned_df, "reports/data_quality_after.csv")
    comp_df = generate_quality_comparison(raw_df, cleaned_df, "reports/data_quality_comparison.csv")
    logger.info("Generated post-cleaning data quality report: reports/data_quality_after.csv")
    logger.info("Generated before vs after quality comparison: reports/data_quality_comparison.csv")

    duration = time.time() - start_time
    logger.info(f"Pipeline executed in {duration:.2f} seconds.")
    logger.info("=" * 75)

    # Display Executive Summary Table
    print("\n" + "=" * 80)
    print("         END-TO-END DATA QUALITY PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Pipeline Status:          SUCCESS")
    print(f"Total Execution Time:     {duration:.2f} seconds")
    print(f"Raw Input Records:        {raw_meta['initial_rows']:,} rows, {raw_meta['initial_columns']} columns")
    print(f"Cleaned Output Records:   {len(cleaned_df):,} rows, {len(cleaned_df.columns)} columns (zero rows deleted)")
    print(f"Validation Scorecard:     {passed_checks} PASS | {warning_checks} WARNING | {failed_checks} FAIL")
    print(f"Artifacts Generated:")
    print(f"  1. Clean Processed Data: {processed_path} ({processed_size:.2f} MB)")
    print(f"  2. Interim Data:         {interim_path} ({interim_size:.2f} MB)")
    print(f"  3. Baseline Report:      reports/data_quality_before.csv")
    print(f"  4. Post-Cleaning Report: reports/data_quality_after.csv")
    print(f"  5. Quality Comparison:   reports/data_quality_comparison.csv")
    print(f"  6. Validation Scorecard: reports/validation_report.csv")
    print(f"  7. Anomaly Registry:     reports/anomaly_report.csv")
    print(f"  8. Execution Log:        pipeline.log")
    print("=" * 80)

    return {
        "status": "SUCCESS",
        "duration_seconds": round(duration, 2),
        "raw_records": raw_meta["initial_rows"],
        "processed_records": len(cleaned_df),
        "columns_count": len(cleaned_df.columns),
        "passed_checks": passed_checks,
        "warning_checks": warning_checks,
        "failed_checks": failed_checks,
        "processed_path": processed_path,
    }


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    run_pipeline()
