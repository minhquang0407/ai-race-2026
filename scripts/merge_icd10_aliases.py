"""Merge alias CSV rows and Vietnamese ICD names into an existing ICD-10 CSV.

Two sources of extra data:
1. --aliases: CSV with columns code,alias  (manual curated aliases)
2. --kcb-path: icd10_kcb_vi.csv from fetch_icd_kcb_vn.py  (Vietnamese ICD names)

Both are merged into the `aliases` column of icd10_full.csv.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge ICD-10 aliases and KCB Vietnamese names into ICD CSV")
    parser.add_argument("--icd-path", default="data/raw/icd10_full.csv")
    parser.add_argument("--aliases", default="data/raw/icd10_aliases_vi.csv", help="Manual alias CSV (code,alias)")
    parser.add_argument("--kcb-path", default=None, help="icd10_kcb_vi.csv from fetch_icd_kcb_vn.py")
    parser.add_argument("--output", default=None, help="Defaults to overwriting --icd-path")
    return parser


def load_manual_aliases(path: Path) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            code = (row.get("code") or "").strip()
            alias = (row.get("alias") or "").strip()
            if code and alias:
                aliases.setdefault(code, []).append(alias)
    return aliases


def load_kcb_aliases(path: Path) -> dict[str, list[str]]:
    """Load Vietnamese names from icd10_kcb_vi.csv as aliases.

    Rules:
    - Only use rows with model in ('type', 'disease')
    - Skip rows where name is empty or equals the code
    - Include aliases column (pipe-separated) if present
    """
    aliases: dict[str, list[str]] = {}

    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            model = (row.get("model") or "").strip()
            if model not in ("type", "disease"):
                continue

            code = (row.get("code") or "").strip()
            name = (row.get("name") or "").strip()
            raw_aliases = (row.get("aliases") or "").strip()

            if not code:
                continue

            candidates: list[str] = []
            if name and name != code:
                candidates.append(name)
            for part in raw_aliases.split("|"):
                part = part.strip()
                if part and part != code and part != name:
                    # Strip leading (CODE) prefix often present in kcb aliases
                    if part.startswith("(") and ")" in part:
                        part = part[part.index(")") + 1:].strip()
                    if part:
                        candidates.append(part)

            if candidates:
                aliases.setdefault(code, []).extend(candidates)

    return aliases


def merge_aliases_into_rows(
    rows: list[dict],
    aliases_by_code: dict[str, list[str]],
) -> int:
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
    return merged_codes


def main() -> int:
    args = build_parser().parse_args()
    icd_path = Path(args.icd_path)
    alias_path = Path(args.aliases)
    output_path = Path(args.output) if args.output else icd_path

    with icd_path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise ValueError(f"empty ICD CSV: {icd_path}")
        rows = list(reader)

    total_merged = 0

    # 1. Manual aliases CSV
    if alias_path.exists():
        manual = load_manual_aliases(alias_path)
        n = merge_aliases_into_rows(rows, manual)
        print(f"manual_aliases: merged_codes={n}")
        total_merged += n

    # 2. KCB Vietnamese names
    if args.kcb_path:
        kcb_path = Path(args.kcb_path)
        if kcb_path.exists():
            kcb = load_kcb_aliases(kcb_path)
            n = merge_aliases_into_rows(rows, kcb)
            print(f"kcb_vietnamese: merged_codes={n}  unique_codes={len(kcb)}")
            total_merged += n
        else:
            print(f"WARN: --kcb-path not found: {kcb_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"total_merged_codes={total_merged}  output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
