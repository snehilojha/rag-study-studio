"""Service for extracting topics from chapter text and saving to DB."""

import json
import logging
import re

from sqlmodel import Session

from models import Chapter, Topic
from services.llm_client import get_llm_client
from prompts.topic_extraction import TOPIC_EXTRACTION_SYSTEM, topic_extraction_user

logger = logging.getLogger(__name__)


def _parse_json_response(raw: str) -> list:
    """Strip markdown fences and parse JSON from LLM response."""
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    return json.loads(cleaned)


def extract_and_save_topics(chapter: Chapter, session: Session, chapter_text: str) -> list[Topic]:
    """Extract topics from chapter text via LLM and persist to DB.
    
    Args:
        chapter: Chapter object to extract topics from.
        chapter_text: Text content of the chapter.
        session: Active DB session.

    Returns:
        List of saved Topic objects.
    """
    if not chapter_text:
        logger.warning("Chapter %d has no content — skipping topic extraction", chapter.id)
        return []

    llm = get_llm_client()

    raw = llm.generate(
        system=TOPIC_EXTRACTION_SYSTEM,
        user=topic_extraction_user(chapter.title, chapter_text),
        temperature=0.3,  # low temperature for structured extraction
    )

    try:
        items = _parse_json_response(raw)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to parse topic extraction response for chapter %d: %s", chapter.id, e)
        return []

    topics = []
    for order_index, item in enumerate(items):
        topic = Topic(
            chapter_id=chapter.id,
            title=item["title"],
            order_index=order_index,
            start_page=item.get("start_page", 0),
            end_page=item.get("end_page", 0),
            summary=item.get("summary"),
        )
        session.add(topic)
        topics.append(topic)

    session.commit()

    for topic in topics:
        session.refresh(topic)

    logger.info("Extracted %d topics for chapter %d", len(topics), chapter.id)
    return topics