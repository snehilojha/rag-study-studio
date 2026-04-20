"""Embedding generation helpers."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    """Load model once and cache. Called lazily on first embed."""
    logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    logger.info("Embedding model loaded. Vector dim: %d", model.get_embedding_dimension())
    return model


def embed_texts(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Embed a list of texts. Returns list of float vectors (Qdrant-compatible).

    Args:
        texts: List of strings to embed.
        batch_size: Passed to sentence-transformers encode(). 32 is safe for CPU.

    Returns:
        List of vectors, same order as input.
    """
    if not texts:
        return []

    model = _load_model()

    embeddings: np.ndarray = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,  # cosine similarity via dot product — required for Qdrant cosine
        convert_to_numpy=True,
    )

    return embeddings.tolist()


def embed_query(text: str) -> List[float]:
    """
    Embed a single query string. Thin wrapper around embed_texts.

    Args:
        text: Query string.

    Returns:
        Single vector as a list of floats.
    """
    results = embed_texts([text])
    return results[0]


def get_embedding_dim() -> int:
    """Return the output dimension of the loaded model."""
    return _load_model().get_embedding_dimension()


def unload_model():
    """Unload model after job is done."""
    logger.info("Unloading embedding model from memory.")
    _load_model.cache_clear()