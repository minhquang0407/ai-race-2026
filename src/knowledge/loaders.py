"""Loaders for lightweight medical knowledge CSV files."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV file into dictionaries.

    The repository sample CSVs are intentionally small and transparent. When
    replacing them with official data, keep the same normalized columns where
    possible so downstream graph/index code does not change.
    """

    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def split_aliases(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().strip().split())


__all__ = ["normalize_text", "read_csv_rows", "split_aliases"]
