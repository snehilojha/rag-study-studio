"""Topics router."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models import Chapter, Topic

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/topics", tags=["topics"])


# GET /topics/{chapter_id} — list all topics for a chapter

@router.get("/{chapter_id}")
def list_topics(
    chapter_id: int,
    session: Session = Depends(get_session),
) -> list[Topic]:
    """List all topics for a given chapter, ordered by their position."""
    chapter = session.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found",
        )
    return session.exec(
        select(Topic)
        .where(Topic.chapter_id == chapter_id)
        .order_by(Topic.order_index)
    ).all()


# GET /topics/{chapter_id}/{topic_id} — get a single topic

@router.get("/{chapter_id}/{topic_id}")
def get_topic(
    chapter_id: int,
    topic_id: int,
    session: Session = Depends(get_session),
) -> Topic:
    """Get a single topic by ID, scoped to its parent chapter."""
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )
    if topic.chapter_id != chapter_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found for this chapter",
        )
    return topic
