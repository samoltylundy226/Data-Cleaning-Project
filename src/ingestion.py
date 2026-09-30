"""
Data Ingestion Module
======================
Chicago Food Inspections Data Cleaning Pipeline

This module handles raw data ingestion, source verification, download retrieval,
and initial shape accounting without mutating source data.
"""

import os
import sys
import yaml
import requests
import pandas as pd


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Loads configuration settings from a YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def verify_raw_data_exists(filepath: str) -> bool:
    """Checks whether the raw data file exists and is non-empty."""
    return os.path.exists(filepath) and os.path.getsize(filepath) > 1000


def download_raw_dataset(url: str, dest_path: str, chunk_size: int = 1024 * 1024):
    """
    Downloads raw dataset from source URL with streaming chunks if not already present.
    """
    if verify_raw_data_exists(dest_path):
        size_mb = os.path.getsize(dest_path) / (1024**2)
        print(f"[OK] Raw dataset already exists at: {dest_path} ({size_mb:.1f} MB)")
        return dest_path

    print(f"[+] Downloading Chicago Food Inspections dataset from: {url}")
    print(f"    Target: {dest_path}")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        downloaded = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    mb = downloaded / (1024 * 1024)
                    print(f"\r    Downloaded: {mb:.1f} MB", end="", flush=True)

    size_mb = os.path.getsize(dest_path) / (1024**2)
    print(f"\n[OK] Ingestion download finished: {dest_path} ({size_mb:.1f} MB)")
    return dest_path


def ingest_raw_data(config: dict = None, config_path: str = "config/config.yaml") -> tuple[pd.DataFrame, dict]:
    """
    Orchestrates raw data ingestion:
    1. Reads configuration paths.
    2. Verifies raw data presence (downloads if absent).
    3. Loads the raw CSV using pandas.
    4. Computes initial structural metadata.
    """
    if config is None:
        config = load_config(config_path)

    raw_path = config["data"]["raw_path"]
    source_url = config["data"]["source_url"]

    # Verify and retrieve if necessary
    if not verify_raw_data_exists(raw_path):
        download_raw_dataset(source_url, raw_path)

    print(f"[+] Loading raw dataset into memory from: {raw_path}...")
    df = pd.read_csv(raw_path, low_memory=False)

    metadata = {
        "raw_path": raw_path,
        "source_url": source_url,
        "initial_rows": len(df),
        "initial_columns": len(df.columns),
        "column_names": list(df.columns),
        "memory_mb": round(df.memory_usage(deep=True).sum() / (1024**2), 2),
        "file_size_mb": round(os.path.getsize(raw_path) / (1024**2), 2),
    }

    print(f"[OK] Raw data ingested: {metadata['initial_rows']:,} rows, {metadata['initial_columns']} columns ({metadata['memory_mb']} MB)")
    return df, metadata


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    df, meta = ingest_raw_data()
