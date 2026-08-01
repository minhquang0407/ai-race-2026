"""Command-line entry point for the end-to-end medical extraction pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.extraction import ExtractionPipeline, FakeExtractor, LLMExtractor, SemanticChunker
from src.retrieval import CandidateRetriever
from src.utils.io_utils import read_text_files, write_entities_json


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Medical Ontological Reasoning AI pipeline")
    parser.add_argument("--input-dir", default="input", help="Directory containing .txt files")
    parser.add_argument("--output-dir", default="output", help="Directory for .json outputs")
    parser.add_argument(
        "--extractor",
        choices=("fake", "llm"),
        default="fake",
        help="Use fake extractor for fast tests or llm for Qwen inference",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional max number of files to process")
    parser.add_argument("--safe", action="store_true", help="Write [] instead of aborting when one file fails")
    parser.add_argument("--model-id", default="Qwen/Qwen2.5-7B-Instruct", help="HuggingFace model id for --extractor llm")
    parser.add_argument("--icd-path", default="data/raw/icd10_sample.csv", help="CSV path for ICD-10 knowledge data")
    parser.add_argument("--rxnorm-path", default="data/raw/rxnorm_sample.csv", help="CSV path for RxNorm knowledge data")
    return parser


def build_extractor(kind: str, model_id: str):
    if kind == "fake":
        return FakeExtractor()
    if kind == "llm":
        return LLMExtractor(model_id=model_id)
    raise ValueError(f"unknown extractor: {kind}")


def process_file(input_path: Path, output_path: Path, pipeline: ExtractionPipeline, retriever: CandidateRetriever) -> int:
    source_text = input_path.read_text(encoding="utf-8")
    entities = pipeline.extract(source_text)
    entities = retriever.retrieve_for_entities(entities)
    write_entities_json(output_path, entities)
    return len(entities)


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    files = read_text_files(input_dir, limit=args.limit)
    if not files:
        print(f"No .txt files found in {input_dir}", file=sys.stderr)
        return 1

    extractor = build_extractor(args.extractor, args.model_id)
    pipeline = ExtractionPipeline(
        chunker=SemanticChunker(
            target_size=600,
            min_size=300,
            max_size=800,
            overlap_chars=0,
            no_split_below=1500,
        ),
        extractor=extractor,
    )
    retriever = CandidateRetriever.from_data(icd_path=args.icd_path, rxnorm_path=args.rxnorm_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    for input_path in files:
        output_path = output_dir / f"{input_path.stem}.json"
        try:
            count = process_file(input_path, output_path, pipeline, retriever)
            print(f"{input_path.name} -> {output_path.name}: {count} entities")
        except Exception as exc:
            if not args.safe:
                raise
            write_entities_json(output_path, [])
            print(f"{input_path.name} failed: {exc}; wrote []", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
