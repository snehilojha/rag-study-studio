"""Ingestion pipeline — PDF to searchable vectors.

Makes no LLM calls. Structure comes from the PDF's table of contents and text
comes from the pages themselves, so ingesting a book is bounded by embedding
throughput rather than by an API. That matters beyond cost: the chunk-size
sweep in eval/ re-ingests the corpus once per configuration, which is only
affordable when a pass is free.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from sqlmodel import Session

from models import Book, BookStatus, Chapter, Topic
from services.chunker import chunk_pages
from services.embedder import embed_texts
from services.pdf_extractor import extract_pages, extract_structure
from services.vector_store import create_collection, upsert_chunks

logger = logging.getLogger(__name__)

# Called with (stage, current, total) so callers can show progress.
ProgressFn = Callable[[str, int, int], None]


def _noop(stage: str, current: int, total: int) -> None:
    pass


def ingest_book(
    book: Book,
    session: Session,
    *,
    progress: ProgressFn = _noop,
) -> Book:
    """Run the full pipeline for a saved Book row and mark it ready.

    The Book must already exist with `file_path` pointing at a readable PDF.
    On failure the row is marked `failed` and the exception propagates.
    """
    file_path = book.file_path
    if not file_path or not Path(file_path).exists():
        raise FileNotFoundError(f"Book {book.id} has no readable file at {file_path!r}")

    try:
        book.status = BookStatus.processing
        session.add(book)
        session.commit()

        # 1. Structure, straight from the TOC.
        progress("structure", 0, 1)
        structure = extract_structure(file_path)
        book.structure_source = structure.source
        logger.info(
            "book_id=%d: %d chapters, %d topics (%s)",
            book.id, len(structure.chapters), structure.topic_count, structure.source,
        )

        chapters: list[Chapter] = []
        for chapter_data in structure.chapters:
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

        for chapter, chapter_data in zip(chapters, structure.chapters):
            for topic_data in chapter_data.topics:
                session.add(Topic(
                    chapter_id=chapter.id,
                    title=topic_data.title,
                    order_index=topic_data.order_index,
                    start_page=topic_data.start_page,
                    end_page=topic_data.end_page,
                ))
        session.commit()
        progress("structure", 1, 1)

        # 2. Chunk, embed, upsert — per chapter.
        create_collection()
        total = len(chapters)
        chunk_total = 0

        for i, (chapter, chapter_data) in enumerate(zip(chapters, structure.chapters), start=1):
            progress("embed", i, total)

            pages = extract_pages(file_path, chapter_data.start_page, chapter_data.end_page)
            chunks = chunk_pages(pages, book_id=book.id, chapter_id=chapter.id)
            if not chunks:
                logger.debug("book_id=%d chapter %d: no text, skipping.", book.id, i)
                continue

            texts = [c.text for c in chunks]
            upsert_chunks(
                book_id=book.id,
                chapter_id=chapter.id,
                texts=texts,
                vectors=embed_texts(texts),
                page_numbers=[c.page_number for c in chunks],
                chunk_indices=[c.chunk_index for c in chunks],
            )
            chunk_total += len(chunks)

        if chunk_total == 0:
            # `ready` with an empty index is the failure that produced a library
            # of unsearchable books. Refuse to claim it.
            raise ValueError(
                "No text could be extracted from this PDF — it may be scanned images."
            )

        book.status = BookStatus.ready
        session.add(book)
        session.commit()
        session.refresh(book)

        logger.info("book_id=%d ingested: %d chunks.", book.id, chunk_total)
        progress("done", total, total)
        return book

    except Exception:
        logger.exception("Ingestion failed for book_id=%s", book.id)
        book.status = BookStatus.failed
        session.add(book)
        session.commit()
        raise
