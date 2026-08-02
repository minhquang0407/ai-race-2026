"""Pre-build and cache ICD embedding index for dense retrieval.

Run this once to avoid recomputing embeddings on every pipeline start.
After this, set ENABLE_DENSE_SEARCH=1 to activate dense retrieval.

Usage:
    python scripts\build_dense_index.py `
        --icd-path data/raw/icd10_full.csv `
        --cache data/processed/icd_dense_embeddings.npz `
        --model cambridgeltl/SapBERT-from-PubMedBERT-fulltext `
        --batch-size 256

Per pj_document.md (Section II.2), SapBERT (biomedical bi-encoder) is the
recommended dense model. Combined with English query expansion, it routes
Vietnamese diagnoses through English to correct ICD nodes.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pre-build ICD dense embedding cache")
    parser.add_argument("--icd-path", default="data/raw/icd10_full.csv")
    parser.add_argument(
        "--cache",
        default="data/processed/icd_dense_embeddings.npz",
        help="Output .npz file path",
    )
    parser.add_argument(
        "--model",
        default="cambridgeltl/SapBERT-from-PubMedBERT-fulltext",
        help="HuggingFace model name for sentence-transformers",
    )
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--force", action="store_true", help="Recompute even if cache exists")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cache_path = Path(args.cache)

    if cache_path.exists() and not args.force:
        print(f"cache already exists: {cache_path}")
        print("Use --force to recompute.")
        return 0

    # Load ICD documents
    import numpy as np
    from sentence_transformers import SentenceTransformer

    from src.knowledge.icd10_graph import load_icd10_graph
    from src.retrieval.bm25_search import BM25Document

    print(f"loading ICD graph from {args.icd_path} ...")
    icd_graph = load_icd10_graph(args.icd_path)
    documents: list[BM25Document] = [
        BM25Document(
            id=code,
            text=" ".join([code, name, *aliases]),
            aliases=(name, *aliases),
        )
        for code, name, aliases in icd_graph.iter_search_documents()
        if not code.startswith(("CHAPTER_", "SECTION_"))
    ]
    print(f"documents: {len(documents)}")

    # Build corpus text
    corpus = [" ".join(filter(None, [doc.text, *doc.aliases])) for doc in documents]

    # Load model
    print(f"loading model: {args.model} ...")
    model = SentenceTransformer(args.model)

    # Encode
    print(f"encoding {len(corpus)} documents with batch_size={args.batch_size} ...")
    t0 = time.time()
    embeddings = model.encode(
        corpus,
        show_progress_bar=True,
        batch_size=args.batch_size,
        convert_to_numpy=True,
    )
    elapsed = time.time() - t0
    print(f"encoding done in {elapsed:.1f}s  shape={embeddings.shape}")

    # Save
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(str(cache_path), embeddings=embeddings, model_name=args.model)
    size_mb = cache_path.stat().st_size / 1024 / 1024
    print(f"saved {cache_path}  ({size_mb:.1f} MB)")

    # Quick sanity check
    q = "irritable bowel syndrome"
    q_emb = model.encode([q], convert_to_numpy=True)[0]
    norms = np.linalg.norm(embeddings, axis=1)
    norms = np.where(norms == 0, 1e-9, norms)
    q_norm = float(np.linalg.norm(q_emb))
    sims = (embeddings @ q_emb) / (norms * q_norm)
    top3 = np.argsort(-sims)[:3]
    print(f"\nsanity check: '{q}' top-3:")
    for idx in top3:
        print(f"  [{documents[int(idx)].id}] {documents[int(idx)].text[:80]}  sim={sims[int(idx)]:.3f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
