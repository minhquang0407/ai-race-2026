"""Compare two submission output directories.

Reports entity/type count changes, added/dropped entities, candidate changes, and
common suspicious ICD candidate patterns. Designed for fast iteration between
runs such as `output_llm_fullkb` and `output_llm_phase9_50`.
"""

from __future__ import annotations

import argparse
import collections
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DIAGNOSIS_TYPE = "CHẨN_ĐOÁN"


@dataclass(frozen=True)
class EntityRow:
    file: str
    text: str
    type: str
    position: tuple[int, int]
    candidates: tuple[str, ...]

    @property
    def key(self) -> tuple[str, str, str, tuple[int, int]]:
        return (self.file, self.text, self.type, self.position)

    @property
    def loose_key(self) -> tuple[str, str, str]:
        return (self.file, self.text, self.type)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare two output directories")
    parser.add_argument("--before", required=True, help="Baseline output directory")
    parser.add_argument("--after", required=True, help="New output directory")
    parser.add_argument("--report", default="data/processed/output_comparison.md")
    parser.add_argument("--limit", type=int, default=None, help="Compare only first N numbered json files")
    parser.add_argument("--max-items", type=int, default=200, help="Max rows per detailed section")
    return parser


def json_sort_key(path: Path) -> tuple[int, str]:
    try:
        return (int(path.stem), path.name)
    except ValueError:
        return (10**9, path.name)


def load_entities(directory: Path, limit: int | None = None) -> list[EntityRow]:
    files = sorted(directory.glob("*.json"), key=json_sort_key)
    if limit is not None:
        files = files[:limit]
    rows: list[EntityRow] = []
    for path in files:
        try:
            payload: Any = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(payload, dict):
            entities = payload.get("entities", [])
        else:
            entities = payload
        if not isinstance(entities, list):
            continue
        for item in entities:
            if not isinstance(item, dict):
                continue
            position = item.get("position") or [None, None]
            if len(position) != 2 or position[0] is None or position[1] is None:
                position_tuple = (-1, -1)
            else:
                position_tuple = (int(position[0]), int(position[1]))
            rows.append(
                EntityRow(
                    file=path.name,
                    text=str(item.get("text") or ""),
                    type=str(item.get("type") or ""),
                    position=position_tuple,
                    candidates=tuple(str(c) for c in (item.get("candidates") or [])),
                )
            )
    return rows


def count_by_type(rows: list[EntityRow]) -> collections.Counter[str]:
    return collections.Counter(row.type for row in rows)


def format_counter_table(before: collections.Counter[str], after: collections.Counter[str]) -> str:
    labels = sorted(set(before) | set(after))
    lines = ["| Type | Before | After | Delta |", "|---|---:|---:|---:|"]
    for label in labels:
        b = before[label]
        a = after[label]
        lines.append(f"| {label} | {b} | {a} | {a - b:+d} |")
    lines.append(f"| **TOTAL** | **{sum(before.values())}** | **{sum(after.values())}** | **{sum(after.values()) - sum(before.values()):+d}** |")
    return "\n".join(lines)


def candidate_changes(before: list[EntityRow], after: list[EntityRow]) -> list[tuple[EntityRow, tuple[str, ...]]]:
    before_map = {row.key: row.candidates for row in before}
    changes = []
    for row in after:
        old = before_map.get(row.key)
        if old is not None and old != row.candidates:
            changes.append((row, old))
    return changes


def added_dropped(before: list[EntityRow], after: list[EntityRow]) -> tuple[list[EntityRow], list[EntityRow]]:
    before_keys = {row.key for row in before}
    after_keys = {row.key for row in after}
    added = [row for row in after if row.key not in before_keys]
    dropped = [row for row in before if row.key not in after_keys]
    return added, dropped


def suspicious_rows(rows: list[EntityRow]) -> list[str]:
    suspicious: list[str] = []
    generic_texts = {"gan", "cấp", "ung thư", "hội chứng", "bệnh", "viêm"}
    procedure_prefixes = ("phẫu thuật", "cắt bỏ", "nối ", "mổ ", "đặt stent", "sinh thiết")
    for row in rows:
        norm = " ".join(row.text.casefold().split())
        if row.type == DIAGNOSIS_TYPE and norm in generic_texts:
            suspicious.append(f"- `{row.file}` generic diagnosis `{row.text}` -> `{list(row.candidates)}`")
        if row.type == DIAGNOSIS_TYPE and norm.startswith(procedure_prefixes):
            suspicious.append(f"- `{row.file}` procedure-as-diagnosis `{row.text}` -> `{list(row.candidates)}`")
        if row.type == DIAGNOSIS_TYPE and row.candidates and row.text.casefold().startswith("hội chứng") and row.candidates[0] == "G20.C" and "parkinson" not in norm:
            suspicious.append(f"- `{row.file}` syndrome mapped to Parkinson `{row.text}` -> `G20.C`")
        if row.type == DIAGNOSIS_TYPE and "mật" in norm and row.candidates and row.candidates[0] == "C73":
            suspicious.append(f"- `{row.file}` biliary/cancer text mapped to thyroid `{row.text}` -> `C73`")
    return suspicious


def render_entity_list(title: str, rows: list[EntityRow], max_items: int) -> str:
    lines = [f"## {title}", ""]
    if not rows:
        lines.append("None.")
        return "\n".join(lines)
    lines.append("| File | Text | Type | Span | Candidates |")
    lines.append("|---|---|---|---:|---|")
    for row in rows[:max_items]:
        candidates = ", ".join(row.candidates)
        lines.append(f"| {row.file} | {row.text} | {row.type} | {row.position} | {candidates} |")
    if len(rows) > max_items:
        lines.append(f"\n... truncated {len(rows) - max_items} more rows")
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    before_dir = Path(args.before)
    after_dir = Path(args.after)
    report_path = Path(args.report)

    before = load_entities(before_dir, args.limit)
    after = load_entities(after_dir, args.limit)
    added, dropped = added_dropped(before, after)
    changes = candidate_changes(before, after)
    suspicious_after = suspicious_rows(after)

    lines = [
        "# Output Comparison Report",
        "",
        f"- Before: `{before_dir}`",
        f"- After: `{after_dir}`",
        f"- Limit: `{args.limit}`",
        "",
        "## Type Counts",
        "",
        format_counter_table(count_by_type(before), count_by_type(after)),
        "",
        "## Candidate Changes",
        "",
    ]

    if changes:
        lines.extend(["| File | Text | Type | Span | Before | After |", "|---|---|---|---:|---|---|"])
        for row, old in changes[: args.max_items]:
            lines.append(
                f"| {row.file} | {row.text} | {row.type} | {row.position} | {', '.join(old)} | {', '.join(row.candidates)} |"
            )
        if len(changes) > args.max_items:
            lines.append(f"\n... truncated {len(changes) - args.max_items} more candidate changes")
    else:
        lines.append("None.")

    lines.extend(["", render_entity_list("Added Entities", added, args.max_items), "", render_entity_list("Dropped Entities", dropped, args.max_items), "", "## Suspicious After Rows", ""])
    if suspicious_after:
        lines.extend(suspicious_after[: args.max_items])
        if len(suspicious_after) > args.max_items:
            lines.append(f"\n... truncated {len(suspicious_after) - args.max_items} more suspicious rows")
    else:
        lines.append("None detected by heuristic checks.")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {report_path}")
    print(f"before={len(before)} after={len(after)} added={len(added)} dropped={len(dropped)} candidate_changes={len(changes)} suspicious_after={len(suspicious_after)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
