"""
Combined schema for job results API response.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.schemas.transaction import TransactionResponse


class CategoryBreakdown(BaseModel):
    category: str
    count: int
    total_amount: float


class JobResultsResponse(BaseModel):
    job_id: int
    status: str
    filename: str
    transactions: List[TransactionResponse]
    anomalies: List[TransactionResponse]
    category_breakdown: List[CategoryBreakdown]
    summary: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
