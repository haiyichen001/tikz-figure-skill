# tikz-figure-skill: local dependency install (Windows)
# Installs Python packages into skill's .venv/ directory

$ErrorActionPreference = "Stop"
$DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$VENV = "$DIR\.venv"

Write-Host "=== tikz-figure-skill setup ==="

if (-not (Test-Path $VENV)) {
    python -m venv $VENV
    Write-Host "Created local venv: $VENV"
}

$PYTHON = "$VENV\Scripts\python.exe"
& $PYTHON -m pip install -q pymupdf pdfplumber Pillow

Write-Host ""
Write-Host "Dependencies installed into skill directory."
Write-Host "Only LaTeX needs manual install:"
Write-Host "  winget install MiKTeX.MiKTeX"
Write-Host "  or https://miktex.org/download"
