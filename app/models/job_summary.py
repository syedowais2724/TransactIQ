"""
JobSummary model for storing AI-generated summary reports.
"""
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, JSON
from app.database.base import Base


class JobSummary(Base):
    __tablename__ = "job_summaries"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, unique=True, index=True)
    
    # Summary statistics
    total_spend_inr = Column(Float, nullable=True)
    total_spend_usd = Column(Float, nullable=True)
    top_merchants = Column(JSON, nullable=True)  # Store as JSON array
    anomaly_count = Column(Integer, default=0, nullable=False)
    
    # AI-generated fields
    narrative = Column(Text, nullable=True)
    risk_level = Column(String(20), nullable=True)  # low, medium, high

    def __repr__(self):
        return f"<JobSummary(id={self.id}, job_id={self.job_id}, risk_level={self.risk_level})>"
