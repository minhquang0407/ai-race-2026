"""I/O helpers for competition input and output files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from src.extraction.schema import Entity


def natural_key(path: Path) -> tuple[int, str]:
    match = re.search(r"\d+", path.stem)
    return (int(match.group()) if match else 10**9, path.name)


def read_text_files(input_dir: str | Path, limit: int | None = None) -> list[Path]:
    files = sorted(Path(input_dir).glob("*.txt"), key=natural_key)
    return files[:limit] if limit is not None else files


def entity_to_submission_dict(entity: Entity) -> dict:
    return {
        "text": entity.text,
        "type": str(entity.type),
        "candidates": [str(candidate) for candidate in entity.candidates],
        "assertions": [str(assertion) for assertion in entity.assertions],
        "position": [int(entity.position[0]), int(entity.position[1])],
    }


def write_entities_json(path: str | Path, entities: Iterable[Entity]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [entity_to_submission_dict(entity) for entity in entities]
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


__all__ = ["entity_to_submission_dict", "natural_key", "read_text_files", "write_entities_json"]
