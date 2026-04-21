"""Database setup and session helpers."""

from sqlmodel import create_engine, Session, SQLModel
from config import settings

# Create the database engine
engine = create_engine(settings.SQLITE_URL, echo=settings.DEBUG,
                       connect_args={"check_same_thread": False})   # needed for SQLite only

def create_db_and_tables():
    """Create database and tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get a new database session."""
    with Session(engine) as session:
        yield session
