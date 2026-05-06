# RAYR MONEY - Manual Backend File Extractor for PowerShell
# Save this as: extract_backend.ps1
# Run with: powershell -ExecutionPolicy Bypass .\extract_backend.ps1

Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 59) -ForegroundColor Green
Write-Host "  RAYR MONEY - Backend File Extractor (PowerShell)" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""

# Check if codebase.ts exists
if (-not (Test-Path "src\codebase.ts")) {
    Write-Host "ERROR: src\codebase.ts not found!" -ForegroundColor Red
    Write-Host "Make sure you're in E:\TRADEUIMM directory" -ForegroundColor Yellow
    pause
    exit
}

# Create backend directory
New-Item -ItemType Directory -Force -Path "backend" | Out-Null
Write-Host "Created: backend\" -ForegroundColor Green

# Read codebase.ts
$content = Get-Content "src\codebase.ts" -Raw -Encoding UTF8

# Extract Python files using regex
$pattern = 'name:\s*"([^"]+\.py)".*?code:\s*`([\s\S]*?)`\s*\}'
$matches = [regex]::Matches($content, $pattern)

Write-Host "`nFound $($matches.Count) Python files:" -ForegroundColor Cyan
Write-Host ""

foreach ($match in $matches) {
    $filename = $match.Groups[1].Value
    $code = $match.Groups[2].Value
    
    $filepath = "backend\$filename"
    
    # Write file
    [System.IO.File]::WriteAllText($filepath, $code, [System.Text.Encoding]::UTF8)
    
    $filesize = (Get-Item $filepath).Length
    Write-Host "  Created: $filepath ($filesize bytes)" -ForegroundColor Green
}

# Create __init__.py
$initContent = "# RAYR MONEY Backend Package`n"
[System.IO.File]::WriteAllText("backend\__init__.py", $initContent, [System.Text.Encoding]::UTF8)
Write-Host "  Created: backend\__init__.py" -ForegroundColor Green

# Create requirements.txt
$requirements = @"
pandas>=2.0.0
numpy>=1.24.0
yfinance>=0.2.0
fastapi>=0.100.0
uvicorn>=0.23.0
python-dotenv>=1.0.0
cryptography>=41.0.0
requests>=2.31.0
alpaca-trade-api>=3.0.0
scikit-learn>=1.3.0
"@

[System.IO.File]::WriteAllText("backend\requirements.txt", $requirements, [System.Text.Encoding]::UTF8)
Write-Host "  Created: backend\requirements.txt" -ForegroundColor Green

# Create .env template
$envTemplate = @"
# Alpaca API Credentials (Get from https://alpaca.markets/)
ALPACA_API_KEY_ID=YOUR_API_KEY_HERE
ALPACA_SECRET_KEY=YOUR_SECRET_KEY_HERE

# Trading Configuration
RISK_PCT_PER_TRADE=0.015
ATR_MULTIPLIER=2.0
SCORE_THRESHOLD=70
MAX_TOTAL_RISK_PCT=0.05
"@

[System.IO.File]::WriteAllText("backend\.env.template", $envTemplate, [System.Text.Encoding]::UTF8)
Write-Host "  Created: backend\.env.template" -ForegroundColor Green

Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "EXTRACTION COMPLETE!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Copy backend\.env.template to backend\.env"
Write-Host "2. Edit backend\.env with your Alpaca API keys"
Write-Host "3. Run: pip install -r backend\requirements.txt"
Write-Host "4. Run: python backend\alpaca_live_runner.py"
Write-Host ""
pause
