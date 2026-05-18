#!/usr/bin/env bash
# tikz-figure-skill: local dependency install
# Installs Python packages into skill's vendor/ directory (no system changes)

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"

echo "=== tikz-figure-skill setup ==="

# Create local venv if not exists
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
    echo "Created local venv: $VENV"
fi

# Activate and install
source "$VENV/bin/activate" 2>/dev/null || source "$VENV/Scripts/activate" 2>/dev/null
pip install -q pymupdf pdfplumber Pillow

echo ""
echo "Dependencies installed into skill directory."
echo "Only LaTeX needs manual install:"
echo "  macOS: brew install --cask mactex-no-gui"
echo "  Linux: sudo apt install texlive-latex-recommended"
echo "  Windows: winget install MiKTeX.MiKTeX"
