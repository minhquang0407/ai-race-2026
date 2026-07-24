"""Submission validator for competition JSON outputs."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.extraction.schema import ASSERTION_ENTITY_TYPES, CANDIDATE_ENTITY_TYPES, AssertionType, EntityType
from src.utils.io_utils import read_text_files

REQUIRED_ENTITY_KEYS = {"text", "position", "type", "assertions", "candidates"}
VALID_TYPES = {entity_type.value for entity_type in EntityType}
VALID_ASSERTIONS = {assertion.value for assertion in AssertionType}
CANDIDATE_TYPE_VALUES = {entity_type.value for entity_type in CANDIDATE_ENTITY_TYPES}
ASSERTION_TYPE_VALUES = {entity_type.value for entity_type in ASSERTION_ENTITY_TYPES}


@dataclass(frozen=True)
class ValidationIssue:
    file: str
    code: str
    message: str
    entity_index: int | None = None

    def format(self) -> str:
        location = self.file
        if self.entity_index is not None:
            location += f"[{self.entity_index}]"
        return f"{location}: {self.code}: {self.message}"


@dataclass
class ValidationReport:
    checked_files: int = 0
    valid_files: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues

    @property
    def invalid_files(self) -> int:
        return self.checked_files - self.valid_files

    def extend(self, other: "ValidationReport") -> None:
        self.checked_files += other.checked_files
        self.valid_files += other.valid_files
        self.issues.extend(other.issues)

    def summary(self) -> str:
        return (
            f"checked_files={self.checked_files}, "
            f"valid_files={self.valid_files}, "
            f"invalid_files={self.invalid_files}, "
            f"issues={len(self.issues)}"
        )


def validate_submission_file(input_path: str | Path, output_path: str | Path) -> ValidationReport:
    input_path = Path(input_path)
    output_path = Path(output_path)
    report = ValidationReport(checked_files=1)
    relative_name = output_path.name

    if not input_path.exists():
        report.issues.append(ValidationIssue(relative_name, "missing_input", f"input file not found: {input_path}"))
        return report
    if not output_path.exists():
        report.issues.append(ValidationIssue(relative_name, "missing_output", f"output file not found: {output_path}"))
        return report

    source_text = input_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.issues.append(ValidationIssue(relative_name, "invalid_json", str(exc)))
        return report

    if not isinstance(payload, list):
        report.issues.append(ValidationIssue(relative_name, "root_not_array", "submission root must be a JSON array"))
        return report

    for index, entity in enumerate(payload):
        report.issues.extend(_validate_entity(relative_name, index, entity, source_text))

    if not report.issues:
        report.valid_files = 1
    return report


def validate_submission_batch(input_dir: str | Path, output_dir: str | Path, limit: int | None = None) -> ValidationReport:
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    report = ValidationReport()
    for input_path in read_text_files(input_dir, limit=limit):
        output_path = output_dir / f"{input_path.stem}.json"
        report.extend(validate_submission_file(input_path, output_path))
    return report


def _validate_entity(file_name: str, index: int, entity: Any, source_text: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(entity, dict):
        return [ValidationIssue(file_name, "entity_not_object", "entity must be a JSON object", index)]

    keys = set(entity)
    missing = REQUIRED_ENTITY_KEYS - keys
    extra = keys - REQUIRED_ENTITY_KEYS
    if missing:
        issues.append(ValidationIssue(file_name, "missing_keys", f"missing keys: {sorted(missing)}", index))
    if extra:
        issues.append(ValidationIssue(file_name, "extra_keys", f"extra keys: {sorted(extra)}", index))

    text = entity.get("text")
    position = entity.get("position")
    entity_type = entity.get("type")
    assertions = entity.get("assertions")
    candidates = entity.get("candidates")

    if not isinstance(text, str) or text == "":
        issues.append(ValidationIssue(file_name, "invalid_text", "text must be a non-empty string", index))
    if entity_type not in VALID_TYPES:
        issues.append(ValidationIssue(file_name, "invalid_type", f"invalid type: {entity_type!r}", index))

    span = _validate_position(file_name, index, position, source_text, issues)
    if span is not None and isinstance(text, str):
        start, end = span
        if source_text[start:end] != text:
            issues.append(
                ValidationIssue(
                    file_name,
                    "span_text_mismatch",
                    f"source_text[{start}:{end}]={source_text[start:end]!r} != text={text!r}",
                    index,
                )
            )

    if not isinstance(assertions, list):
        issues.append(ValidationIssue(file_name, "invalid_assertions", "assertions must be a list", index))
    else:
        for assertion in assertions:
            if assertion not in VALID_ASSERTIONS:
                issues.append(ValidationIssue(file_name, "invalid_assertion", f"invalid assertion: {assertion!r}", index))
        if assertions and entity_type in VALID_TYPES and entity_type not in ASSERTION_TYPE_VALUES:
            issues.append(
                ValidationIssue(file_name, "assertions_not_allowed", f"assertions not allowed for type {entity_type}", index)
            )

    if not isinstance(candidates, list) or not all(isinstance(candidate, str) for candidate in candidates):
        issues.append(ValidationIssue(file_name, "invalid_candidates", "candidates must be list[str]", index))
    elif candidates and entity_type in VALID_TYPES and entity_type not in CANDIDATE_TYPE_VALUES:
        issues.append(
            ValidationIssue(file_name, "candidates_not_allowed", f"candidates not allowed for type {entity_type}", index)
        )

    return issues


def _validate_position(
    file_name: str,
    index: int,
    position: Any,
    source_text: str,
    issues: list[ValidationIssue],
) -> tuple[int, int] | None:
    if (
        not isinstance(position, list)
        or len(position) != 2
        or not all(isinstance(value, int) for value in position)
    ):
        issues.append(ValidationIssue(file_name, "invalid_position", "position must be [int, int]", index))
        return None
    start, end = position
    if start < 0 or end < 0 or start >= end or end > len(source_text):
        issues.append(
            ValidationIssue(file_name, "position_out_of_bounds", f"invalid span [{start}, {end}) for text length {len(source_text)}", index)
        )
        return None
    return start, end


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate competition submission JSON files")
    parser.add_argument("--input-dir", default="input")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-issues", type=int, default=50)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = validate_submission_batch(args.input_dir, args.output_dir, limit=args.limit)
    print(report.summary())
    for issue in report.issues[: args.max_issues]:
        print(issue.format(), file=sys.stderr)
    if len(report.issues) > args.max_issues:
        print(f"... {len(report.issues) - args.max_issues} more issues", file=sys.stderr)
    return 0 if report.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ValidationIssue",
    "ValidationReport",
    "validate_submission_batch",
    "validate_submission_file",
]
