# Start DocForge Backend with Groq AI Provider

Write-Host "Starting DocForge Backend with Groq AI" -ForegroundColor Cyan
Write-Host ""

# Set environment variables for Groq (load from .env or set manually)
$env:AI_PROVIDER = "groq"
$env:GROQ_API_KEY = $env:GROQ_API_KEY  # Will use key from .env
$env:GROQ_MODEL = "openai/gpt-oss-120b"

Write-Host "AI Provider: $env:AI_PROVIDER" -ForegroundColor Green
Write-Host "Model: $env:GROQ_MODEL" -ForegroundColor Green
Write-Host "API Key: Set" -ForegroundColor Green
Write-Host ""

# Navigate to backend and activate virtual environment
Set-Location backend
& .venv\Scripts\Activate.ps1

# Start the backend
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
Write-Host ""
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
