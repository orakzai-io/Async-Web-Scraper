from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime


# This is the "Base" class — every model you create must inherit from it.
# Alembic reads this to understand your table structure.
class Base(DeclarativeBase):
    pass


# This is your actual table. Each class = one table in the database.
class ParsedData(Base):
    __tablename__ = "parsed_data"

    id = Column(Integer, primary_key=True, autoincrement=True)

    Content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    llm_extractions = relationship(
        "LlmExtraction", back_populates="parsed_data", cascade="all, delete-orphan"
    )


class LlmExtraction(Base):
    __tablename__ = "llm_extractions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    parsed_data_id = Column(Integer, ForeignKey("parsed_data.id"), nullable=False)

    source_url = Column(String, nullable=True)
    json_data = Column(Text, nullable=False)  # store full JSON string

    created_at = Column(DateTime, default=datetime.utcnow)

    parsed_data = relationship("ParsedData", back_populates="llm_extractions")
