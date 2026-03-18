from pathlib import Path

from sqlalchemy import (Column, ForeignKey, Integer, String, UniqueConstraint,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Use a file-based SQLite database in the repository root.
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=False)
    schedule = Column(String, nullable=False)
    max_participants = Column(Integer, nullable=False)

    participants = relationship(
        "Participant",
        back_populates="activity",
        cascade="all, delete-orphan",
        lazy="joined",
    )


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)

    activity = relationship("Activity", back_populates="participants")

    __table_args__ = (UniqueConstraint("activity_id", "email", name="uq_activity_email"),)


def init_db():
    """Create database tables.

    This is safe to call multiple times.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """Yield a SQLAlchemy session (dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
