# System Architecture

## Overview

The AI-Powered Transaction Processing Pipeline is a microservices-based system designed for scalable, asynchronous processing of financial transaction data with AI-powered analysis.

## Architecture Diagram

```
┌─────────────┐
│   Client    │
│  (Browser/  │
│   curl)     │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────────────────┐
│            FastAPI Application              │
│  ┌─────────────────────────────────────┐   │
│  │  API Endpoints                       │   │
│  │  - POST /jobs/upload                 │   │
│  │  - GET  /jobs/{id}/status            │   │
│  │  - GET  /jobs/{id}/results           │   │
│  │  - GET  /jobs                        │   │
│  └─────────────────────────────────────┘   │
└──────┬──────────────────────┬───────────────┘
       │                      │
       │ Write Job            │ Read Results
       │                      │
       ▼                      ▼
┌────────────────────────────────────────────┐
│          PostgreSQL Database               │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │   jobs   │ │transactions│ │ summaries │  │
│  └──────────┘ └──────────┘ └───────────┘  │
└────────────────────────────────────────────┘
       ▲
       │ Store Results
       │
┌──────┴─────────────────────────────────────┐
│          Celery Worker                      │
│  ┌─────────────────────────────────────┐   │
│  │  Processing Pipeline                │   │
│  │  1. Data Cleaning                   │   │
│  │  2. Anomaly Detection               │   │
│  │  3. AI Classification  ────────┐    │   │
│  │  4. Summary Generation ────────┤    │   │
│  └─────────────────────────────────┘   │   │
└────────────────────────┬───────────────┘   │
       ▲                 │                    │
       │ Get Task        │ API Calls          │
       │                 ▼                    │
┌──────┴────────┐   ┌──────────────────────┐ │
│     Redis     │   │   Gemini 1.5 Flash   │ │
│  (Message     │   │   API (Google AI)    │ │
│   Broker)     │   └──────────────────────┘ │
└───────────────┘                              │
```

## Component Details

### 1. FastAPI Application

**Purpose**: RESTful API server for handling client requests

**Responsibilities**:
- Accept CSV file uploads
- Validate file format and size
- Create job records in database
- Queue processing tasks
- Serve job status and results
- Provide health check endpoint

**Technology Stack**:
- FastAPI: Web framework
- Uvicorn: ASGI server
- Pydantic: Request/response validation
- SQLAlchemy: Database ORM

**Endpoints**:
```python
POST   /jobs/upload           # Upload CSV file
GET    /jobs/{id}/status      # Check processing status
GET    /jobs/{id}/results     # Get processed results
GET    /jobs                  # List all jobs
GET    /health                # Health check
```

**Scaling**: Stateless, horizontally scalable

### 2. PostgreSQL Database

**Purpose**: Persistent storage for jobs, transactions, and summaries

**Schema Design**:

```sql
-- Jobs table
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    row_count_raw INTEGER,
    row_count_clean INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    txn_id VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    merchant VARCHAR(255) NOT NULL,
    amount FLOAT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    status VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    account_id VARCHAR(100) NOT NULL,
    notes TEXT,
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_reason TEXT,
    llm_category VARCHAR(100),
    llm_raw_response TEXT,
    llm_failed BOOLEAN DEFAULT FALSE
);

-- Job summaries table
CREATE TABLE job_summaries (
    id SERIAL PRIMARY KEY,
    job_id INTEGER UNIQUE REFERENCES jobs(id),
    total_spend_inr FLOAT,
    total_spend_usd FLOAT,
    top_merchants JSON,
    anomaly_count INTEGER DEFAULT 0,
    narrative TEXT,
    risk_level VARCHAR(20)
);
```

**Indexes**:
```sql
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_transactions_job_id ON transactions(job_id);
CREATE INDEX idx_transactions_txn_id ON transactions(txn_id);
CREATE INDEX idx_transactions_anomaly ON transactions(is_anomaly);
```

