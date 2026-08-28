#!/usr/bin/env python
"""Ingest PDFs from the command line.

Drives the same pipeline as POST /api/books/ without going through HTTP, so a
corpus rebuild is one command and there is no request timeout to strand a book
in `processing`. Used to build the evaluation corpus, which gets rebuilt once
per configuration during a chunk-size sweep.

Usage:
    python backend/ingest.py "path/to/book.pdf" [more.pdf ...]
    python backend/ingest.py --list
    python backend/ingest.py --delete 3
    python backend/ingest.py --reset            # drop every book and its vectors
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent
# config reads .env relative to the working directory, so run from backend/.
# Command-line paths are resolved against the caller's directory first.
_CALLER_CWD = Path.cwd()

if __package__ in (None, ""):
    sys.path.insert(0, str(_BACKEND))
os.chdir(_BACKEND)


def _caller_path(arg: str) -> Path:
    """Resolve a CLI path against the directory the user actually ran from."""
    return (_CALLER_CWD / arg).resolve()

from sqlmodel import Session, select  # noqa: E402

from config import settings  # noqa: E402
from database import create_db_and_tables, engine  # noqa: E402
from models import Book, BookStatus, Chapter, Topic  # noqa: E402


def _progress(stage: str, current: int, total: int) -> None:
    if stage == "structure":
        return
    if stage == "done":
        print()
        return
    bar_width = 28
    filled = int(bar_width * current / total) if total else bar_width
    print(f"\r  embedding [{'#' * filled}{'.' * (bar_width - filled)}] "
          f"chapter {current}/{total}", end="", flush=True)


def cmd_list(session: Session) -> int:
    from services.vector_store import COLLECTION_NAME, _get_client

    books = session.exec(select(Book).order_by(Book.id)).all()
    if not books:
        print("No books.")
        return 0

    try:
        client = _get_client()
        counts = {}
        offset = None
        while True:
            pts, offset = client.scroll(COLLECTION_NAME, limit=256, offset=offset, with_payload=True)
            for p in pts:
                bid = p.payload.get("book_id")
                counts[bid] = counts.get(bid, 0) + 1
            if offset is None:
                break
    except Exception as exc:
        print(f"(vector store unreachable: {exc})")
        counts = {}

    print(f"{'id':<4}{'status':<11}{'src':<7}{'chapters':<10}{'topics':<9}{'vectors':<9}title")
    print("-" * 88)
    for b in books:
        chapters = session.exec(select(Chapter).where(Chapter.book_id == b.id)).all()
        topics = sum(
            len(session.exec(select(Topic).where(Topic.chapter_id == c.id)).all())
            for c in chapters
        )
        vectors = counts.get(b.id, 0)
        flag = " <- ready but unsearchable" if b.status == BookStatus.ready and not vectors else ""
        print(f"{b.id:<4}{b.status.value:<11}{b.structure_source:<7}"
              f"{len(chapters):<10}{topics:<9}{vectors:<9}{b.title[:38]}{flag}")

    orphans = {k: v for k, v in counts.items() if k not in {b.id for b in books}}
    if orphans:
        print(f"\n! orphaned vectors with no book row: {orphans}")
    return 0


def cmd_delete(session: Session, book_id: int) -> int:
    from services.vector_store import delete_book_chunks

    book = session.get(Book, book_id)
    if not book:
        print(f"No book with id {book_id}.", file=sys.stderr)
        return 1

    delete_book_chunks(book_id)  # vectors first — a failure here aborts
    path = Path(book.file_path) if book.file_path else None
    if path and path.exists():
        path.unlink()
    session.delete(book)
    session.commit()
    print(f"Deleted book {book_id}: {book.title}")
    return 0


def cmd_reset(session: Session) -> int:
    from services.vector_store import COLLECTION_NAME, _get_client

    books = session.exec(select(Book)).all()
    for book in books:
        session.delete(book)
    session.commit()

    try:
        client = _get_client()
        if any(c.name == COLLECTION_NAME for c in client.get_collections().collections):
            client.delete_collection(COLLECTION_NAME)
    except Exception as exc:
        print(f"(could not drop collection: {exc})", file=sys.stderr)

    for pdf in settings.UPLOAD_DIR.glob("*.pdf"):
        pdf.unlink()

    print(f"Reset: {len(books)} book(s) removed, collection dropped, uploads cleared.")
    return 0


def cmd_ingest(session: Session, paths: list[Path]) -> int:
    from services.ingest_service import ingest_book

    failures = 0
    for path in paths:
        if not path.exists():
            print(f"! {path} does not exist", file=sys.stderr)
            failures += 1
            continue

        book = Book(title=path.stem, author="", file_path="", status=BookStatus.pending)
        session.add(book)
        session.commit()
        session.refresh(book)

        dest = settings.UPLOAD_DIR / f"{book.id}_{path.name}"
        shutil.copy2(path, dest)
        book.file_path = str(dest)
        session.add(book)
        session.commit()

        print(f"[{book.id}] {path.name}")
        try:
            ingest_book(book, session, progress=_progress)
        except Exception as exc:
            print(f"\n  failed: {exc}", file=sys.stderr)
            failures += 1
            continue

        chapters = session.exec(select(Chapter).where(Chapter.book_id == book.id)).all()
        topics = sum(
            len(session.exec(select(Topic).where(Topic.chapter_id == c.id)).all())
            for c in chapters
        )
        print(f"  {len(chapters)} chapters, {topics} topics, structure={book.structure_source}")

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest PDFs into the study tool.")
    parser.add_argument("paths", nargs="*", type=_caller_path, help="PDF files to ingest")
    parser.add_argument("--list", action="store_true", help="Show books, structure, and vector counts")
    parser.add_argument("--delete", type=int, metavar="ID", help="Delete one book and its vectors")
    parser.add_argument("--reset", action="store_true", help="Delete every book and drop the collection")
    parser.add_argument("--verbose", action="store_true", help="Show pipeline logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    create_db_and_tables()

    with Session(engine) as session:
        if args.list:
            return cmd_list(session)
        if args.delete is not None:
            return cmd_delete(session, args.delete)
        if args.reset:
            return cmd_reset(session)
        if args.paths:
            return cmd_ingest(session, args.paths)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
