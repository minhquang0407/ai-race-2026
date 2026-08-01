"""Convert RxNorm RXNCONSO.RRF to the project CSV schema.

Input:  RXNCONSO.RRF from RxNorm Prescribable/Full release.
Output: rxcui,name,tty,synonyms

Example:
    python scripts/convert_rxnorm_rrf.py --input data/raw/RxNorm/rrf/RXNCONSO.RRF --output data/raw/rxnorm_full.csv
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

# RXNCONSO.RRF columns, compatible with UMLS/RxNorm RRF convention.
COL_RXCUI = 0
COL_LAT = 1
COL_TTY = 12
COL_STR = 14
COL_SUPPRESS = 16

TTY_PRIORITY = {
    "IN": 0,    # Ingredient
    "MIN": 1,   # Multiple ingredients
    "PIN": 2,   # Precise ingredient
    "BN": 3,    # Brand name
    "SCD": 4,   # Semantic clinical drug
    "SBD": 5,   # Semantic branded drug
    "GPCK": 6,
    "BPCK": 7,
}

SUPPRESSED_VALUES = {"Y", "O"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert RXNCONSO.RRF to rxnorm_full.csv")
    parser.add_argument("--input", default="data/raw/RxNorm/rrf/RXNCONSO.RRF", help="Path to RXNCONSO.RRF")
    parser.add_argument("--output", default="data/raw/rxnorm_full.csv", help="Output CSV path")
    parser.add_argument("--include-suppressed", action="store_true", help="Include suppressed/obsolete terms")
    return parser


def tty_rank(tty: str) -> int:
    return TTY_PRIORITY.get(tty, 99)


def main() -> int:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    terms_by_rxcui: dict[str, list[tuple[str, str]]] = defaultdict(list)

    with input_path.open("r", encoding="utf-8", errors="replace", newline="") as file:
        for line in file:
            parts = line.rstrip("\n").split("|")
            if len(parts) <= COL_SUPPRESS:
                continue
            if parts[COL_LAT] != "ENG":
                continue
            if not args.include_suppressed and parts[COL_SUPPRESS] in SUPPRESSED_VALUES:
                continue
            rxcui = parts[COL_RXCUI].strip()
            tty = parts[COL_TTY].strip()
            text = " ".join(parts[COL_STR].strip().split())
            if rxcui and text:
                terms_by_rxcui[rxcui].append((tty, text))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=["rxcui", "name", "tty", "synonyms"])
        writer.writeheader()
        for rxcui in sorted(terms_by_rxcui, key=lambda item: int(item) if item.isdigit() else item):
            terms = terms_by_rxcui[rxcui]
            # Deduplicate while preserving best ranking.
            unique: dict[str, str] = {}
            for tty, text in sorted(terms, key=lambda item: (tty_rank(item[0]), len(item[1]), item[1].casefold())):
                unique.setdefault(text.casefold(), text)
            ranked = sorted(
                [(tty, text) for tty, text in terms if text.casefold() in unique],
                key=lambda item: (tty_rank(item[0]), len(item[1]), item[1].casefold()),
            )
            name_tty, name = ranked[0]
            synonyms = [text for text in unique.values() if text != name]
            writer.writerow(
                {
                    "rxcui": rxcui,
                    "name": name,
                    "tty": name_tty,
                    "synonyms": "|".join(synonyms[:100]),
                }
            )

    print(f"concepts={len(terms_by_rxcui)} output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
