"""Chapters router."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models import Book, Chapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chapters", tags=["chapters"])


# GET /chapters/ - list all chapter for a book
@router.get("/{book_id}")
def list_chapters(book_id: int, session: Session = Depends(get_session)) -> list[Chapter]:
    """List all chapters for a given book."""
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return session.exec(select(Chapter).where(Chapter.book_id == book_id).order_by(Chapter.order_index)).all()


# GET /chapters/{chapter_id} - get single chapter

@router.get("/{book_id}/{chapter_id}")
def get_chapter(book_id: int,chapter_id: int, session: Session = Depends(get_session)) -> Chapter:
    """Get a single chapter by ID."""
    chapter = session.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    if chapter.book_id != book_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found for this book")
    return chapter