### 3. Redis

**Purpose**: Message broker for Celery task queue

**Usage**:
- Task queue: Stores pending processing tasks
- Result backend: Stores task results
- Broker: Routes tasks to workers

**Configuration**:
```python
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/0"
```

**Scaling**: 
- Single instance sufficient for most workloads
- Redis Cluster for high availability
- Redis Sentinel for automatic failover

### 4. Celery Worker

**Purpose**: Asynchronous task processing

**Processing Pipeline**:

```python
@celery_app.task(name="process_csv")
def process_csv_task(job_id: int, filepath: str):
    # 1. Load CSV
    df = pd.read_csv(filepath)
    
    # 2. Clean Data
    df = DataCleaner.clean_dataframe(df)
    
    # 3. Detect Anomalies
    df = AnomalyDetector.detect_all_anomalies(df)
    
    # 4. Classify Categories (AI)
    df = classify_missing_categories(df)
    
    # 5. Generate Summary (AI)
    generate_and_store_summary(df)
    
    # 6. Store Results
    store_transactions(db, job_id, df)
```

**Scaling**:
- Horizontal: Add more workers
- Vertical: Increase worker concurrency
- Auto-scale based on queue depth

### 5. Gemini AI Service

**Purpose**: AI-powered category classification and summary generation

**Integration Points**:
1. **Category Classification**
   - Input: Merchant, amount, notes
   - Output: Category (Food, Shopping, Travel, etc.)
   - Batching: 20 transactions per API call

2. **Summary Generation**
   - Input: All transactions data
   - Output: Narrative, risk level, insights
   - Frequency: Once per job

**Retry Logic**:
```python
def _retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func(), True
        except Exception as e:
            wait_time = 2 ** attempt  # Exponential backoff
            time.sleep(wait_time)
    return None, False
```

**Error Handling**:
- Failed classifications marked with `llm_failed=true`
- Processing continues even if AI fails
- Manual review possible for failed classifications

## Data Flow

### Upload Flow

```
1. Client uploads CSV
   ↓
2. FastAPI receives file
   ↓
3. Validate file format
   ↓
4. Create Job record (status=pending)
   ↓
5. Save file to disk
   ↓
6. Queue Celery task
   ↓
7. Return job_id to client
```

### Processing Flow

```
1. Celery worker picks task from Redis
   ↓
2. Update job status to "processing"
   ↓
3. Load CSV with pandas
   ↓
4. Clean data (dates, amounts, duplicates)
   ↓
5. Detect anomalies (amount, currency)
   ↓
6. Classify categories with Gemini (batched)
   ↓
7. Generate summary with Gemini
   ↓
8. Store transactions in database
   ↓
9. Store summary in database
   ↓
10. Update job status to "completed"
```

### Retrieval Flow

```
1. Client requests results
   ↓
2. FastAPI queries database
   ↓
3. Join jobs, transactions, summaries
   ↓
4. Calculate category breakdown
   ↓
5. Format response
   ↓
6. Return JSON to client
```

## Security Architecture

### Authentication & Authorization
```
Future enhancement:
- JWT tokens for API authentication
- Role-based access control (RBAC)
- API key authentication for M2M
```

### Data Security
- Database: SSL/TLS connections
- API: HTTPS only in production
- Secrets: Environment variables, not hardcoded
- File uploads: Size limits, format validation

### Network Security
```
Production:
- VPC isolation
- Security groups
- Private subnets for database/redis
- Public subnet for API (via load balancer)
```

## Scalability Patterns

### Horizontal Scaling

**API Servers**:
```yaml
# Scale to 5 replicas
docker compose up --scale api=5
```

**Celery Workers**:
```yaml
# Scale to 10 workers
docker compose up --scale celery_worker=10
```

### Vertical Scaling

**Database**:
- Increase CPU/memory for complex queries
- Add read replicas for GET-heavy workloads

