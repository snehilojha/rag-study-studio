"""PDF extraction — book structure read from the embedded table of contents.

The TOC is parsed, not inferred. Where it is unusable the book is presented
flat and says so, rather than a hierarchy being invented for it.

`doc.get_toc()` returns [[level, title, page], ...] with 1-based pages, or -1
where the entry has no destination. Both cases occur in real files: ISLR ships
12 correct chapter titles with every page set to 0, and Burkov's outline covers
only its preface. Those are detectable, which is the whole argument for reading
structure instead of generating it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import fitz  # PyMuPDF
import pdfplumber

logger = logging.getLogger(__name__)

# A TOC level needs at least this many entries to be a plausible chapter list.
MIN_CHAPTERS = 3
# ...and its entries must span at least this fraction of the book. Burkov's
# outline describes 2 of 152 pages; that is a preface, not a structure.
MIN_COVERAGE = 0.25

SOURCE_TOC = "toc"
SOURCE_FLAT = "flat"


@dataclass
class TopicData:
    """A second-level TOC entry, nested under a chapter."""
    title: str
    order_index: int
    start_page: int
    end_page: int


@dataclass
class ChapterData:
    """A top-level TOC entry and the topics beneath it."""
    title: str
    order_index: int
    start_page: int
    end_page: int
    topics: list[TopicData] = field(default_factory=list)


@dataclass
class BookStructure:
    """Parsed structure, plus how it was arrived at."""
    chapters: list[ChapterData]
    source: str  # SOURCE_TOC | SOURCE_FLAT
    page_count: int

    @property
    def is_flat(self) -> bool:
        return self.source == SOURCE_FLAT

    @property
    def topic_count(self) -> int:
        return sum(len(c.topics) for c in self.chapters)


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

def extract_structure(file_path: str) -> BookStructure:
    """Build chapters and topics from the PDF's own table of contents."""
    doc = fitz.open(file_path)
    try:
        page_count = doc.page_count
        toc = doc.get_toc() or []
        entries = _valid_entries(toc, page_count)

        if not entries:
            logger.info("No usable TOC entries in %s — presenting flat.", file_path)
            return _flat(page_count)

        level = _choose_chapter_level(entries, page_count)
        if level is None:
            logger.info(
                "TOC in %s has no level with >=%d entries covering >=%.0f%% of the book "
                "— presenting flat.", file_path, MIN_CHAPTERS, MIN_COVERAGE * 100,
            )
            return _flat(page_count)

        chapters = _build_chapters(entries, level, page_count)
        if len(chapters) < MIN_CHAPTERS:
            return _flat(page_count)

        logger.info(
            "Parsed %d chapters / %d topics from the TOC of %s (chapter level %d).",
            len(chapters), sum(len(c.topics) for c in chapters), file_path, level,
        )
        return BookStructure(chapters=chapters, source=SOURCE_TOC, page_count=page_count)
    finally:
        doc.close()


def _valid_entries(toc: list, page_count: int) -> list[tuple[int, str, int]]:
    """Drop entries that cannot describe a location in this document."""
    out: list[tuple[int, str, int]] = []
    for entry in toc:
        if len(entry) < 3:
            continue
        level, title, page = entry[0], (entry[1] or "").strip(), entry[2]
        if not title or not isinstance(page, int):
            continue
        if page < 1 or page > page_count:
            continue  # 0 and -1 both mean "no destination"
        out.append((level, title, page))
    return out


def _choose_chapter_level(entries: list[tuple[int, str, int]], page_count: int) -> int | None:
    """Pick the shallowest level that behaves like a chapter list.

    Not hardcoded to level 1: some files put the series or book title at level 1
    and the real chapters at level 2.
    """
    for level in sorted({e[0] for e in entries}):
        pages = [e[2] for e in entries if e[0] == level]
        if len(pages) < MIN_CHAPTERS:
            continue
        if (max(pages) - min(pages)) / page_count < MIN_COVERAGE:
            continue
        return level
    return None


def _build_chapters(
    entries: list[tuple[int, str, int]],
    chapter_level: int,
    page_count: int,
) -> list[ChapterData]:
    """Walk the ordered TOC, opening a chapter at each `chapter_level` entry.

    Page ranges come from the next entry at the same level, so they are the
    book's own boundaries rather than an estimate.
    """
    topic_level = chapter_level + 1
    chapters: list[ChapterData] = []

    for level, title, page in entries:
        if level == chapter_level:
            chapters.append(ChapterData(
                title=title,
                order_index=len(chapters) + 1,
                start_page=page,
                end_page=page_count,  # closed below
                topics=[],
            ))
        elif level == topic_level and chapters:
            chapter = chapters[-1]
            chapter.topics.append(TopicData(
                title=title,
                order_index=len(chapter.topics) + 1,
                start_page=page,
                end_page=page_count,  # closed below
            ))

    # Close ranges against the following sibling.
    for i, chapter in enumerate(chapters):
        if i + 1 < len(chapters):
            chapter.end_page = max(chapter.start_page, chapters[i + 1].start_page - 1)
        for j, topic in enumerate(chapter.topics):
            if j + 1 < len(chapter.topics):
                topic.end_page = max(topic.start_page, chapter.topics[j + 1].start_page - 1)
            else:
                topic.end_page = max(topic.start_page, chapter.end_page)

        # A topic pointing outside its chapter means the TOC nests inconsistently;
        # drop those rather than storing a range that reads the wrong pages.
        kept = [t for t in chapter.topics if chapter.start_page <= t.start_page <= chapter.end_page]
        if len(kept) != len(chapter.topics):
            logger.debug(
                "Chapter %r: dropped %d topic(s) outside its page range.",
                chapter.title, len(chapter.topics) - len(kept),
            )
        for order, topic in enumerate(kept, start=1):
            topic.order_index = order
        chapter.topics = kept

    return chapters


def _flat(page_count: int) -> BookStructure:
    """One chapter spanning the book, no topics, flagged as such."""
    return BookStructure(
        chapters=[ChapterData(
            title="Full text",
            order_index=1,
            start_page=1,
            end_page=page_count,
            topics=[],
        )],
        source=SOURCE_FLAT,
        page_count=page_count,
    )


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

def extract_pages(file_path: str, start_page: int, end_page: int) -> list[tuple[int, str]]:
    """Return [(page_number, text)] for an inclusive, 1-based page range.

    Per-page rather than concatenated so the chunker can record which page each
    chunk actually starts on.
    """
    try:
        doc = fitz.open(file_path)
        try:
            first = max(1, start_page)
            last = min(end_page, doc.page_count)
            return [(n, doc[n - 1].get_text()) for n in range(first, last + 1)]
        finally:
            doc.close()
    except Exception:
        logger.warning("PyMuPDF failed on %s — falling back to pdfplumber.", file_path, exc_info=True)
        return _pages_pdfplumber(file_path, start_page, end_page)


def extract_text_for_pages(file_path: str, start_page: int, end_page: int) -> str:
    """Concatenated text for a page range. Used by the reader view."""
    return "\n".join(text for _, text in extract_pages(file_path, start_page, end_page)).strip()


def _pages_pdfplumber(file_path: str, start_page: int, end_page: int) -> list[tuple[int, str]]:
    """Text-only fallback. pdfplumber is not used for structure."""
    with pdfplumber.open(file_path) as pdf:
        first = max(1, start_page)
        last = min(end_page, len(pdf.pages))
        return [(n, pdf.pages[n - 1].extract_text() or "") for n in range(first, last + 1)]
