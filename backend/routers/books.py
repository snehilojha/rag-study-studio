"""Books router."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlmodel import Session, select

from config import settings
from database import get_session
from models import Book, BookStatus, Chapter
from services.pdf_extractor import extract_chapters
from services.chunker import chunk_chapter
from services.embedder import embed_texts, unload_model
from services.vector_store import create_collection, upsert_chunks, delete_book_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["books"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_upload(file: UploadFile, book_id: int) -> Path:
    """Save uploaded PDF to UPLOAD_DIR/<book_id>_<filename>."""
    dest = settings.UPLOAD_DIR / f"{book_id}_{file.filename}"
    with dest.open("wb") as f:
        f.write(file.file.read())
    return dest


# ---------------------------------------------------------------------------
# POST /books — upload + full pipeline (blocking)
# ---------------------------------------------------------------------------

@router.post("/", status_code=status.HTTP_201_CREATED)
def upload_book(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> Book:
    """
    Upload a PDF book and run the full ingestion pipeline:
      1. Save PDF to disk
      2. Create Book record (status=processing)
      3. Extract chapters -> Chapter records
      4. Chunk each chapter
      5. Embed chunks
      6. Upsert to Qdrant
      7. Mark Book status=ready

    Blocking. Returns the Book record when done.
    """
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    # 1. Create Book record with placeholder path so we have an id
    book = Book(
        title=Path(file.filename).stem,
        file_path="",
        status=BookStatus.processing,
    )
    session.add(book)
    session.commit()
    session.refresh(book)

    try:
        # 2. Save file to disk now that we have the id
        file_path = _save_upload(file, book.id)
        book.file_path = str(file_path)
        session.add(book)
        session.commit()

        # 3. Extract chapters from PDF
        chapter_data_list = extract_chapters(str(file_path))
        if not chapter_data_list:
            raise ValueError("No chapters could be extracted from the PDF.")

        chapters: list[Chapter] = []
        for chapter_data in chapter_data_list:
            chapter = Chapter(
                book_id=book.id,
                title=chapter_data.title,
                order_index=chapter_data.order_index,
                start_page=chapter_data.start_page,
                end_page=chapter_data.end_page,
            )
            session.add(chapter)
            chapters.append(chapter)

        session.commit()
        for chapter in chapters:
            session.refresh(chapter)

        # 4-6. Chunk, embed, upsert per chapter
        create_collection()  # no-op if already exists

        for chapter, chapter_data in zip(chapters, chapter_data_list):
            chunks = chunk_chapter(
                text=chapter_data.text,
                start_page=chapter_data.start_page,
            )
            if not chunks:
                continue

            texts = [c.text for c in chunks]
            page_numbers = [c.page_number for c in chunks]
            chunk_indices = list(range(len(chunks)))

            vectors = embed_texts(texts)

            upsert_chunks(
                book_id=book.id,
                chapter_id=chapter.id,
                texts=texts,
                vectors=vectors,
                page_numbers=page_numbers,
                chunk_indices=chunk_indices,
            )

        # 7. Mark ready
        book.status = BookStatus.ready
        session.add(book)
        session.commit()
        session.refresh(book)

        logger.info("Book id=%d ingestion complete.", book.id)

    except Exception as exc:
        logger.exception("Ingestion failed for book id=%d: %s", book.id, exc)
        book.status = BookStatus.failed
        session.add(book)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        )

    finally:
        unload_model()  # free embedding model from RAM after job

    return book


# ---------------------------------------------------------------------------
# GET /books — list all books
# ---------------------------------------------------------------------------

@router.get("/")
def list_books(session: Session = Depends(get_session)) -> list[Book]:
    """Return all books ordered by upload date descending."""
    return session.exec(select(Book).order_by(Book.uploaded_at.desc())).all()


# ---------------------------------------------------------------------------
# GET /books/{book_id} — get single book
# ---------------------------------------------------------------------------

@router.get("/{book_id}")
def get_book(book_id: int, session: Session = Depends(get_session)) -> Book:
    """Return a single book by id. 404 if not found."""
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found.")
    return book


# ---------------------------------------------------------------------------
# DELETE /books/{book_id} — delete book + Qdrant chunks
# ---------------------------------------------------------------------------

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

    # Remove vectors from Qdrant first
    try:
        delete_book_chunks(book_id)
    except Exception as exc:
        logger.warning("Qdrant deletion failed for book_id=%d: %s", book_id, exc)
        # Don't block DB deletion if Qdrant fails — log and continue

    # Remove PDF from disk
    file_path = Path(book.file_path)
    if file_path.exists():
        file_path.unlink()
        logger.info("Deleted file: %s", file_path)

    session.delete(book)
    session.commit()
    logger.info("Deleted book id=%d.", book_id)