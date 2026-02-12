# -*- coding: utf-8 -*-
# Unciv Referee Tool - Build Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Unciv Referee Tool - Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# [1/3] Check Python environment
Write-Host "[1/3] Checking Python environment..." -ForegroundColor Yellow
$pythonPath = Get-Command python -ErrorAction SilentlyContinue

if (-not $pythonPath) {
    Write-Host "Error: Python not found, please install Python first" -ForegroundColor Red
    Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Python found at: $($pythonPath.Source)" -ForegroundColor Green
python --version
Write-Host ""

# [2/3] Install PyInstaller
Write-Host "[2/3] Installing PyInstaller..." -ForegroundColor Yellow
python -m pip install pyinstaller --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: PyInstaller installation failed, trying to continue..." -ForegroundColor Yellow
}
Write-Host ""

# [3/3] Build executable
Write-Host "[3/3] Building executable..." -ForegroundColor Yellow
Write-Host "Compiling, this may take a few minutes, please wait..." -ForegroundColor Cyan
Write-Host ""

python -m PyInstaller --onefile --name "UncivRefereeTool" --clean --noconfirm "Unciv联机游戏数据提取.py"

Write-Host ""
if (Test-Path "dist\UncivRefereeTool.exe") {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Output: dist\UncivRefereeTool.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "1. Copy exe to any location"
    Write-Host "2. First run will generate config files"
    Write-Host "3. Modify config as needed"
    Write-Host "4. Run program again to use"
    Write-Host ""
    Read-Host "Press Enter to open output folder"
    explorer "dist"
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Build failed, please check error messages above" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

Read-Host "Press Enter to exit"