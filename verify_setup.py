"""
Day 1 Dataset Ingestion and Verification Script
================================================
Chicago Food Inspections Data Cleaning Pipeline

This script:
1. Loads pipeline configuration from config/config.yaml.
2. Downloads the raw Chicago Food Inspections dataset if not already present.
3. Verifies that pandas can load and read the dataset without error.
4. Prints a structural audit summary (rows, columns, dtypes, memory).
"""

import os
import sys
import yaml
import requests
import pandas as pd

# Ensure standard UTF-8 console output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Loads configuration settings from YAML."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def download_raw_dataset(url: str, dest_path: str):
    """Downloads dataset from source URL with streaming chunks."""
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        size_mb = os.path.getsize(dest_path) / (1024**2)
        print(f"[OK] Raw dataset already exists at: {dest_path} ({size_mb:.1f} MB)")
        return

    print(f"[+] Starting download from City of Chicago Data Portal...")
    print(f"    URL: {url}")
    print(f"    Destination: {dest_path}")

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        downloaded = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB chunk
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    mb = downloaded / (1024 * 1024)
                    print(f"\r    Downloaded: {mb:.1f} MB", end="", flush=True)

    print(f"\n[OK] Download finished: {dest_path}")


def verify_dataset(file_path: str):
    """Loads dataset with pandas and verifies structure."""
    print(f"\n[+] Verifying dataset with pandas: {file_path}")
    df = pd.read_csv(file_path, low_memory=False)

    print("\n" + "=" * 60)
    print("        DAY 1 DATASET VERIFICATION REPORT")
    print("=" * 60)
    print(f"Total Rows:        {len(df):,}")
    print(f"Total Columns:     {len(df.columns)}")
    print(f"Memory Usage:      {df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")
    print("-" * 60)
    print("Columns & Data Types:")
    for i, col in enumerate(df.columns, start=1):
        non_null_count = df[col].notnull().sum()
        pct = (non_null_count / len(df)) * 100
        print(f"  {i:2d}. {col:<20} | {str(df[col].dtype):<10} | {pct:5.1f}% non-null")
    print("=" * 60)
    print("\nSample Preview (First 3 rows):")
    cols_to_preview = [c for c in ["Inspection ID", "DBA Name", "Facility Type", "Risk", "Results"] if c in df.columns]
    print(df[cols_to_preview].head(3).to_string())
    print("\n[OK] VERIFICATION COMPLETE: Dataset is loaded and ready for Day 2 exploration.")


def main():
    config = load_config()
    raw_path = config["data"]["raw_path"]
    source_url = config["data"]["source_url"]

    download_raw_dataset(source_url, raw_path)
    verify_dataset(raw_path)


if __name__ == "__main__":
    main()
