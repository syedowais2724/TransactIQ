# AI-Powered Transaction Processing Pipeline

A production-ready backend system that processes transaction CSV files asynchronously with AI-powered analysis using Google's Gemini 1.5 Flash API.

## 🏗️ Architecture Overview

This system implements a complete asynchronous processing pipeline:

```
CSV Upload → FastAPI → Redis Queue → Celery Worker → PostgreSQL
                                    ↓
                              Gemini AI API
                                    ↓
                            Results & Summary
```

### Components

- **FastAPI**: High-performance async web framework for API endpoints
- **PostgreSQL**: Relational database for persistent storage
- **Redis**: Message broker for Celery task queue
- **Celery**: Distributed task queue for async processing
- **SQLAlchemy**: ORM for database operations
- **Gemini 1.5 Flash**: AI-powered category classification and summary generation
- **Docker Compose**: One-command deployment

## 🚀 Features

### Data Processing Pipeline

1. **Data Cleaning**
   - Normalizes mixed date formats to ISO 8601
   - Removes currency symbols from amounts
   - Standardizes status and currency values
   - Fills missing categories
   - Removes duplicate rows

2. **Anomaly Detection**
   - Flags transactions > 3x account median
   - Detects currency mismatches (USD with Indian merchants)
   - Provides detailed anomaly reasons

3. **AI-Powered Classification**
   - Uses Gemini to classify missing categories
   - Batch processing for efficiency
   - Retry logic with exponential backoff
   - Categories: Food, Shopping, Travel, Transport, Utilities, Cash Withdrawal, Entertainment, Other

4. **AI Summary Generation**
   - Total spend by currency
   - Top 3 merchants
   - Anomaly analysis
   - Business narrative
   - Risk level assessment (low/medium/high)

## 📁 Project Structure

```
project/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── jobs.py              # API endpoints
│   ├── database/
│   │   ├── __init__.py
│   │   └── base.py              # Database config
│   ├── models/
│   │   ├── __init__.py
│   │   ├── job.py               # Job model
│   │   ├── transaction.py       # Transaction model
│   │   └── job_summary.py       # Summary model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── job.py               # Job schemas
│   │   ├── transaction.py       # Transaction schemas
│   │   ├── job_summary.py       # Summary schemas
│   │   └── results.py           # Results schemas
│   ├── services/
│   │   ├── __init__.py
│   │   └── gemini_service.py    # Gemini AI integration
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── data_cleaner.py      # Data cleaning utilities
│   │   └── anomaly_detector.py  # Anomaly detection
│   ├── workers/
│   │   ├── __init__.py
│   │   └── celery_worker.py     # Celery tasks
│   └── main.py                  # FastAPI app
├── uploads/                     # Uploaded CSV files
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## 🛠️ Setup Instructions

### Prerequisites

- Docker
- Docker Compose
- Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd project
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

3. **Start the entire system**
   ```bash
   docker compose up
   ```

That's it! The system will:
- Start PostgreSQL database
- Start Redis message broker
- Initialize database tables
- Launch FastAPI server on port 8000
- Start Celery worker for background processing

4. **Access the API**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## 📡 API Endpoints

### 1. Upload CSV

```bash
curl -X POST "http://localhost:8000/jobs/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@transactions.csv"
```

**Response:**
```json
{
  "job_id": 1,
  "status": "pending"
}
```

### 2. Check Job Status

```bash
curl "http://localhost:8000/jobs/1/status"
```

**Response:**
```json
{
  "job_id": 1,
  "status": "completed",
  "filename": "transactions.csv",
  "row_count_raw": 100,
  "row_count_clean": 95,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:31:00Z",
  "error_message": null
}
```

### 3. Get Results

```bash
curl "http://localhost:8000/jobs/1/results"
```

**Response includes:**
- All cleaned transactions
- Flagged anomalies
- Category breakdown
- AI-generated summary

### 4. List Jobs

```bash
# All jobs
curl "http://localhost:8000/jobs"

