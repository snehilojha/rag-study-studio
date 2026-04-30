"""Q&A router — free-form question answering over book content."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from database import get_session
from services.qa_service import ask_question

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["qa"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class QuestionRequest(BaseModel):
    """Request body for asking a question."""
    question: str
    book_id: Optional[int] = None
    topic_id: Optional[int] = None


class Citation(BaseModel):
    """A citation referencing a specific chunk in the book."""
    text: str
    page_number: Optional[int] = None
    chapter_id: Optional[int] = None
    book_id: Optional[int] = None


class AnswerResponse(BaseModel):
    """Response returned by the Q&A endpoint."""
    answer: str
    citations: list[Citation]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/ask", response_model=AnswerResponse)
def ask(
    body: QuestionRequest,
    session: Session = Depends(get_session),
) -> AnswerResponse:
    """
    Ask a free-form question about uploaded book content.

    The answer is generated via RAG:
      1. Hybrid search (dense + BM25) retrieves candidate chunks from Qdrant.
      2. A cross-encoder reranks the candidates for precision.
      3. An LLM generates a cited answer from the top chunks.

    Request body:
    - **question** (required): The free-form question.
    - **book_id** (optional): Scope retrieval to a single book.
    - **topic_id** (optional): Provide topic title + summary as extra context.

    Returns:
      - **answer**: The generated answer with inline citations.
      - **citations**: A list of citation objects with text, page_number,
        chapter_id, and book_id.
    """
    if not body.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty.",
        )

    try:
        result = ask_question(
            question=body.question.strip(),
            session=session,
            book_id=body.book_id,
            topic_id=body.topic_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except RuntimeError as exc:
        logger.exception("Q&A generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    return AnswerResponse(
        answer=result.get("answer", ""),
        citations=[Citation(**c) for c in result.get("citations", [])],
    )
