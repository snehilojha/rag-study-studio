"""Database and domain models."""
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import JSON, Column 

class BookStatus(str, Enum):
    """Enumeration for book processing status."""
    pending = "pending"
    processing = 'processing'
    ready = 'ready'
    failed = 'failed'

class Book(SQLModel, table=True):
    """Represents a book in the system."""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author: str
    file_path: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: BookStatus = Field(default=BookStatus.pending)

    chapters: List["Chapter"] = Relationship(back_populates="book")

class Chapter(SQLModel, table=True):
    """Represents a chapter of a book."""
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key='book.id')
    title: str
    order_index: int
    start_page: int
    end_page: int
    summary: Optional[str] = Field(default=None)

    book: Optional[Book] = Relationship(back_populates="chapters")
    topics: List["Topic"] = Relationship(back_populates="chapter")

class Topic(SQLModel, table=True):
    """Represents a topic extracted from a chapter."""
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key='chapter.id')
    title: str
    order_index: int
    start_page: int
    end_page: int
    summary: Optional[str] = Field(default=None)

    chapter: Optional[Chapter] = Relationship(back_populates="topics")
    quiz_questions: List["QuizQuestion"] = Relationship(back_populates="topic")
    outgoing_edges: List["ConceptEdge"] = Relationship(back_populates="source_topic", sa_relationship_kwargs={"foreign_keys": "[ConceptEdge.source_topic_id]"})
    incoming_edges: List["ConceptEdge"] = Relationship(back_populates="target_topic", sa_relationship_kwargs={"foreign_keys": "[ConceptEdge.target_topic_id]"})

class question_type(str, Enum):
    """Enumeration for quiz question types."""
    multiple_choice = "multiple_choice"
    true_false = "true_false"
    short_answer = "short_answer"

class QuizQuestion(SQLModel, table=True):
    """Represents a quiz question related to a topic."""
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: int = Field(foreign_key='topic.id')
    order_index: int
    question: str
    question_type: question_type
    options: Optional[List[str]] = Field(default=None, sa_column=Column(JSON)) # only for multiple choice
    correct_answer: Optional[str] = Field(default=None) # for multiple choice and true/false, store the correct option; for short answer, store the expected answer
    explanation: Optional[str] = Field(default=None) # explanation for the correct answer

    topic: Optional[Topic] = Relationship(back_populates='quiz_questions')
    attempts: List["QuizAttempt"] = Relationship(back_populates="quiz_question")

class QuizAttempt(SQLModel, table=True):
    """Represents a user's attempt at a quiz question."""
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key='quizquestion.id')
    user_answer: str
    is_correct: bool
    attempted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    question: Optional[QuizQuestion] = Relationship(back_populates="attempts")

class EdgeType(str, Enum):
    """Enumeration for concept graph edge types."""
    prerequisite = "prerequisite"
    extension = "extension"
    application = "application"
    contrast = "contrast"

class ConceptEdge(SQLModel, table=True):
    """Represents a directed edge in the concept graph between two topics."""
    id: Optional[int] = Field(default=None, primary_key=True)
    source_topic_id: int = Field(foreign_key='topic.id')
    target_topic_id: int = Field(foreign_key='topic.id')
    edge_type: EdgeType

    source_topic: Optional[Topic] = Relationship(
        back_populates="outgoing_edges",
        sa_relationship_kwargs={"foreign_keys": "[ConceptEdge.source_topic_id]"}
    )
    target_topic: Optional[Topic] = Relationship(
        back_populates="incoming_edges",
        sa_relationship_kwargs={"foreign_keys": "[ConceptEdge.target_topic_id]"}
    )