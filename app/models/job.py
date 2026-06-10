"""
Job model for tracking CSV processing jobs.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)
    # Status options: pending, processing, completed, failed
    
    row_count_raw = Column(Integer, nullable=True)
    row_count_clean = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Job(id={self.id}, filename={self.filename}, status={self.status})>"
