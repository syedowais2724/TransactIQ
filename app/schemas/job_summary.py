"""
Pydantic schemas for JobSummary-related API responses.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class JobSummaryResponse(BaseModel):
    id: int
    job_id: int
    total_spend_inr: Optional[float] = None
    total_spend_usd: Optional[float] = None
    top_merchants: Optional[List[Dict[str, Any]]] = None
    anomaly_count: int
    narrative: Optional[str] = None
    risk_level: Optional[str] = None

    class Config:
        from_attributes = True
