"""Study router — interactive AI-generated study content for topics."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from database import get_session
from models import Topic
from services.rag_service import get_theory, get_practical, get_connections

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/study", tags=["study"])


# GET /study/theory/{topic_id} — theory content

@router.get("/theory/{topic_id}")
def study_theory(
    topic_id: int,
    session: Session = Depends(get_session),
) -> dict:
    """Get a thorough theoretical explanation for a topic.

    Returns JSON with keys:
      - explanation (str): full explanation from first principles
      - key_points (list[str]): core takeaways
      - definitions (list[dict]): term/definition pairs
    """
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )
    try:
        return get_theory(topic_id, session)
    except (ValueError, RuntimeError) as exc:
        logger.exception("Failed to generate theory for topic %d", topic_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


# GET /study/practical/{topic_id} — practical content

@router.get("/practical/{topic_id}")
def study_practical(
    topic_id: int,
    session: Session = Depends(get_session),
) -> dict:
    """Get practical examples and applications for a topic.

    Returns JSON with keys:
      - overview (str): how the topic is applied in practice
      - examples (list[dict]): concrete examples with steps
      - tips (list[str]): practical tips
    """
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )
    try:
        return get_practical(topic_id, session)
    except (ValueError, RuntimeError) as exc:
        logger.exception("Failed to generate practical content for topic %d", topic_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


# GET /study/connections/{topic_id} — concept graph connections

@router.get("/connections/{topic_id}")
def study_connections(
    topic_id: int,
    session: Session = Depends(get_session),
) -> list:
    """Get validated concept-graph connections for a topic.

    Returns a list of connection dicts with keys:
      - source_topic (str)
      - target_topic (str)
      - relationship (str): prerequisite | extension | application | contrast
      - valid (bool)
      - reason (str)
    """
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )
    try:
        return get_connections(topic_id, session)
    except (ValueError, RuntimeError) as exc:
        logger.exception("Failed to generate connections for topic %d", topic_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
