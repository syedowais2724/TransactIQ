"""
FastAPI application for local development (without Celery).
Processes CSV files synchronously.
"""
import os
import logging
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import pandas as pd
from datetime import datetime

from app.database.base import init_db, get_db
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.job_summary import JobSummary
from app.schemas import (
    JobResponse,
    JobStatusResponse,
    JobListResponse,
    JobResultsResponse,
    TransactionResponse,
)
from app.schemas.results import CategoryBreakdown
from app.utils.data_cleaner import DataCleaner
from app.utils.anomaly_detector import AnomalyDetector
from app.utils.category_classifier import CategoryClassifier
from app.services.gemini_service import GeminiService
from app.services import processing_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Upload directory
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


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

# Create FastAPI app
app = FastAPI(
    title="AI-Powered Transaction Processing Pipeline (Local)",
    description="Backend system for processing transaction CSVs - Local Development Mode",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")
    logger.info("Running in LOCAL MODE (synchronous processing)")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "transaction-processing-api-local",
        "mode": "synchronous"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI-Powered Transaction Processing Pipeline API (Local Mode)",
        "version": "1.0.0",
        "mode": "synchronous",
        "docs": "/docs"
    }


@app.post("/jobs/upload", response_model=JobResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process CSV file (synchronous).
    Processing happens immediately - may take 30-60 seconds.
    """
    # Validate file
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    job = None
    filepath = None
    
    try:
        # Create job record
        job = Job(filename=file.filename, status="processing")
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Save file
        filepath = os.path.join(UPLOAD_DIR, f"job_{job.id}_{file.filename}")
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Processing job {job.id} synchronously...")
        
        # Process immediately (synchronous)
        process_csv_sync(job.id, filepath, db)
        
        return JobResponse(job_id=job.id, status="completed")
    
    except Exception as e:
        logger.error(f"Upload/processing failed: {str(e)}", exc_info=True)
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


def process_csv_sync(job_id: int, filepath: str, db: Session):
    """Process CSV synchronously (inline)."""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        
        # Load CSV
        logger.info(f"Loading CSV...")
        df = pd.read_csv(filepath)
        job.row_count_raw = len(df)
        db.commit()
        
        # Clean data
        logger.info("Cleaning data...")
        df, _ = DataCleaner.clean_dataframe(df)
        job.row_count_clean = len(df)
        db.commit()
        
        # Detect anomalies
        logger.info("Detecting anomalies...")
        df = AnomalyDetector.detect_all_anomalies(df)
        
        # Classify with AI
        logger.info("Classifying categories with AI...")
        df = processing_service.classify_missing_categories(df)
        
        # Store transactions
        logger.info("Storing transactions...")
        processing_service.store_transactions(db, job_id, df)
        
        # Generate summary
        logger.info("Generating AI summary...")
        processing_service.generate_and_store_summary(db, job_id, df)
        
        # Complete
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
        raise


def classify_missing_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Intelligent category classification with 3-tier approach:
    1. Rule-based classification (merchant patterns)
    2. Gemini AI for uncertain cases
    3. Fallback to 'Other'
    
    This dramatically reduces 'Other' category usage!
    """
    # Find rows that need classification
    missing_mask = df['category'] == '__MISSING__'
    missing_df = df[missing_mask]
    
    logger.info(f"===== SMART CATEGORY CLASSIFICATION START =====")
    logger.info(f"Total rows: {len(df)}")
    logger.info(f"Rows needing classification: {len(missing_df)}")
    
    # Initialize columns
    df['llm_category'] = None
    df['llm_raw_response'] = None
    df['llm_failed'] = False
    df['classified_by'] = 'original'  # Track classification method
    
    if len(missing_df) == 0:
        logger.info("No missing categories to classify!")
        return df
    
    # STEP 1: Rule-based classification
    logger.info("=== STEP 1: Rule-based Classification ===")
    rule_classified = 0
    ai_needed = []
    
    for idx, row in df[missing_mask].iterrows():
        rule_category = CategoryClassifier.classify_by_rules(
            row['merchant'], 
            row['amount'], 
            row.get('notes')
        )
        
        if rule_category:
            df.at[idx, 'category'] = rule_category
            df.at[idx, 'classified_by'] = 'rule'
            rule_classified += 1
        else:
            # Need AI classification
            ai_needed.append({
                'index': idx,
                'txn_id': row['txn_id'],
                'merchant': row['merchant'],
                'amount': row['amount'],
                'notes': row.get('notes')
            })
    
    logger.info(f"✓ Rule-based: {rule_classified} transactions classified")
    logger.info(f"⟳ AI needed: {len(ai_needed)} transactions")
    
    # STEP 2: AI classification for uncertain cases
    if len(ai_needed) > 0:
        logger.info("=== STEP 2: Gemini AI Classification ===")
        
        transactions = [
            {'txn_id': t['txn_id'], 'merchant': t['merchant'], 'amount': t['amount'], 'notes': t['notes']}
            for t in ai_needed
        ]
        
        try:
            gemini_service = GeminiService()
            results = gemini_service.classify_categories_batch(transactions)
            results_map = {r['txn_id']: r for r in results}
            
            ai_success = 0
            ai_failed = 0
            
            for txn_info in ai_needed:
                idx = txn_info['index']
                txn_id = txn_info['txn_id']
                
                if txn_id in results_map:
                    result = results_map[txn_id]
                    
                    df.at[idx, 'llm_category'] = result['category']
                    df.at[idx, 'llm_raw_response'] = result.get('raw_response', '')
                    df.at[idx, 'llm_failed'] = not result['success']
                    
                    if result['success'] and result['category'] and result['category'] != 'Other':
                        # Normalize category
                        normalized = CategoryClassifier.normalize_category(result['category'])
                        df.at[idx, 'category'] = normalized
                        df.at[idx, 'classified_by'] = 'ai'
                        ai_success += 1
                    else:
                        df.at[idx, 'category'] = 'Other'
                        df.at[idx, 'classified_by'] = 'fallback'
                        ai_failed += 1
                else:
                    df.at[idx, 'category'] = 'Other'
                    df.at[idx, 'classified_by'] = 'fallback'
                    df.at[idx, 'llm_failed'] = True
                    ai_failed += 1
            
            logger.info(f"✓ AI classified: {ai_success} transactions")
            logger.info(f"✗ AI failed (using Other): {ai_failed} transactions")
            
        except Exception as e:
            logger.error(f"Gemini classification error: {str(e)}", exc_info=True)
            
            # Fallback for all AI-needed transactions
            for txn_info in ai_needed:
                idx = txn_info['index']
                df.at[idx, 'category'] = 'Other'
                df.at[idx, 'classified_by'] = 'fallback'
                df.at[idx, 'llm_failed'] = True
                df.at[idx, 'llm_raw_response'] = f"Error: {str(e)}"
            
            logger.warning(f"All {len(ai_needed)} uncertain transactions set to 'Other' due to API error")
    
    # STEP 3: Final validation
    still_missing = (df['category'] == '__MISSING__').sum()
    if still_missing > 0:
        logger.error(f"CRITICAL: {still_missing} rows still have __MISSING__!")
        df.loc[df['category'] == '__MISSING__', 'category'] = 'Other'
        df.loc[df['category'] == '__MISSING__', 'classified_by'] = 'emergency_fallback'
    
    # Ensure no NaN or empty
    df['category'] = df['category'].fillna('Other')
    df['category'] = df['category'].replace('', 'Other')
    
    # Log final statistics
    logger.info(f"===== CLASSIFICATION SUMMARY =====")
    logger.info(f"Rule-based: {rule_classified}")
    logger.info(f"AI classified: {(df['classified_by'] == 'ai').sum()}")
    logger.info(f"Fallback to Other: {(df['classified_by'] == 'fallback').sum()}")
    
    # Log category distribution
    category_counts = df['category'].value_counts()
    logger.info(f"===== FINAL CATEGORY DISTRIBUTION =====")
    for cat, count in category_counts.items():
        pct = (count / len(df)) * 100
        logger.info(f"  {cat}: {count} ({pct:.1f}%)")
    
    return df


def store_transactions(db: Session, job_id: int, df: pd.DataFrame):
    """Store transactions in database."""
    transactions = []
    for _, row in df.iterrows():
        transaction = Transaction(
            job_id=job_id,
            txn_id=row['txn_id'],
            date=row['date'],
            merchant=row['merchant'],
            amount=row['amount'],
            currency=row['currency'],
            status=row['status'],
            category=row['category'],
            account_id=row['account_id'],
            notes=row.get('notes'),
            is_anomaly=row['is_anomaly'],
            anomaly_reason=row.get('anomaly_reason'),
            llm_category=row.get('llm_category'),
            llm_raw_response=row.get('llm_raw_response'),
            llm_failed=row.get('llm_failed', False)
        )
        transactions.append(transaction)
    
    db.bulk_save_objects(transactions)
    db.commit()


def generate_and_store_summary(db: Session, job_id: int, df: pd.DataFrame):
    """Generate and store AI summary."""
    try:
        gemini_service = GeminiService()
        summary_data = gemini_service.generate_summary(df)
        
        if summary_data:
            summary = JobSummary(
                job_id=job_id,
                total_spend_inr=summary_data.get('total_spend_by_currency', {}).get('INR', 0),
                total_spend_usd=summary_data.get('total_spend_by_currency', {}).get('USD', 0),
                top_merchants=summary_data.get('top_3_merchants', []),
                anomaly_count=summary_data.get('anomaly_count', 0),
                narrative=summary_data.get('narrative'),
                risk_level=summary_data.get('risk_level')
            )
            db.add(summary)
            db.commit()
    except Exception as e:
        logger.error(f"Summary generation failed: {str(e)}")


@app.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get job status."""
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


@app.get("/jobs/{job_id}/results", response_model=JobResultsResponse)
def get_job_results(job_id: int, db: Session = Depends(get_db)):
    """Get job results."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed. Current status: {job.status}"
        )
    
    transactions = db.query(Transaction).filter(Transaction.job_id == job_id).all()
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
        for stat in processing_service.get_category_breakdown(db, job_id)
    ]
    
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


@app.get("/jobs", response_model=List[JobListResponse])
def list_jobs(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all jobs."""
    query = db.query(Job)
    if status:
        query = query.filter(Job.status == status)
    
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
