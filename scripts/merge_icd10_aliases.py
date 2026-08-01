"""Merge alias CSV rows into an existing ICD-10 CSV.

This is useful when the canonical XML source is not locally available but an
already-converted `icd10_full.csv` exists.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge ICD-10 aliases into an existing ICD CSV")
    parser.add_argument("--icd-path", default="data/raw/icd10_full.csv")
    parser.add_argument("--aliases", default="data/raw/icd10_aliases_vi.csv")
    parser.add_argument("--output", default=None, help="Defaults to overwriting --icd-path")
    return parser


def load_aliases(path: Path) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            code = (row.get("code") or "").strip()
            alias = (row.get("alias") or "").strip()
            if code and alias:
                aliases.setdefault(code, []).append(alias)
    return aliases


def main() -> int:
    args = build_parser().parse_args()
    icd_path = Path(args.icd_path)
    alias_path = Path(args.aliases)
    output_path = Path(args.output) if args.output else icd_path

    aliases_by_code = load_aliases(alias_path)
    with icd_path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise ValueError(f"empty ICD CSV: {icd_path}")
        rows = list(reader)

    merged_codes = 0
    for row in rows:
        code = (row.get("code") or "").strip()
        aliases = aliases_by_code.get(code)
        if not aliases:
            continue
        existing = [item.strip() for item in (row.get("aliases") or "").split("|") if item.strip()]
        seen = {item.casefold() for item in existing}
        before = len(existing)
        for alias in aliases:
            if alias.casefold() not in seen:
                existing.append(alias)
                seen.add(alias.casefold())
        if len(existing) > before:
            merged_codes += 1
        row["aliases"] = "|".join(existing)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"merged_codes={merged_codes} output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
