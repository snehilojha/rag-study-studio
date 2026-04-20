"""Vector store helpers."""

from __future__ import annotations

import logging
import uuid
from functools import lru_cache
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from config import settings
from services.embedder import get_embedding_dim

logger = logging.getLogger(__name__)

COLLECTION_NAME = "book_chunks"



# Client singleton

@lru_cache(maxsize=1)
def _get_client() -> QdrantClient:
    """Create Qdrant client once and cache."""
    logger.info("Connecting to Qdrant at %s", settings.QDRANT_URL)
    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
    )



# Collection management

def collection_exists() -> bool:
    """Return True if the book_chunks collection already exists."""
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    return COLLECTION_NAME in existing


def create_collection() -> None:
    """
    Create the book_chunks collection if it doesn't exist.
    Vector size is read from the embedding model — no hardcoding.
    Uses cosine distance (vectors are pre-normalized in embedder.py).
    Sparse vector config added for BM25 hybrid search.
    """
    if collection_exists():
        logger.info("Collection '%s' already exists. Skipping creation.", COLLECTION_NAME)
        return

    dim = get_embedding_dim()
    client = _get_client()

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qdrant_models.VectorParams(
            size=dim,
            distance=qdrant_models.Distance.COSINE,
        ),
        sparse_vectors_config={
            "bm25": qdrant_models.SparseVectorParams(
                modifier=qdrant_models.Modifier.IDF,  # IDF weighting for BM25
            )
        },
    )
    logger.info("Created collection '%s' with dim=%d.", COLLECTION_NAME, dim)


# Upsert

def upsert_chunks(
    book_id: int,
    chapter_id: int,
    texts: List[str],
    vectors: List[List[float]],
    page_numbers: List[int],
    chunk_indices: List[int],
    chunk_type: str = "chapter",
) -> None:
    """
    Upsert a batch of chunks into Qdrant.

    Each point stores:
      - dense vector (from embedder)
      - sparse vector (BM25 — Qdrant computes from text via IDF modifier)
      - payload: text, book_id, chapter_id, page_number, chunk_index, chunk_type

    Args:
        book_id: DB id of the book.
        chapter_id: DB id of the chapter.
        texts: Raw chunk texts (used for BM25 and stored in payload).
        vectors: Dense embeddings from embed_texts().
        page_numbers: Approximate page per chunk.
        chunk_indices: Position of each chunk within its chapter.
        chunk_type: "chapter" (Phase 1) or "topic" (Phase 2).
    """
    if not texts:
        return

    client = _get_client()

    points = []
    for text, vector, page, idx in zip(texts, vectors, page_numbers, chunk_indices):
        points.append(
            qdrant_models.PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "": vector,          # default dense vector (unnamed = primary)
                    "bm25": {},          # Qdrant fills sparse from payload text via IDF modifier
                },
                payload={
                    "text": text,
                    "book_id": book_id,
                    "chapter_id": chapter_id,
                    "page_number": page,
                    "chunk_index": idx,
                    "chunk_type": chunk_type,
                },
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info(
        "Upserted %d chunks for book_id=%d, chapter_id=%d.",
        len(points), book_id, chapter_id,
    )


# Search

def search_chunks(
    query_vector: List[float],
    book_id: Optional[int] = None,
    top_k: Optional[int] = None,
) -> List[dict]:
    """
    Hybrid search: dense (cosine) + sparse (BM25) with RRF fusion.
    Filters by book_id if provided.

    Args:
        query_vector: Dense embedding of the query from embed_query().
        book_id: If set, restrict results to this book.
        top_k: Number of results. Defaults to settings.RAG_TOP_K.

    Returns:
        List of payload dicts, ordered by relevance score descending.
        Each dict includes 'text', 'book_id', 'chapter_id', 'page_number', 'score'.
    """
    client = _get_client()
    k = top_k or settings.RAG_TOP_K

    payload_filter = None
    if book_id is not None:
        payload_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="book_id",
                    match=qdrant_models.MatchValue(value=book_id),
                )
            ]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            # Dense leg
            qdrant_models.Prefetch(
                query=query_vector,
                using="",           # default dense vector
                limit=k * 2,        # over-fetch before fusion
            ),
            # Sparse leg — Qdrant handles BM25 internally via IDF modifier
            qdrant_models.Prefetch(
                query=qdrant_models.SparseVector(indices=[], values=[]),
                using="bm25",
                limit=k * 2,
            ),
        ],
        query=qdrant_models.FusionQuery(fusion=qdrant_models.Fusion.RRF),
        limit=k,
        query_filter=payload_filter,
        with_payload=True,
    ).points

    output = []
    for point in results:
        payload = point.payload or {}
        payload["score"] = point.score
        output.append(payload)

    return output

# Delete


def delete_book_chunks(book_id: int) -> None:
    """
    Delete all chunks belonging to a book from Qdrant.
    Called when a book is deleted from the DB.

    Args:
        book_id: DB id of the book to remove.
    """
    client = _get_client()

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=qdrant_models.FilterSelector(
            filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="book_id",
                        match=qdrant_models.MatchValue(value=book_id),
                    )
                ]
            )
        ),
    )
    logger.info("Deleted all chunks for book_id=%d from Qdrant.", book_id)