"""Books router."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlmodel import Session, select

from config import settings
from database import get_session
from models import Book, BookStatus
from services.ingest_service import ingest_book
from services.vector_store import delete_book_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["books"])


# Helpers


def _save_upload(file: UploadFile, book_id: int) -> Path:
    """Save uploaded PDF to UPLOAD_DIR/<book_id>_<filename>."""
    dest = settings.UPLOAD_DIR / f"{book_id}_{file.filename}"
    with dest.open("wb") as f:
        f.write(file.file.read())
    return dest


# POST /books — upload + full pipeline (blocking)

@router.post("/", status_code=status.HTTP_201_CREATED)
def upload_book(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> Book:
    """
    Upload a PDF book and run the ingestion pipeline:
      1. Create the Book row, then save the PDF under its id
      2. Read chapters and topics from the PDF's table of contents
      3. Chunk each chapter into token windows, embed, upsert to Qdrant
      4. Mark the book ready

    Still blocking. No longer makes any LLM calls, so a book ingests in
    seconds rather than minutes.
    """
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    book = Book(
        title=Path(file.filename).stem,
        author="",
        file_path="",
        status=BookStatus.processing,
    )
    session.add(book)
    session.commit()
    session.refresh(book)

    file_path = _save_upload(file, book.id)
    book.file_path = str(file_path)
    session.add(book)
    session.commit()

    try:
        return ingest_book(book, session)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        )


# GET /books — list all books

@router.get("/")
def list_books(session: Session = Depends(get_session)) -> list[Book]:
    """Return all books ordered by upload date descending."""
    return session.exec(select(Book).order_by(Book.uploaded_at.desc())).all()


# GET /books/{book_id} — get single book

@router.get("/{book_id}")
def get_book(book_id: int, session: Session = Depends(get_session)) -> Book:
    """Return a single book by id. 404 if not found."""
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")
    return book


# DELETE /books/{book_id} — delete book + Qdrant chunks

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, session: Session = Depends(get_session)) -> None:
    """
    Delete a book and all associated data:
      - Qdrant chunks (delete_book_chunks)
      - Chapter records (cascades via DB relationship)
      - Book record
    """
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")

    # Vectors first. If this fails the delete is abandoned entirely: dropping
    # the row anyway is what leaves orphaned vectors in the collection, and
    # since SQLite reuses primary keys a later book inherits them and answers
    # questions from a book that is no longer in the library.
    try:
        delete_book_chunks(book_id)
    except Exception as exc:
        logger.exception("Qdrant deletion failed for book_id=%d — aborting delete", book_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not remove this book's vectors, so nothing was deleted. "
                   f"Check the vector store and retry. ({exc})",
        )

    # Remove PDF from disk
    file_path = Path(book.file_path)
    if file_path.exists():
        file_path.unlink()
        logger.info("Deleted file: %s", file_path)

    session.delete(book)
    session.commit()
    logger.info("Deleted book id=%d.", book_id)