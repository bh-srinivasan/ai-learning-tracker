# Test script to demonstrate the Python 64-bit upgrade functionality
# This script shows current system state before running the upgrade

Write-Host "=== Pre-Upgrade System Check ===" -ForegroundColor Cyan

# Check current Python state
Write-Host "`nPython Information:" -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Version: $pythonVersion" -ForegroundColor Green
        
        $archInfo = python -c "import platform; print('Architecture:', platform.architecture()[0]); print('Platform:', platform.platform())" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $archInfo -split "`n" | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }
        }
        
        $pythonPath = where.exe python 2>$null | Select-Object -First 1
        Write-Host "  Path: $pythonPath" -ForegroundColor Green
    }
    else {
        Write-Host "  Python not found in PATH" -ForegroundColor Red
    }
}
catch {
    Write-Host "  Error checking Python: $($_.Exception.Message)" -ForegroundColor Red
}

# Check for cryptography warning
Write-Host "`nCryptography Test:" -ForegroundColor Yellow
try {
    $cryptoWarning = python -c "import cryptography; print('Cryptography imported successfully')" 2>&1
    if ($cryptoWarning -match "32-bit Python") {
        Write-Host "  [WARN] 32-bit Python detected - upgrade recommended" -ForegroundColor Red
    }
    elseif ($cryptoWarning -match "successfully") {
        Write-Host "  [OK] Cryptography working optimally" -ForegroundColor Green
    }
    else {
        Write-Host "  [INFO] Cryptography not installed or other issue" -ForegroundColor Blue
    }
}
catch {
    Write-Host "  Error testing cryptography: $($_.Exception.Message)" -ForegroundColor Red
}

# Check virtual environment
Write-Host "`nVirtual Environment:" -ForegroundColor Yellow
if (Test-Path "venv64") {
    Write-Host "  [OK] venv64 directory exists" -ForegroundColor Green
    
    if (Test-Path "venv64\Scripts\activate.ps1") {
        Write-Host "  [OK] Activation script found" -ForegroundColor Green
    }
    else {
        Write-Host "  [FAIL] Activation script missing" -ForegroundColor Red
    }
}
else {
    Write-Host "  [FAIL] venv64 directory not found" -ForegroundColor Red
}

# Check dependency files
Write-Host "`nDependency Files:" -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    $reqCount = (Get-Content "requirements.txt" | Where-Object { $_.Trim() -and -not $_.StartsWith("#") }).Count
    Write-Host "  [OK] requirements.txt found ($reqCount packages)" -ForegroundColor Green
}
else {
    Write-Host "  [FAIL] requirements.txt not found" -ForegroundColor Red
}

if (Test-Path "pyproject.toml") {
    Write-Host "  [OK] pyproject.toml found" -ForegroundColor Green
}
else {
    Write-Host "  [FAIL] pyproject.toml not found" -ForegroundColor Red
}

Write-Host "`n=== To run the upgrade: ===" -ForegroundColor Cyan
Write-Host "  .\upgrade-python-64bit.ps1" -ForegroundColor Green
Write-Host "  .\upgrade-python-64bit.ps1 -Force    # Force reinstall" -ForegroundColor Yellow
Write-Host "  .\upgrade-python-64bit.ps1 -PythonVersion 3.11.9    # Specific version" -ForegroundColor Yellow
