"""Smoke-check ICD/RxNorm retrieval quality without running the LLM.

Examples:
    python scripts/build_knowledge_smoke_report.py
    python scripts/build_knowledge_smoke_report.py --icd-path data/raw/icd10_full.csv --rxnorm-path data/raw/rxnorm_full.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.retrieval import CandidateRetriever


DEFAULT_ICD_QUERIES = [
    "Kawasaki",
    "bệnh Kawasaki",
    "hội chứng Parkinson",
    "viêm dạ dày ruột do virus",
    "loét tá tràng",
    "thiếu men G6PD",
    "sỏi thận",
]

DEFAULT_RXNORM_QUERIES = [
    "aspirin",
    "ceftriaxone",
    "levothyroxine",
    "albuterol",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke-check knowledge retrieval quality")
    parser.add_argument("--icd-path", default="data/raw/icd10_sample.csv", help="ICD CSV path")
    parser.add_argument("--rxnorm-path", default="data/raw/rxnorm_sample.csv", help="RxNorm CSV path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    for path in (args.icd_path, args.rxnorm_path):
        if not Path(path).exists():
            raise FileNotFoundError(f"Knowledge data file not found: {path}")

    retriever = CandidateRetriever.from_data(icd_path=args.icd_path, rxnorm_path=args.rxnorm_path)

    print("# Knowledge Smoke Report")
    print()
    print(f"ICD nodes: {retriever.icd_graph.graph.number_of_nodes()}")
    print(f"RxNorm concepts: {len(retriever.rxnorm_index.concepts)}")
    print()

    print("## ICD queries")
    for query in DEFAULT_ICD_QUERIES:
        candidates = retriever.retrieve_icd_candidates(query)
        labels = [f"{code}:{retriever.icd_graph.name(code)}" for code in candidates]
        print(f"- {query!r} -> {labels}")
    print()

    print("## RxNorm queries")
    for query in DEFAULT_RXNORM_QUERIES:
        candidates = retriever.retrieve_rxnorm_candidates(query)
        labels = [f"{rxcui}:{retriever.rxnorm_index.by_rxcui[rxcui].name}" for rxcui in candidates]
        print(f"- {query!r} -> {labels}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
