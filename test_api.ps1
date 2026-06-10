# PowerShell test script for Transaction Processing API
# Usage: .\test_api.ps1

$API_URL = "http://localhost:8000"
$SAMPLE_CSV = "sample_transactions.csv"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Transaction Processing API Test Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if API is healthy
Write-Host "1. Testing health endpoint..." -ForegroundColor Yellow
$healthResponse = Invoke-RestMethod -Uri "$API_URL/health" -Method Get
$healthResponse | ConvertTo-Json
Write-Host ""

# Upload CSV
Write-Host "2. Uploading CSV file..." -ForegroundColor Yellow
$form = @{
    file = Get-Item -Path $SAMPLE_CSV
}
$uploadResponse = Invoke-RestMethod -Uri "$API_URL/jobs/upload" -Method Post -Form $form
$uploadResponse | ConvertTo-Json
$JOB_ID = $uploadResponse.job_id
Write-Host ""
Write-Host "Job ID: $JOB_ID" -ForegroundColor Green
Write-Host ""

# Check status
Write-Host "3. Checking job status..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
$statusResponse = Invoke-RestMethod -Uri "$API_URL/jobs/$JOB_ID/status" -Method Get
$statusResponse | ConvertTo-Json
Write-Host ""

# Wait for completion
Write-Host "4. Waiting for job to complete..." -ForegroundColor Yellow
$MAX_ATTEMPTS = 30
$ATTEMPT = 0

while ($ATTEMPT -lt $MAX_ATTEMPTS) {
    $statusResponse = Invoke-RestMethod -Uri "$API_URL/jobs/$JOB_ID/status" -Method Get
    $STATUS = $statusResponse.status
    
    if ($STATUS -eq "completed") {
        Write-Host "Job completed successfully!" -ForegroundColor Green
        break
    }
    elseif ($STATUS -eq "failed") {
        Write-Host "Job failed!" -ForegroundColor Red
        $statusResponse | ConvertTo-Json
        exit 1
    }
    
    Write-Host "Status: $STATUS (attempt $($ATTEMPT+1)/$MAX_ATTEMPTS)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
    $ATTEMPT++
}

if ($ATTEMPT -eq $MAX_ATTEMPTS) {
    Write-Host "Timeout waiting for job completion" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Get results
Write-Host "5. Fetching job results..." -ForegroundColor Yellow
$resultsResponse = Invoke-RestMethod -Uri "$API_URL/jobs/$JOB_ID/results" -Method Get
$resultsResponse | ConvertTo-Json -Depth 10
Write-Host ""

# List all jobs
Write-Host "6. Listing all jobs..." -ForegroundColor Yellow
$jobsResponse = Invoke-RestMethod -Uri "$API_URL/jobs" -Method Get
$jobsResponse | ConvertTo-Json
Write-Host ""

# List completed jobs
Write-Host "7. Listing completed jobs..." -ForegroundColor Yellow
$completedJobsResponse = Invoke-RestMethod -Uri "$API_URL/jobs?status=completed" -Method Get
$completedJobsResponse | ConvertTo-Json
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
