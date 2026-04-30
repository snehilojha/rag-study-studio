"""Cross-encoder reranker for retrieved chunks."""

from __future__ import annotations

import logging
from functools import lru_cache

from sentence_transformers import CrossEncoder

from config import settings

logger = logging.getLogger(__name__)

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@lru_cache(maxsize=1)
def _get_reranker() -> CrossEncoder:
    """Load cross-encoder once and keep resident."""
    logger.info("Loading reranker model: %s", RERANKER_MODEL)
    return CrossEncoder(RERANKER_MODEL)


def rerank(query: str, chunks: list[str], top_k: int | None = None) -> list[str]:
    """
    Rerank retrieved chunks by relevance to query using a cross-encoder.

    The cross-encoder reads (query, chunk) pairs together — more accurate
    than bi-encoder similarity scores but only feasible on a small candidate set.

    Args:
        query: The search query or topic title.
        chunks: Candidate chunks from Qdrant retrieval.
        top_k: Number of top chunks to return. Defaults to settings.RAG_TOP_K.

    Returns:
        Reranked chunks, best first, truncated to top_k.
    """
    if not chunks:
        return []

    k = top_k or settings.RAG_TOP_K

    reranker = _get_reranker()
    pairs = [(query, chunk) for chunk in chunks]
    scores = reranker.predict(pairs)

    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in ranked[:k]]