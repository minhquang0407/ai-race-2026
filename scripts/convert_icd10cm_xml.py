"""Convert CDC ICD-10-CM tabular XML to project ICD CSV schema.

Example:
    python scripts/convert_icd10cm_xml.py --input data/raw/icd10cm-April-1-2026-XML/icd10c-tabular-April-1-2026.xml --output data/raw/icd10_full.csv
"""

from __future__ import annotations

import argparse
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert CDC ICD-10-CM tabular XML to icd10_full.csv")
    parser.add_argument("--input", default="data/raw/icd10cm-April-1-2026-XML/icd10c-tabular-April-1-2026.xml")
    parser.add_argument("--output", default="data/raw/icd10_full.csv")
    parser.add_argument("--aliases", default="data/raw/icd10_aliases_vi.csv", help="Optional CSV with columns code,alias")
    return parser


def child_text(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    return " ".join((child.text or "").split()) if child is not None else ""


def collect_inclusion_aliases(diag: ET.Element) -> list[str]:
    aliases: list[str] = []
    for note in diag.findall("./inclusionTerm/note"):
        text = " ".join("".join(note.itertext()).split())
        if text:
            aliases.append(text)
    return aliases


def load_alias_overrides(path: str | Path) -> dict[str, list[str]]:
    alias_path = Path(path)
    aliases: dict[str, list[str]] = defaultdict(list)
    if not alias_path.exists():
        return aliases
    with alias_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            code = (row.get("code") or "").strip()
            alias = (row.get("alias") or "").strip()
            if code and alias:
                aliases[code].append(alias)
    return aliases


def add_row(rows: list[dict[str, str]], code: str, name: str, parent_code: str, level: int, aliases: list[str] | None = None) -> None:
    rows.append(
        {
            "code": code,
            "name": name,
            "parent_code": parent_code,
            "level": str(level),
            "aliases": "|".join(dict.fromkeys(aliases or [])),
        }
    )


def walk_diag(rows: list[dict[str, str]], diag: ET.Element, parent_code: str, level: int) -> None:
    code = child_text(diag, "name")
    name = child_text(diag, "desc")
    if not code or not name:
        return
    add_row(rows, code, name, parent_code, level, collect_inclusion_aliases(diag))
    for child_diag in diag.findall("diag"):
        walk_diag(rows, child_diag, code, level + 1)


def main() -> int:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    tree = ET.parse(input_path)
    root = tree.getroot()

    rows: list[dict[str, str]] = []
    add_row(rows, "ROOT", "ICD-10-CM", "", 0)

    for chapter in root.findall("chapter"):
        chapter_number = child_text(chapter, "name")
        chapter_desc = child_text(chapter, "desc")
        chapter_code = f"CHAPTER_{chapter_number}"
        add_row(rows, chapter_code, chapter_desc, "ROOT", 1)

        for section in chapter.findall("section"):
            section_id = section.attrib.get("id", "").strip()
            section_desc = child_text(section, "desc")
            if not section_id:
                continue
            section_code = f"SECTION_{section_id}"
            add_row(rows, section_code, section_desc, chapter_code, 2)
            for diag in section.findall("diag"):
                walk_diag(rows, diag, section_code, 3)

    alias_overrides = load_alias_overrides(args.aliases)
    for row in rows:
        merged_aliases = []
        if row["aliases"]:
            merged_aliases.extend(row["aliases"].split("|"))
        merged_aliases.extend(alias_overrides.get(row["code"], []))
        row["aliases"] = "|".join(dict.fromkeys(alias for alias in merged_aliases if alias))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=["code", "name", "parent_code", "level", "aliases"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"nodes={len(rows)} output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
