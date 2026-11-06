# Start DocForge Backend with Groq AI Provider

Write-Host "Starting DocForge Backend with Groq AI" -ForegroundColor Cyan
Write-Host ""

# Load environment variables from .env file
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host "Loaded environment from .env" -ForegroundColor Green
} else {
    Write-Host "Warning: .env file not found" -ForegroundColor Yellow
}

Write-Host "AI Provider: $env:AI_PROVIDER" -ForegroundColor Green
Write-Host "Model: $env:GROQ_MODEL" -ForegroundColor Green
Write-Host "API Key: $(if ($env:GROQ_API_KEY) { 'Set' } else { 'MISSING!' })" -ForegroundColor Green
Write-Host ""

# Navigate to backend and activate virtual environment
Set-Location backend
& .venv\Scripts\Activate.ps1

# Start the backend
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
Write-Host ""
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
