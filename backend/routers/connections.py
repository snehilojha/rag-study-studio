"""Connections router — book-level concept edge queries."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import Book, Chapter, ConceptEdge, Topic

router = APIRouter(prefix="/connections", tags=["connections"])


class ConnectionResponse(BaseModel):
    id: int
    source_topic_id: int
    source_topic_title: str
    source_chapter_id: int
    source_chapter_title: str
    target_topic_id: int
    target_topic_title: str
    target_chapter_id: int
    target_chapter_title: str
    edge_type: str


@router.get("/book/{book_id}", response_model=list[ConnectionResponse])
def list_connections_for_book(
    book_id: int,
    session: Session = Depends(get_session),
) -> list[ConnectionResponse]:
    """Return all persisted concept edges for a book in a single DB read.

    Called once when BookMap loads. New edges are added as users visit individual
    topics (via GET /study/connections/:topicId), so this list grows over time.
    """
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Fetch all chapter IDs for this book
    chapters = session.exec(
        select(Chapter).where(Chapter.book_id == book_id)
    ).all()
    chapter_ids = {ch.id for ch in chapters}
    chapter_by_id = {ch.id: ch for ch in chapters}

    if not chapter_ids:
        return []

    # Fetch all topics that belong to this book
    topics = session.exec(
        select(Topic).where(Topic.chapter_id.in_(chapter_ids))  # type: ignore[attr-defined]
    ).all()
    topic_ids = {t.id for t in topics}
    topic_by_id = {t.id: t for t in topics}

    if not topic_ids:
        return []

    # Fetch all edges where both endpoints belong to this book
    edges = session.exec(
        select(ConceptEdge).where(
            ConceptEdge.source_topic_id.in_(topic_ids)  # type: ignore[attr-defined]
        )
    ).all()

    result: list[ConnectionResponse] = []
    for edge in edges:
        src = topic_by_id.get(edge.source_topic_id)
        tgt = topic_by_id.get(edge.target_topic_id)
        # Skip if target is outside this book (shouldn't happen, but guard anyway)
        if not src or not tgt:
            continue

        src_chapter = chapter_by_id.get(src.chapter_id)
        tgt_chapter = chapter_by_id.get(tgt.chapter_id)
        if not src_chapter or not tgt_chapter:
            continue

        result.append(ConnectionResponse(
            id=edge.id,
            source_topic_id=src.id,
            source_topic_title=src.title,
            source_chapter_id=src_chapter.id,
            source_chapter_title=src_chapter.title,
            target_topic_id=tgt.id,
            target_topic_title=tgt.title,
            target_chapter_id=tgt_chapter.id,
            target_chapter_title=tgt_chapter.title,
            edge_type=edge.edge_type.value,
        ))

    return result
