"""RAG service — retrieval from Qdrant + LLM generation for study content."""

import json
import logging
import re

from sqlmodel import Session

from models import Chapter, ConceptEdge, EdgeType, Topic
from services.llm_client import get_llm_client
from services.cache import get_cache, set_cache
from services.vector_store import search_chunks
from services.embedder import embed_texts
from prompts.theory import THEORY_SYSTEM, theory_user
from prompts.practical import PRACTICAL_SYSTEM, practical_user
from prompts.connections import CONNECTIONS_SYSTEM, connections_user
from services.reranker import rerank

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
    return rerank(query=topic.title, chunks=[r["text"] for r in results])
    
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

    Flow: cache check → fetch sibling topics from same book → LLM validation
    → resolve titles to IDs → persist to ConceptEdge table → cache store.

    Args:
        topic_id: DB id of the topic.
        session: Active DB session.

    Returns:
        List of validated connection dicts with keys:
        source_topic, source_topic_id, target_topic, target_topic_id,
        relationship, valid, reason.
    """
    key = _cache_key("connections", topic_id)
    cached = get_cache(key)
    if cached:
        logger.info("Cache hit: %s", key)
        return json.loads(cached)

    topic, book_id = _get_topic_with_book(topic_id, session)

    candidate_topics = _extract_candidate_topics(topic, session)

    if not candidate_topics:
        logger.info("No candidates found for topic %d — returning empty connections", topic_id)
        return []

    title_to_id: dict[str, int] = {t.title: t.id for t in candidate_topics}

    candidates = [
        {"source_topic": topic.title, "target_topic": t.title}
        for t in candidate_topics
    ]

    llm = get_llm_client()
    raw = llm.generate(
        system=CONNECTIONS_SYSTEM,
        user=connections_user(candidates),
        temperature=0.2,
    )

    try:
        result = _parse_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to parse connections response for topic %d: %s", topic_id, e)
        raise RuntimeError(f"LLM returned invalid JSON for connections: {e}") from e

    # Resolve titles to IDs, persist to DB, build enriched output
    from sqlmodel import select as sa_select

    enriched: list[dict] = []
    for conn in result:
        if not conn.get("valid"):
            continue

        tgt_title = conn.get("target_topic", "")
        tgt_id = title_to_id.get(tgt_title)
        if tgt_id is None:
            logger.warning("Could not resolve target topic '%s' to an ID — skipping", tgt_title)
            continue

        rel = conn.get("relationship", "")
        try:
            edge_type = EdgeType(rel)
        except ValueError:
            logger.warning("Unknown relationship type '%s' — skipping", rel)
            continue

        # Persist edge if it doesn't already exist (check both directions)
        existing = session.exec(
            sa_select(ConceptEdge).where(
                (
                    (ConceptEdge.source_topic_id == topic.id) &
                    (ConceptEdge.target_topic_id == tgt_id)
                ) | (
                    (ConceptEdge.source_topic_id == tgt_id) &
                    (ConceptEdge.target_topic_id == topic.id)
                )
            )
        ).first()

        if not existing:
            session.add(ConceptEdge(
                source_topic_id=topic.id,
                target_topic_id=tgt_id,
                edge_type=edge_type,
            ))

        enriched.append({
            **conn,
            "source_topic_id": topic.id,
            "target_topic_id": tgt_id,
        })

    session.commit()

    set_cache(key, json.dumps(enriched))
    return enriched


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_candidate_topics(
    current_topic: Topic,
    session: Session,
) -> list[Topic]:
    """
    Find other topics from the same book that are candidates for conceptual
    connections with the current topic. Returns Topic objects so callers have
    both titles and IDs available.
    """
    from sqlmodel import select

    chapter = current_topic.chapter
    if not chapter:
        return []

    book_chapters = session.exec(
        select(Chapter).where(Chapter.book_id == chapter.book_id)
    ).all()

    candidates: list[Topic] = []
    for ch in book_chapters:
        for t in ch.topics:
            if t.id != current_topic.id:
                candidates.append(t)

    return candidates