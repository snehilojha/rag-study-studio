"""RAG service — retrieval from Qdrant + LLM generation for study content."""

import json
import logging
import re

from sqlmodel import Session

from models import Topic
from services.llm_client import get_llm_client
from services.cache import get_cache, set_cache
from services.vector_store import search_chunks
from services.embedder import embed_texts
from prompts.theory import THEORY_SYSTEM, theory_user
from prompts.practical import PRACTICAL_SYSTEM, practical_user
from prompts.connections import CONNECTIONS_SYSTEM, connections_user

logger = logging.getLogger(__name__)

# Number of chunks to retrieve per topic query
TOP_K = 6


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cache_key(content_type: str, topic_id: int) -> str:
    """Build a deterministic cache key for a topic's generated content."""
    return f"{content_type}:topic_{topic_id}"


def _parse_json(raw: str) -> dict | list:
    """Strip markdown fences and parse JSON from LLM response."""
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    return json.loads(cleaned)


def _retrieve_chunks(topic: Topic, book_id: int) -> list[str]:
    """Embed topic title and retrieve relevant chunks from Qdrant."""
    vectors = embed_texts([topic.title])
    query_vector = vectors[0]

    results = search_chunks(
        query_vector=query_vector,
        book_id=book_id,
        top_k=TOP_K,
    )
    return [r["text"] for r in results]


def _get_topic_with_book(topic_id: int, session: Session) -> tuple[Topic, int]:
    """Fetch topic and resolve its book_id via chapter relationship."""
    topic = session.get(Topic, topic_id)
    if not topic:
        raise ValueError(f"Topic {topic_id} not found")
    chapter = topic.chapter
    if not chapter:
        raise ValueError(f"Topic {topic_id} has no associated chapter")
    return topic, chapter.book_id


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_theory(topic_id: int, session: Session) -> dict:
    """
    Retrieve theory content for a topic.

    Flow: cache check → Qdrant retrieval → LLM generation → cache store.

    Args:
        topic_id: DB id of the topic.
        session: Active DB session.

    Returns:
        Parsed JSON dict with keys: explanation, key_points, definitions.
    """
    key = _cache_key("theory", topic_id)
    cached = get_cache(key)
    if cached:
        logger.info("Cache hit: %s", key)
        return json.loads(cached)

    topic, book_id = _get_topic_with_book(topic_id, session)
    chunks = _retrieve_chunks(topic, book_id)

    llm = get_llm_client()
    raw = llm.generate(
        system=THEORY_SYSTEM,
        user=theory_user(topic.title, chunks),
        temperature=0.3,
    )

    try:
        result = _parse_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to parse theory response for topic %d: %s", topic_id, e)
        raise RuntimeError(f"LLM returned invalid JSON for theory: {e}") from e

    set_cache(key, json.dumps(result))
    return result


def get_practical(topic_id: int, session: Session) -> dict:
    """
    Retrieve practical content for a topic.

    Flow: cache check → Qdrant retrieval → LLM generation → cache store.

    Args:
        topic_id: DB id of the topic.
        session: Active DB session.

    Returns:
        Parsed JSON dict with keys: overview, examples, tips.
    """
    key = _cache_key("practical", topic_id)
    cached = get_cache(key)
    if cached:
        logger.info("Cache hit: %s", key)
        return json.loads(cached)

    topic, book_id = _get_topic_with_book(topic_id, session)
    chunks = _retrieve_chunks(topic, book_id)

    llm = get_llm_client()
    raw = llm.generate(
        system=PRACTICAL_SYSTEM,
        user=practical_user(topic.title, chunks),
        temperature=0.4,
    )

    try:
        result = _parse_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to parse practical response for topic %d: %s", topic_id, e)
        raise RuntimeError(f"LLM returned invalid JSON for practical: {e}") from e

    set_cache(key, json.dumps(result))
    return result


def get_connections(topic_id: int, session: Session) -> list:
    """
    Retrieve concept graph connections for a topic.

    Flow: cache check → fetch sibling topics from same book → build
    candidates via embedding similarity → LLM validation → cache store.

    Args:
        topic_id: DB id of the topic.
        session: Active DB session.

    Returns:
        List of validated connection dicts with keys:
        source_topic, target_topic, relationship, valid, reason.
    """
    key = _cache_key("connections", topic_id)
    cached = get_cache(key)
    if cached:
        logger.info("Cache hit: %s", key)
        return json.loads(cached)

    topic, book_id = _get_topic_with_book(topic_id, session)

    # Retrieve chunks for this topic to find semantically similar topics
    chunks = _retrieve_chunks(topic, book_id)

    # Build candidate connections: topics appearing in retrieved chunks
    # Use chunk metadata (chapter_id) to find related topic titles
    candidate_titles = _extract_candidate_topics(chunks, topic, session)

    if not candidate_titles:
        logger.info("No candidates found for topic %d — returning empty connections", topic_id)
        return []

    candidates = [
        {"source_topic": topic.title, "target_topic": title}
        for title in candidate_titles
    ]

    llm = get_llm_client()
    raw = llm.generate(
        system=CONNECTIONS_SYSTEM,
        user=connections_user(candidates),
        temperature=0.2,  # low — classification task, not creative
    )

    try:
        result = _parse_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to parse connections response for topic %d: %s", topic_id, e)
        raise RuntimeError(f"LLM returned invalid JSON for connections: {e}") from e

    # Filter to only valid connections
    valid = [c for c in result if c.get("valid")]

    set_cache(key, json.dumps(valid))
    return valid


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_candidate_topics(
    chunks: list[str],
    current_topic: Topic,
    session: Session,
) -> list[str]:
    """
    Find other topic titles from the same book that are candidates
    for conceptual connections with the current topic.

    Strategy: fetch all topics from the same book, exclude self,
    return their titles as candidates for LLM validation.
    Keeps it simple — LLM does the heavy lifting of deciding
    which connections are real.
    """
    from sqlmodel import select
    from models import Chapter

    chapter = current_topic.chapter
    if not chapter:
        return []

    # Get all chapters for this book
    book_chapters = session.exec(
        select(Chapter).where(Chapter.book_id == chapter.book_id)
    ).all()

    candidate_titles = []
    for ch in book_chapters:
        for t in ch.topics:
            if t.id != current_topic.id:
                candidate_titles.append(t.title)

    return candidate_titles