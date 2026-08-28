"""Text chunking.

Pages are tokenized into one continuous stream with a parallel token-to-page
map, then a window slides across it. Two consequences:

  - Overlap survives page boundaries, so a passage split across a page break
    still produces a chunk containing all of it.
  - Every chunk records the page it actually started on, because the map is
    consulted at the window's start index. The previous implementation
    incremented a counter per chunk, which made every citation fiction.

CHUNK_SIZE and CHUNK_OVERLAP are counted in TOKENS, using the embedding
model's own tokenizer, so the configured size is the size the model sees.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

# Windows shorter than this are trailing scraps, not passages.
MIN_CHUNK_TOKENS = 20


@dataclass
class ChunkData:
    """One embeddable passage and where it came from."""
    text: str
    book_id: int
    chapter_id: int
    page_number: int
    chunk_index: int
    topic_id: Optional[int] = None


def chunk_pages(
    pages: list[tuple[int, str]],
    *,
    book_id: int,
    chapter_id: int,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[ChunkData]:
    """Split (page_number, text) pairs into overlapping token windows.

    Args:
        pages: Inclusive page range from pdf_extractor.extract_pages().
        book_id: Owning book.
        chapter_id: Owning chapter.
        chunk_size: Tokens per chunk. Defaults to settings.CHUNK_SIZE.
        chunk_overlap: Tokens shared between neighbours. Defaults to settings.

    Returns:
        Chunks in document order, each carrying the page it starts on.
    """
    from services.embedder import get_tokenizer

    size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
    overlap = chunk_overlap if chunk_overlap is not None else settings.CHUNK_OVERLAP

    if size <= 0:
        raise ValueError(f"chunk_size must be positive, got {size}")
    if overlap >= size:
        raise ValueError(f"chunk_overlap ({overlap}) must be smaller than chunk_size ({size})")

    stride = size - overlap
    tokenizer = get_tokenizer()

    # Global token stream. Each token records the page it came from and its
    # character span within that page, so a chunk's text is sliced out of the
    # source rather than decoded back from token ids.
    token_pages: list[int] = []
    token_spans: list[tuple[int, int]] = []
    page_text: dict[int, str] = {}
    token_count = 0

    for page_number, text in pages:
        if not text or not text.strip():
            continue
        encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
        offsets = encoded["offset_mapping"]
        if not offsets:
            continue
        page_text[page_number] = text
        token_pages.extend([page_number] * len(offsets))
        token_spans.extend(offsets)
        token_count += len(offsets)

    if not token_count:
        return []

    chunks: list[ChunkData] = []
    for start in range(0, token_count, stride):
        end = min(start + size, token_count)
        if end - start < MIN_CHUNK_TOKENS:
            continue  # trailing scrap

        text = _slice_source(token_pages, token_spans, page_text, start, end)
        if not text:
            continue

        chunks.append(ChunkData(
            text=text,
            book_id=book_id,
            chapter_id=chapter_id,
            page_number=token_pages[start],
            chunk_index=len(chunks),
        ))

    logger.debug(
        "chapter_id=%d: %d tokens over %d pages -> %d chunks (size=%d, overlap=%d)",
        chapter_id, token_count, len(pages), len(chunks), size, overlap,
    )
    return chunks


def _slice_source(
    token_pages: list[int],
    token_spans: list[tuple[int, int]],
    page_text: dict[int, str],
    start: int,
    end: int,
) -> str:
    """Cut [start, end) out of the source text the tokens came from.

    A window can span pages, so it is sliced per page — from the first token's
    start offset to the last token's end offset — and the pieces are rejoined.
    """
    pieces: list[str] = []
    i = start
    while i < end:
        page = token_pages[i]
        j = i
        while j < end and token_pages[j] == page:
            j += 1
        first_char = token_spans[i][0]
        last_char = token_spans[j - 1][1]
        pieces.append(page_text[page][first_char:last_char])
        i = j
    return "\n".join(p.strip() for p in pieces if p.strip()).strip()
