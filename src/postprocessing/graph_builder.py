"""Builders for postprocessing knowledge graphs."""

from __future__ import annotations

from pathlib import Path

from src.knowledge.icd10_graph import ICD10Graph, load_icd10_graph


def build_icd10_graph(path: str | Path = "data/raw/icd10_sample.csv") -> ICD10Graph:
    """Build the ICD-10 rooted tree used by Pragmatic Graph pruning."""

    return load_icd10_graph(path)


__all__ = ["build_icd10_graph"]
