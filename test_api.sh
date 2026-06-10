#!/bin/bash

# Test script for Transaction Processing API
# Usage: ./test_api.sh

set -e

API_URL="http://localhost:8000"
SAMPLE_CSV="sample_transactions.csv"

echo "========================================"
echo "Transaction Processing API Test Script"
echo "========================================"
echo ""

# Check if API is healthy
echo "1. Testing health endpoint..."
curl -s "${API_URL}/health" | python -m json.tool
echo ""

# Upload CSV
echo "2. Uploading CSV file..."
UPLOAD_RESPONSE=$(curl -s -X POST "${API_URL}/jobs/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@${SAMPLE_CSV}")

echo "$UPLOAD_RESPONSE" | python -m json.tool
JOB_ID=$(echo "$UPLOAD_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo ""
echo "Job ID: $JOB_ID"
echo ""

# Check status
echo "3. Checking job status..."
sleep 2
curl -s "${API_URL}/jobs/${JOB_ID}/status" | python -m json.tool
echo ""

# Wait for completion
echo "4. Waiting for job to complete..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  STATUS=$(curl -s "${API_URL}/jobs/${JOB_ID}/status" | python -c "import sys, json; print(json.load(sys.stdin)['status'])")
  
  if [ "$STATUS" == "completed" ]; then
    echo "Job completed successfully!"
    break
  elif [ "$STATUS" == "failed" ]; then
    echo "Job failed!"
    curl -s "${API_URL}/jobs/${JOB_ID}/status" | python -m json.tool
    exit 1
  fi
  
  echo "Status: $STATUS (attempt $((ATTEMPT+1))/$MAX_ATTEMPTS)"
  sleep 2
  ATTEMPT=$((ATTEMPT+1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
  echo "Timeout waiting for job completion"
  exit 1
fi

echo ""

# Get results
echo "5. Fetching job results..."
curl -s "${API_URL}/jobs/${JOB_ID}/results" | python -m json.tool
echo ""

# List all jobs
echo "6. Listing all jobs..."
curl -s "${API_URL}/jobs" | python -m json.tool
echo ""

# List completed jobs
echo "7. Listing completed jobs..."
curl -s "${API_URL}/jobs?status=completed" | python -m json.tool
echo ""

echo "========================================"
echo "Test completed successfully!"
echo "========================================"
