"""PDF extraction helpers."""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import fitz # PyMuPDF
import pdfplumber

from config import settings


@dataclass
class ChapterData:
    """Represents extracted chapter metadata."""
    title: str
    order_index: int
    start_page: int
    end_page: int


def extract_chapters(file_path: str) -> list[ChapterData]:
    """Extract chapters from a PDF file.
        Strategy: TOC first, heuristics as fallback."""
    try:
        doc = fitz.open(file_path)
        toc = doc.get_toc() # returns [[level, title, page], ...]

        if toc:
            return _chapters_from_toc(toc, doc.page_count)
        else:
            return _chapters_from_heuristics(doc)
        
    except:
        # PyMuPDF failed,fall back to pdfplumber
        return _extract_chapters_pdfplumber(file_path)

def extract_text_for_pages(file_path: str, start_page: int, end_page: int) -> str:
    """
    Extract raw text from a page range (inclusive).
    Pages are 0-indexed internally, but stored 1-indexed in DB.
    """
    try:
        doc = fitz.open(file_path)
        text = ""
        for page_num in range(start_page - 1, end_page): # convert to 0-index
            text += doc[page_num].get_text()
        return text.strip()
    except Exception:
        return _extract_text_pdfplumber(file_path, start_page, end_page)
    
# TOC based extraction

def _chapters_from_toc(toc:list, total_pages: int) -> list[ChapterData]:
    """Build chapter list from embedded TOC. Uses level-1 entries only."""
    top_level = [entry for entry in toc if entry[0] == 1] # [level, title, pages]
    chapters = []

    for i, entry in enumerate(top_level):
        _, title, start_page = entry
        end_page = (
            top_level[i+1][2] - 1
            if i + 1 < len(top_level)
            else total_pages
        )
        chapters.append(ChapterData(
            title=title.strip(),
            order_index=i+1,
            start_page=start_page,
            end_page=end_page,
        ))

    return chapters

# Heuristic-based extraction

def _chapters_from_heuristics(doc: fitz.Document) -> list[ChapterData]:
    """
    Detect chapters by checking first line of each page.
    Looks for short lines starting with 'chapter'.
    """
    chapter_pages = []

    for page_num in range(len(doc)):
        text = doc[page_num].get_text().strip()
        if not text:
            continue
        first_line = text.split("\n")[0].strip()
        if first_line.lower().startswith("chapter") and len(first_line) < 60:
            chapter_pages.append((page_num + 1, first_line))  # 1-indexed

    chapters = []
    for i, (start_page, title) in enumerate(chapter_pages):
        end_page = chapter_pages[i + 1][0] - 1 if i + 1 < len(chapter_pages) else doc.page_count
        chapters.append(ChapterData(
            title=title,
            order_index=i + 1,
            start_page=start_page,
            end_page=end_page,
        ))

    return chapters


# pdfplumber fallbacks 

def _extract_chapters_pdfplumber(file_path: str) -> list[ChapterData]:
    """Heuristic chapter detection using pdfplumber."""
    chapter_pages = []

    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            first_line = text.strip().split("\n")[0] if text.strip() else ""

            if first_line.lower().startswith("chapter") and len(first_line) < 60:
                chapter_pages.append((i + 1, first_line))  # 1-indexed

    chapters = []
    for i, (start_page, title) in enumerate(chapter_pages):
        end_page = chapter_pages[i + 1][0] - 1 if i + 1 < len(chapter_pages) else total_pages
        chapters.append(ChapterData(
            title=title,
            order_index=i + 1,
            start_page=start_page,
            end_page=end_page,
        ))

    return chapters


def _extract_text_pdfplumber(file_path: str, start_page: int, end_page: int) -> str:
    """Extract text using pdfplumber for given page range."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages[start_page - 1:end_page]:  # convert to 0-index
            text += page.extract_text() or ""
    return text.strip()