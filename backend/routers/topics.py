"""Topics router."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import Book, Chapter, Topic

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/topics", tags=["topics"])


class TopicWithChapter(BaseModel):
    """Topic enriched with its parent chapter metadata — used by the concept map."""
    id: int
    title: str
    order_index: int
    start_page: int
    end_page: int
    summary: Optional[str]
    chapter_id: int
    chapter_title: str
    chapter_order_index: int


# GET /topics/book/{book_id} — all topics for a book, enriched with chapter metadata

@router.get("/book/{book_id}", response_model=list[TopicWithChapter])
def list_all_topics_for_book(
    book_id: int,
    session: Session = Depends(get_session),
) -> list[TopicWithChapter]:
    """Return every topic in a book, each annotated with its chapter title and position.

    Used by the frontend concept map to build the full topic graph in a single request
    rather than making one call per chapter.
    """
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    chapters = session.exec(
        select(Chapter).where(Chapter.book_id == book_id).order_by(Chapter.order_index)
    ).all()

    result: list[TopicWithChapter] = []
    for chapter in chapters:
        topics = session.exec(
            select(Topic)
            .where(Topic.chapter_id == chapter.id)
            .order_by(Topic.order_index)
        ).all()
        for topic in topics:
            result.append(TopicWithChapter(
                id=topic.id,
                title=topic.title,
                order_index=topic.order_index,
                start_page=topic.start_page,
                end_page=topic.end_page,
                summary=topic.summary,
                chapter_id=chapter.id,
                chapter_title=chapter.title,
                chapter_order_index=chapter.order_index,
            ))

    return result


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
