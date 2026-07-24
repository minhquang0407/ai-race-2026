"""ICD-10 hierarchy graph utilities.

ICD-10 is naturally modeled as a rooted directed tree:
ROOT -> chapter -> block -> category -> detailed code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import networkx as nx

from .loaders import read_csv_rows


@dataclass(frozen=True)
class ICD10Node:
    code: str
    name: str
    parent_code: str | None
    level: int


class ICD10Graph:
    """Small wrapper around a NetworkX DiGraph for ICD-10 reasoning."""

    def __init__(self, graph: nx.DiGraph, root_code: str = "ROOT") -> None:
        if root_code not in graph:
            raise ValueError(f"root node {root_code!r} is missing")
        if not nx.is_arborescence(graph):
            raise ValueError("ICD-10 graph must be a directed rooted tree/arborescence")
        self.graph = graph
        self.root_code = root_code
        self._depth_cache = nx.single_source_shortest_path_length(graph, root_code)

    @classmethod
    def from_csv(cls, path: str | Path, root_code: str = "ROOT") -> "ICD10Graph":
        graph = nx.DiGraph()
        for row in read_csv_rows(path):
            code = row["code"].strip()
            parent_code = (row.get("parent_code") or "").strip() or None
            graph.add_node(
                code,
                name=row.get("name", "").strip(),
                level=int(row.get("level") or 0),
                parent_code=parent_code,
            )
            if parent_code:
                graph.add_edge(parent_code, code)
        return cls(graph=graph, root_code=root_code)

    def has_code(self, code: str) -> bool:
        return code in self.graph

    def name(self, code: str) -> str:
        return self.graph.nodes[code].get("name", "")

    def depth(self, code: str) -> int:
        self._require_code(code)
        return self._depth_cache[code]

    def ancestors(self, code: str) -> list[str]:
        self._require_code(code)
        path = nx.shortest_path(self.graph, self.root_code, code)
        return path[:-1]

    def path_to_root(self, code: str) -> list[str]:
        self._require_code(code)
        return nx.shortest_path(self.graph, self.root_code, code)

    def lowest_common_ancestor(self, left: str, right: str) -> str:
        self._require_code(left)
        self._require_code(right)
        left_path = self.path_to_root(left)
        right_path = self.path_to_root(right)
        lca = self.root_code
        for left_node, right_node in zip(left_path, right_path):
            if left_node != right_node:
                break
            lca = left_node
        return lca

    def distance(self, left: str, right: str) -> int:
        lca = self.lowest_common_ancestor(left, right)
        return self.depth(left) + self.depth(right) - 2 * self.depth(lca)

    def wu_palmer_similarity(self, left: str, right: str) -> float:
        lca = self.lowest_common_ancestor(left, right)
        denominator = self.depth(left) + self.depth(right)
        if denominator == 0:
            return 1.0
        return (2 * self.depth(lca)) / denominator

    def ontology_penalty(self, left: str, right: str, lambda_: float = 0.7) -> float:
        import math

        return math.exp(-lambda_ * (1 - self.wu_palmer_similarity(left, right)))

    def _require_code(self, code: str) -> None:
        if code not in self.graph:
            raise KeyError(f"unknown ICD-10 code: {code}")


def load_icd10_graph(path: str | Path = "data/raw/icd10_sample.csv") -> ICD10Graph:
    return ICD10Graph.from_csv(path)


__all__ = ["ICD10Graph", "ICD10Node", "load_icd10_graph"]
