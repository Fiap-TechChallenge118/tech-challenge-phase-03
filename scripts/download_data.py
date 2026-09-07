"""Download the Medical Abstracts TC Corpus into data/raw/.

Usage:
    python scripts/download_data.py

Fetches via kagglehub and copies the CSV files into the local data/raw/
directory so train.py has a stable, versioned input path.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import kagglehub

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
DATASET = "saharalaa/medical-abstracts-tc-corpus"


def main() -> None:
    cache_path = Path(kagglehub.dataset_download(DATASET))
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for src in sorted(cache_path.glob("*.csv")):
        dst = RAW_DIR / src.name
        shutil.copy2(src, dst)
        print(f"{src.name} -> {dst}")
    print(f"Done. Files in {RAW_DIR}")


if __name__ == "__main__":
    main()
