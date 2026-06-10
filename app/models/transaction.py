"""
Transaction model for storing processed transaction data.
"""
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Original transaction fields
    txn_id = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False)
    merchant = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(50), nullable=False)
    category = Column(String(100), nullable=True)
    account_id = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    
    # Anomaly detection fields
    is_anomaly = Column(Boolean, default=False, nullable=False, index=True)
    anomaly_reason = Column(Text, nullable=True)
    
    # LLM classification fields
    llm_category = Column(String(100), nullable=True)
    llm_raw_response = Column(Text, nullable=True)
    llm_failed = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Transaction(id={self.id}, txn_id={self.txn_id}, merchant={self.merchant})>"
