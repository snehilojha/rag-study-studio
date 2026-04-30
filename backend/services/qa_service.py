"""Q&A service — answer free-form questions using RAG."""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

from sqlmodel import Session

from models import Book, Topic
from services.llm_client import get_llm_client
from services.vector_store import search_chunks
from services.embedder import embed_texts
from services.reranker import rerank as _rerank
from prompts.qa import QA_SYSTEM, qa_user
from prompts.query_rewrite import QUERY_REWRITE_SYSTEM, query_rewrite_user

logger = logging.getLogger(__name__)

# Small collection: over-fetch moderately then rerank sharply
_RETRIEVE_TOP_K = 12
_RERANK_TOP_K = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json(raw: str) -> dict | list:
    """Strip markdown fences and parse JSON from LLM response."""
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    return json.loads(cleaned)


def _rewrite_query(
    question: str,
    topic_context: str | None = None,
) -> str:
    """
    Rewrite the user's raw question into a standalone search query.

    Handles ambiguous phrasing like "how does the thing from chapter 3 work"
    by resolving pronouns, adding domain terminology, and producing a
    self-contained query optimal for semantic search.
    """
    llm = get_llm_client()
    raw = llm.generate(
        system=QUERY_REWRITE_SYSTEM,
        user=query_rewrite_user(question, topic_context),
        temperature=0.1,  # low — rewrite, not creative generation
    )

    try:
        result = _parse_json(raw)
        rewritten = result.get("rewritten_query", question)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Query rewrite JSON parse failed — falling back to original question")
        rewritten = question

    if not rewritten.strip():
        rewritten = question

    logger.debug("Rewritten query: %s", rewritten)
    return rewritten


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ask_question(
    question: str,
    session: Session,
    *,
    book_id: Optional[int] = None,
    topic_id: Optional[int] = None,
) -> dict:
    """
    Answer a free-form question using RAG.

    Flow:
      1. Rewrite the user's question into a standalone search query (via LLM).
      2. Embed the rewritten query and over-fetch from Qdrant (top 12).
      3. Rerank with cross-encoder for precision (top 5).
      4. Feed top chunks + original question to the LLM for a cited answer.
      5. Return answer text and citation metadata.

    Args:
        question: The user's free-form question.
        session: Active DB session.
        book_id: If set, restrict retrieval to this book's content.
        topic_id: If set, gather topic title + summary as additional context.

    Returns:
        A dict with keys:
          - answer (str): The generated answer with inline citations.
          - citations (list[dict]): Each dict has keys: text, page_number,
            chapter_id, book_id.

    Raises:
        ValueError: If book_id is given but the book doesn't exist.
        RuntimeError: If the LLM returns unparseable JSON.
    """
    # --- Validate inputs ---
    if book_id is not None:
        book = session.get(Book, book_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")

    # --- Build topic context ---
    topic_context = None
    if topic_id is not None:
        topic = session.get(Topic, topic_id)
        if topic:
            topic_context = topic.title
            if topic.summary:
                topic_context += f"\nSummary: {topic.summary}"

    # --- Rewrite the query ---
    rewritten = _rewrite_query(question, topic_context)

    # --- Embed the rewritten query, not the raw question ---
    vectors = embed_texts([rewritten])
    query_vector = vectors[0]

    # --- Retrieve from Qdrant (over-fetch) ---
    results = search_chunks(
        query_vector=query_vector,
        book_id=book_id,
        top_k=_RETRIEVE_TOP_K,
    )

    if not results:
        return {
            "answer": "I couldn't find any relevant content in the book to answer your question.",
            "citations": [],
        }

    # --- Rerank with cross-encoder (against the rewritten query) ---
    chunk_texts = [r["text"] for r in results]
    reranked_texts: list[str] = _rerank(rewritten, chunk_texts, top_k=_RERANK_TOP_K)

    # Reconstruct enriched results with payload metadata
    text_to_payload = {r["text"]: r for r in results}
    reranked: list[dict] = []
    for text in reranked_texts:
        payload = text_to_payload.get(text, {})
        reranked.append({
            "text": text,
            "page_number": payload.get("page_number"),
            "chapter_id": payload.get("chapter_id"),
            "book_id": payload.get("book_id"),
        })

    # --- Generate answer via LLM (uses original question, not rewritten) ---
    llm = get_llm_client()
    raw = llm.generate(
        system=QA_SYSTEM,
        user=qa_user(question, topic_context, reranked),
        temperature=0.3,
    )

    try:
        result = _parse_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to parse Q&A response: %s", e)
        raise RuntimeError(f"LLM returned invalid JSON: {e}") from e

    return result