**Workers**:
- Increase worker concurrency
- Allocate more CPU/memory per worker

### Auto-Scaling

**Metric-based scaling**:
```yaml
# Kubernetes HPA example
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: External
    external:
      metric:
        name: celery_queue_length
      target:
        type: AverageValue
        averageValue: "10"
```

## Reliability Patterns

### Retry Logic
- Gemini API: 3 retries with exponential backoff
- Database: Connection pooling with auto-reconnect
- Celery: Automatic task retry on failure

### Health Checks
```python
@app.get("/health")
async def health_check():
    # Check database connection
    # Check Redis connection
    # Return status
    return {"status": "healthy"}
```

### Graceful Degradation
- If Gemini fails: Mark as `llm_failed`, continue processing
- If summary fails: Store transactions, skip summary
- Partial success: Store what succeeded, log failures

### Circuit Breaker Pattern
```python
# Future enhancement
@circuit_breaker(failure_threshold=5, timeout=60)
def call_gemini_api():
    # API call
    pass
```

## Monitoring Architecture

### Metrics to Track

**Application Metrics**:
- Request rate (requests/sec)
- Response time (p50, p95, p99)
- Error rate (%)
- Active connections

**Worker Metrics**:
- Queue depth
- Task processing time
- Task success/failure rate
- Worker utilization

**Business Metrics**:
- Jobs processed per hour
- Average rows per job
- Anomaly detection rate
- AI classification success rate

### Logging Strategy

**Log Levels**:
```python
DEBUG: Development only
INFO:  Normal operations (job started, completed)
WARN:  Recoverable issues (retry attempts)
ERROR: Failures requiring attention
```

**Structured Logging**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "celery_worker",
  "job_id": 123,
  "event": "job_completed",
  "duration_seconds": 45.2,
  "rows_processed": 1000
}
```

## Performance Optimization

### Database Optimization
- Indexes on frequently queried columns
- Connection pooling
- Query optimization
- Partitioning for large tables

### API Optimization
- Async endpoints
- Response pagination
- Caching (Redis)
- Connection reuse

### Worker Optimization
- Batch processing
- Pandas vectorization
- Parallel processing
- Memory-efficient CSV reading

### AI API Optimization
- Batch requests (20 per call)
- Response caching
- Request compression
- Rate limiting

## Disaster Recovery

### Backup Strategy
```bash
# Database backup
pg_dump -U postgres transactions_db > backup.sql

# Automated daily backups
0 2 * * * /usr/local/bin/backup_database.sh
```

### Recovery Procedures
1. Restore database from backup
2. Replay failed jobs from job table
3. Reprocess with `job.status='failed'`

### High Availability
- Multi-AZ database deployment
- Load-balanced API servers
- Redis Sentinel for failover
- Health check-based routing

## Technology Choices

| Component | Technology | Why? |
|-----------|-----------|------|
| API Framework | FastAPI | High performance, async, auto docs |
| Database | PostgreSQL | ACID compliance, JSON support, mature |
| Message Broker | Redis | Fast, simple, dual-purpose (queue + cache) |
| Task Queue | Celery | Battle-tested, Python-native, scalable |
| AI Provider | Gemini | Cost-effective, fast, good quality |
| ORM | SQLAlchemy | Mature, flexible, widely used |
| Data Processing | Pandas | Industry standard for tabular data |
| Containerization | Docker | Consistent environments, easy deployment |

## Future Enhancements

1. **Authentication**: Add JWT-based authentication
2. **Rate Limiting**: Prevent abuse
3. **Webhooks**: Notify clients on job completion
4. **Batch API**: Process multiple files in one job
5. **Real-time Updates**: WebSocket for live status
6. **Caching**: Cache frequently accessed results
7. **Analytics Dashboard**: Visualize trends
8. **Export**: Download results as CSV/Excel
9. **Scheduled Jobs**: Recurring processing
10. **ML Model**: Custom anomaly detection model
