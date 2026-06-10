"""
Celery worker configuration and task definitions.
Processes CSV uploads asynchronously.
"""
import os
import logging
from celery import Celery
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.base import SessionLocal
from app.models.job import Job
from app.models.transaction import Transaction
from app.models.job_summary import JobSummary
from app.utils.data_cleaner import DataCleaner
from app.utils.anomaly_detector import AnomalyDetector
from app.services.gemini_service import GeminiService
from app.services import processing_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("worker", broker=redis_url, backend=redis_url)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@celery_app.task(name="process_csv")
def process_csv_task(job_id: int, filepath: str):
    """
    Main Celery task to process uploaded CSV.
    
    Pipeline:
    1. Load and validate CSV
    2. Clean data
    3. Detect anomalies
    4. Classify missing categories with Gemini
    5. Generate AI summary
    6. Store results in database
    """
    db = SessionLocal()
    
    try:
        logger.info(f"Starting processing for job {job_id}")
        
        # Update job status
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        job.status = "processing"
        db.commit()
        
        # STEP 1: Load CSV
        logger.info(f"Loading CSV from {filepath}")
        df = pd.read_csv(filepath)
        job.row_count_raw = len(df)
        db.commit()
        
        # STEP 2: Clean data
        logger.info("Cleaning data...")
        df, clean_stats = DataCleaner.clean_dataframe(df)
        job.row_count_clean = len(df)
        db.commit()
        
        # STEP 3: Detect anomalies
        logger.info("Detecting anomalies...")
        df = AnomalyDetector.detect_all_anomalies(df)
        
        # STEP 4: Classify missing categories with Gemini
        logger.info("Classifying categories with Gemini AI...")
        df = processing_service.classify_missing_categories(df)
        
        # STEP 5: Store transactions in database
        logger.info("Storing transactions...")
        processing_service.store_transactions(db, job_id, df)
        
        # STEP 6: Generate AI summary
        logger.info("Generating AI summary...")
        processing_service.generate_and_store_summary(db, job_id, df)
        
        # Mark job as completed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
        
        # Mark job as failed
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        raise
    
    finally:
        db.close()


def classify_missing_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Use Gemini to classify transactions with missing categories.
    """
    # Find rows with Uncategorised category
    uncategorised_mask = df['category'] == 'Uncategorised'
    uncategorised_df = df[uncategorised_mask]
    
    if len(uncategorised_df) == 0:
        logger.info("No missing categories to classify")
        df['llm_category'] = None
        df['llm_raw_response'] = None
        df['llm_failed'] = False
        return df
    
    logger.info(f"Classifying {len(uncategorised_df)} transactions with missing categories")
    
    # Prepare transactions for Gemini
    transactions = uncategorised_df[['txn_id', 'merchant', 'amount', 'notes']].to_dict('records')
    
    # Call Gemini service
    try:
        gemini_service = GeminiService()
        results = gemini_service.classify_categories_batch(transactions)
        
        # Create results map
        results_map = {r['txn_id']: r for r in results}
        
        # Initialize LLM columns
        df['llm_category'] = None
        df['llm_raw_response'] = None
        df['llm_failed'] = False
        
        # Update DataFrame with results
        for idx, row in df.iterrows():
            if row['txn_id'] in results_map:
                result = results_map[row['txn_id']]
                df.at[idx, 'llm_category'] = result['category']
                df.at[idx, 'llm_raw_response'] = result['raw_response']
                df.at[idx, 'llm_failed'] = not result['success']
                
                # Update category if classification succeeded
                if result['success']:
                    df.at[idx, 'category'] = result['category']
        
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"Successfully classified {success_count}/{len(results)} transactions")
        
    except Exception as e:
        logger.error(f"Category classification failed: {str(e)}")
        # Initialize columns with failure state
        df['llm_category'] = None
        df['llm_raw_response'] = f"Error: {str(e)}"
        df['llm_failed'] = True
    
    return df


def store_transactions(db: Session, job_id: int, df: pd.DataFrame):
    """Store processed transactions in database."""
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
    logger.info(f"Stored {len(transactions)} transactions")


def generate_and_store_summary(db: Session, job_id: int, df: pd.DataFrame):
    """Generate AI summary and store in database."""
    try:
        gemini_service = GeminiService()
        summary_data = gemini_service.generate_summary(df)
        
        if summary_data:
            # Extract spend by currency
            total_spend_inr = summary_data.get('total_spend_by_currency', {}).get('INR', 0)
            total_spend_usd = summary_data.get('total_spend_by_currency', {}).get('USD', 0)
            
            summary = JobSummary(
                job_id=job_id,
                total_spend_inr=total_spend_inr,
                total_spend_usd=total_spend_usd,
                top_merchants=summary_data.get('top_3_merchants', []),
                anomaly_count=summary_data.get('anomaly_count', 0),
                narrative=summary_data.get('narrative'),
                risk_level=summary_data.get('risk_level')
            )
            
            db.add(summary)
            db.commit()
            logger.info(f"Stored summary for job {job_id}")
        else:
            logger.warning(f"No summary generated for job {job_id}")
            
    except Exception as e:
        logger.error(f"Failed to generate/store summary: {str(e)}")
        # Don't fail the entire job if summary generation fails
