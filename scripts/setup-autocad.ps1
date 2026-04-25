# One-shot setup for the autocad-mcp server.
# Run from the repo root:  powershell -ExecutionPolicy Bypass -File scripts\setup-autocad.ps1
#
# What it does:
#   1. Creates .venv/ using the first Python >= 3.10 it finds
#   2. Installs requirements.txt
#   3. Generates the win32com typelib cache for AutoCAD (makemepy), so
#      early-bound COM calls are fast and IntelliSense-friendly.
#
# Requirements on the target machine:
#   - Windows with AutoCAD (full, not LT) installed and licensed
#   - Python 3.10+

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "==> Locating Python 3.10+" -ForegroundColor Cyan
$pythons = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythons += @("py -3.12", "py -3.11", "py -3.10")
}
$pythons += @("python", "python3")

$python = $null
foreach ($candidate in $pythons) {
    try {
        $ver = & cmd /c "$candidate --version 2>&1"
        if ($ver -match "Python 3\.(1[0-9]|[2-9][0-9])") {
            $python = $candidate
            Write-Host "    using: $candidate  ($ver)" -ForegroundColor Green
            break
        }
    } catch {}
}
if (-not $python) { throw "Need Python 3.10+ on PATH (or via 'py' launcher)" }

Write-Host "==> Creating .venv" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    & cmd /c "$python -m venv .venv"
}

$venvPy = ".venv\Scripts\python.exe"

Write-Host "==> Upgrading pip + installing requirements" -ForegroundColor Cyan
& $venvPy -m pip install --upgrade pip --quiet
& $venvPy -m pip install -r autocad-mcp\requirements.txt

Write-Host "==> Running pywin32 post-install (needed once per venv)" -ForegroundColor Cyan
$pywin32PostInstall = ".venv\Scripts\pywin32_postinstall.py"
if (Test-Path $pywin32PostInstall) {
    & $venvPy $pywin32PostInstall -install 2>&1 | Out-Null
}

Write-Host "==> Generating AutoCAD typelib cache (makepy)" -ForegroundColor Cyan
$makepy = @"
import win32com.client.makepy as m
# AutoCAD 2026 = AutoCAD.Application.26, older versions auto-detect by ProgID
try:
    m.GenerateFromTypeLibSpec('AutoCAD.Application')
    print('typelib cache generated')
except Exception as e:
    print(f'typelib cache skipped: {e}')
"@
$makepy | & $venvPy -

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Start AutoCAD, then restart Claude Code - it will pick up .mcp.json automatically." -ForegroundColor Yellow
