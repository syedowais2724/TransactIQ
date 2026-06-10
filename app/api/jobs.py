"""
FastAPI routes for job management.
Handles CSV upload, status tracking, and results retrieval.
"""
import os
import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.job_summary import JobSummary
from app.schemas import (
    JobResponse,
    JobStatusResponse,
    JobListResponse,
    JobResultsResponse,
    TransactionResponse,
    JobSummaryResponse
)
from app.schemas.results import CategoryBreakdown
from app.workers.celery_worker import process_csv_task
from app.services.processing_service import get_category_breakdown

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])

# Upload directory from environment
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def summary_to_dict(summary: JobSummary):
    if not summary:
        return None

    return {
        "total_spend_inr": summary.total_spend_inr,
        "total_spend_usd": summary.total_spend_usd,
        "top_merchants": summary.top_merchants,
        "anomaly_count": summary.anomaly_count,
        "narrative": summary.narrative,
        "risk_level": summary.risk_level,
    }


@router.post("/upload", response_model=JobResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a CSV file for processing.
    
    - Validates file format (must be .csv)
    - Creates a Job record with status='pending'
    - Saves file to upload directory
    - Triggers asynchronous Celery task
    - Returns job_id immediately
    """
    # Validate file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        # Create job record
        job = Job(
            filename=file.filename,
            status="pending"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Save uploaded file
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filepath = os.path.join(UPLOAD_DIR, f"job_{job.id}_{file.filename}")
        
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"File uploaded: {filepath} for job {job.id}")
        
        # Trigger Celery task
        process_csv_task.delay(job.id, filepath)
        logger.info(f"Celery task triggered for job {job.id}")
        
        return JobResponse(job_id=job.id, status=job.status)
    
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """
    Get the status of a processing job.
    
    Returns:
    - pending: Job is waiting to be processed
    - processing: Job is currently being processed
    - completed: Job finished successfully (includes summary stats)
    - failed: Job encountered an error
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    summary = None
    if job.status == "completed":
        summary = summary_to_dict(db.query(JobSummary).filter(JobSummary.job_id == job_id).first())

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        filename=job.filename,
        row_count_raw=job.row_count_raw,
        row_count_clean=job.row_count_clean,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        summary=summary
    )


@router.get("/{job_id}/results", response_model=JobResultsResponse)
def get_job_results(job_id: int, db: Session = Depends(get_db)):
    """
    Get detailed results for a completed job.
    
    Returns:
    - All cleaned transactions
    - List of anomalies
    - Category breakdown with counts and totals
    - AI-generated summary report
    """
    # Get job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet. Current status: {job.status}"
        )
    
    # Get all transactions
    transactions = db.query(Transaction).filter(Transaction.job_id == job_id).all()
    
    # Get anomalies
    anomalies = db.query(Transaction).filter(
        Transaction.job_id == job_id,
        Transaction.is_anomaly == True
    ).all()
    
    category_breakdown = [
        CategoryBreakdown(
            category=stat["category"],
            count=stat["count"],
            total_amount=stat["total_amount"]
        )
        for stat in get_category_breakdown(db, job_id)
    ]
    
    # Get summary
    summary = db.query(JobSummary).filter(JobSummary.job_id == job_id).first()
    summary_dict = summary_to_dict(summary)
    
    return JobResultsResponse(
        job_id=job.id,
        status=job.status,
        filename=job.filename,
        transactions=[TransactionResponse.from_orm(t) for t in transactions],
        anomalies=[TransactionResponse.from_orm(a) for a in anomalies],
        category_breakdown=category_breakdown,
        summary=summary_dict
    )



@router.get("", response_model=List[JobListResponse])
def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    List all jobs with optional status filter.
    
    Query parameters:
    - status: Filter by job status (pending, processing, completed, failed)
    
    Returns list of jobs with basic information and timestamps.
    """
    query = db.query(Job)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Job.status == status)
    
    # Order by creation time, newest first
    jobs = query.order_by(Job.created_at.desc()).all()
    
    return [
        JobListResponse(
            job_id=job.id,
            filename=job.filename,
            status=job.status,
            row_count_raw=job.row_count_raw,
            row_count_clean=job.row_count_clean,
            created_at=job.created_at,
            completed_at=job.completed_at
        )
        for job in jobs
    ]