# Filter by status
curl "http://localhost:8000/jobs?status=completed"
```

## 🗄️ Database Schema

### Job Table
- `id`: Primary key
- `filename`: Original CSV filename
- `status`: pending | processing | completed | failed
- `row_count_raw`: Original row count
- `row_count_clean`: Cleaned row count
- `created_at`: Creation timestamp
- `completed_at`: Completion timestamp
- `error_message`: Error details if failed

### Transaction Table
- `id`: Primary key
- `job_id`: Foreign key to Job
- `txn_id`: Transaction ID
- `date`: Transaction date (normalized)
- `merchant`: Merchant name
- `amount`: Transaction amount (cleaned)
- `currency`: Currency code
- `status`: Transaction status
- `category`: Transaction category
- `account_id`: Account identifier
- `notes`: Additional notes
- `is_anomaly`: Anomaly flag
- `anomaly_reason`: Reason for flagging
- `llm_category`: AI-classified category
- `llm_raw_response`: Raw AI response
- `llm_failed`: AI classification failure flag

### JobSummary Table
- `id`: Primary key
- `job_id`: Foreign key to Job
- `total_spend_inr`: Total spend in INR
- `total_spend_usd`: Total spend in USD
- `top_merchants`: Top 3 merchants (JSON)
- `anomaly_count`: Number of anomalies
- `narrative`: AI-generated narrative
- `risk_level`: low | medium | high

## 🔧 Configuration

### Environment Variables

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/transactions_db
REDIS_URL=redis://redis:6379/0
GEMINI_API_KEY=your_api_key_here
UPLOAD_DIR=/app/uploads
```

### Retry Logic

Gemini API calls implement exponential backoff:
- Max retries: 3
- Backoff: 1s, 2s, 4s
- Failed calls marked as `llm_failed=true`
- Processing continues even if AI classification fails

## 📊 Data Processing Details

### Date Normalization
Handles formats:
- `YYYY-MM-DD` (ISO)
- `DD/MM/YYYY`
- `MM/DD/YYYY`
- `DD-MM-YYYY`
- `DD-MMM-YYYY`
- And more...

### Amount Cleaning
Removes:
- Currency symbols: $, ₹, €, £
- Thousands separators: commas
- Whitespace

### Anomaly Detection Rules

1. **Amount-based**: `amount > 3 × account_median`
2. **Currency-based**: USD used with Indian merchants (Swiggy, Ola, IRCTC)

### Category Classification

Uses Gemini to classify into:
- Food
- Shopping
- Travel
- Transport
- Utilities
- Cash Withdrawal
- Entertainment
- Other

## 🚦 Scaling Considerations

### Horizontal Scaling

1. **API Servers**: Scale FastAPI containers
   ```bash
   docker compose up --scale api=3
   ```

2. **Celery Workers**: Add more workers for parallel processing
   ```bash
   docker compose up --scale celery_worker=5
   ```

3. **Redis**: Use Redis Cluster for high availability

4. **PostgreSQL**: 
   - Read replicas for GET queries
   - Connection pooling (already configured)
   - Partitioning for large transaction tables

### Performance Optimization

- Batch Gemini API calls (20 transactions per request)
- Bulk insert transactions using SQLAlchemy
- Database indexes on: `job_id`, `txn_id`, `is_anomaly`, `status`
- Async FastAPI endpoints where applicable

### Monitoring

Add monitoring for:
- Celery queue length
- Processing time per job
- Gemini API latency and errors
- Database connection pool usage

## 🧪 Testing

### Manual Testing

1. Create a sample CSV:
```csv
txn_id,date,merchant,amount,currency,status,category,account_id,notes
TXN001,15/01/2024,Starbucks,$5.50,USD,completed,,ACC001,Coffee
TXN002,16-01-2024,Swiggy,₹500,INR,completed,Food,ACC001,Lunch order
```

2. Upload via API
3. Check status
4. View results

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database connectivity
docker compose exec api python -c "from app.database.base import engine; engine.connect()"

# Redis connectivity  
docker compose exec redis redis-cli ping
```

## 📝 Logging

Logs are written to stdout and include:
- Job processing stages
- Data cleaning statistics
- Anomaly detection results
- AI API calls and responses
- Error traces

View logs:
```bash
docker compose logs -f api
docker compose logs -f celery_worker
```

## 🐛 Troubleshooting

### Celery worker not processing
```bash
# Check worker status
docker compose logs celery_worker

# Restart worker
docker compose restart celery_worker
```

### Database connection issues
```bash
# Check database health
docker compose ps db

# View database logs
docker compose logs db
```

### Gemini API errors
- Verify API key in `.env`
- Check API quota/rate limits
- Review worker logs for retry attempts

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 🔗 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
