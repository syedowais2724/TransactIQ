"""
Pydantic schemas for Job-related API requests and responses.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class JobCreate(BaseModel):
    filename: str


class JobResponse(BaseModel):
    job_id: int
    status: str

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    job_id: int
    status: str
    filename: str
    row_count_raw: Optional[int] = None
    row_count_clean: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    job_id: int
    filename: str
    status: str
    row_count_raw: Optional[int] = None
    row_count_clean: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
