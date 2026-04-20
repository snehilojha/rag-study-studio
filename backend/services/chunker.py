"""Text chunking helpers."""

from typing import Optional
from dataclasses import dataclass

from config import settings

@dataclass
class ChunkData:
    """Represents a text chunk."""
    text: str
    book_id: int
    chapter_id: int
    topic_id: Optional[int] = None
    page_number: Optional[int] = None

def chunk_chapter(text: str, chapter_id: int, book_id: int, start_page: int) -> list[ChunkData]:
    """Split chapter text into chunks of max size, with optional overlap."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    page_number = start_page

    for word in words:
        word_length = len(word) + 1 # +1 for space
        if current_length + word_length > settings.CHUNK_SIZE:
            chunk_text = " ".join(current_chunk)
            chunks.append(ChunkData(
                text=chunk_text,
                book_id=book_id,
                chapter_id=chapter_id,
                page_number=page_number
            ))
            # Start new chunk with overlap)
            overlap_words = current_chunk[-settings.CHUNK_OVERLAP:] if settings.CHUNK_OVERLAP < len(current_chunk) else current_chunk
            current_chunk = overlap_words + [word]
            current_length = sum(len(w) + 1 for w in current_chunk)
            page_number += 1 # increment page number for each new chunk (approximation)
        else:
            current_chunk.append(word)
            current_length += word_length
        
    # Flush remaining words
    if current_chunk:
        chunks.append(ChunkData(
            text=" ".join(current_chunk),
            book_id=book_id,
            chapter_id=chapter_id,
            page_number=page_number,
        ))

    return chunks