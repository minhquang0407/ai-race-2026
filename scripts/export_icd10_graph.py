"""Export ICD-10 graph artifacts for inspection/visualization."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import networkx as nx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.knowledge.icd10_graph import load_icd10_graph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export ICD graph artifacts")
    parser.add_argument("--icd-path", default="data/raw/icd10_full.csv")
    parser.add_argument("--output-dir", default="data/processed/icd10_graph")
    parser.add_argument("--sample-code", action="append", default=["M30.3", "A08.4", "D55.0", "N20.0"])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    icd = load_icd10_graph(args.icd_path)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    nodes_path = out_dir / "nodes.csv"
    with nodes_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["code", "name", "parent_code", "level", "depth", "aliases"])
        writer.writeheader()
        for code in icd.graph.nodes:
            data = icd.graph.nodes[code]
            writer.writerow(
                {
                    "code": code,
                    "name": data.get("name", ""),
                    "parent_code": data.get("parent_code") or "",
                    "level": data.get("level", ""),
                    "depth": icd.depth(code),
                    "aliases": "|".join(data.get("aliases", ())),
                }
            )

    edges_path = out_dir / "edges.csv"
    with edges_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["source", "target"])
        writer.writeheader()
        for source, target in icd.graph.edges:
            writer.writerow({"source": source, "target": target})

    graphml_path = out_dir / "icd10_graph.graphml"
    graphml = nx.DiGraph()
    for code, data in icd.graph.nodes(data=True):
        graphml.add_node(
            code,
            name=str(data.get("name", "")),
            parent_code=str(data.get("parent_code") or ""),
            level=str(data.get("level", "")),
            aliases="|".join(data.get("aliases", ())),
        )
    graphml.add_edges_from(icd.graph.edges)
    nx.write_graphml(graphml, graphml_path)

    sample_paths = {}
    for code in args.sample_code:
        if icd.has_code(code):
            sample_paths[code] = icd.path_to_root(code)

    summary = {
        "nodes": icd.graph.number_of_nodes(),
        "edges": icd.graph.number_of_edges(),
        "is_arborescence": nx.is_arborescence(icd.graph),
        "root_code": icd.root_code,
        "max_depth": max(icd.depth(code) for code in icd.graph.nodes),
        "sample_paths": sample_paths,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# ICD-10 Graph Top Levels", ""]
    for chapter in icd.graph.successors(icd.root_code):
        lines.append(f"- **{chapter}**: {icd.name(chapter)}")
        for section in list(icd.graph.successors(chapter))[:20]:
            lines.append(f"  - `{section}`: {icd.name(section)}")
    (out_dir / "top_levels.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"output_dir={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
