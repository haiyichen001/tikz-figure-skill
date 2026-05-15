#!/usr/bin/env python3
"""
Environment check for tikz-figure-skill.
Detects platform, LaTeX distro, Python deps, and outputs install commands.

Usage: python scripts/check-env.py
Exit: 0=all OK, 1=missing optional, 2=missing required
"""

import os
import sys
import shutil
import subprocess
import platform as plat

REQUIRED_PY_PKGS = []  # core Python: no extras needed
OPTIONAL_PY_PKGS = {
    "pdfplumber": "pip install pdfplumber",
    "fitz": "pip install pymupdf",  # PyMuPDF
    "PIL": "pip install Pillow",
}
LATEX_CMDS = ["pdflatex", "lualatex", "xelatex"]
PDF_TO_PNG_CMDS = ["pdftoppm", "gs", "magick", "convert"]

IS_WIN = plat.system() == "Windows"
IS_MAC = plat.system() == "Darwin"
IS_LINUX = plat.system() == "Linux"

class Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

if IS_WIN:
    Color.RED = Color.GREEN = Color.YELLOW = Color.RESET = Color.BOLD = ""


def check_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def check_py_pkg(import_name: str) -> bool:
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def find_latex() -> list[str]:
    """Find available LaTeX engines."""
    found = []
    for cmd in LATEX_CMDS:
        if check_cmd(cmd):
            found.append(cmd)
    return found


def install_hint_latex() -> str:
    if IS_MAC:
        return "brew install --cask mactex-no-gui"
    elif IS_LINUX:
        return "sudo apt install texlive-full  # or texlive-latex-recommended for minimal"
    else:
        return "Install MiKTeX from https://miktex.org/download or run: winget install MiKTeX.MiKTeX"


def install_hint_pdftoppm() -> str:
    if IS_MAC:
        return "brew install poppler"
    elif IS_LINUX:
        return "sudo apt install poppler-utils"
    else:
        return "Install poppler from https://github.com/oschwartz10612/poppler-windows/releases"


def main():
    issues = 0
    errors = 0

    print(f"{Color.BOLD}=== tikz-figure-skill Environment Check ==={Color.RESET}")
    print(f"Platform: {plat.system()} {plat.release()}")
    print(f"Python: {sys.version.split()[0]}")
    print()

    # 1. LaTeX
    latex = find_latex()
    if not latex:
        print(f"{Color.RED}[MISSING] No LaTeX engine found.{Color.RESET}")
        print(f"  Install: {install_hint_latex()}")
        errors += 1
    else:
        print(f"{Color.GREEN}[OK] LaTeX engines: {', '.join(latex)}{Color.RESET}")

    # 2. PDF to PNG
    png_tool = None
    for cmd in PDF_TO_PNG_CMDS:
        if check_cmd(cmd):
            png_tool = cmd
            break
    if png_tool:
        print(f"{Color.GREEN}[OK] PDF-to-PNG: {png_tool}{Color.RESET}")
    else:
        print(f"{Color.YELLOW}[WARN] No PDF-to-PNG tool. PNG preview unavailable.{Color.RESET}")
        print(f"  Install: {install_hint_pdftoppm()}")
        issues += 1

    # 3. Python packages
    for pkg, install_cmd in OPTIONAL_PY_PKGS.items():
        if check_py_pkg(pkg):
            print(f"{Color.GREEN}[OK] Python: {pkg}{Color.RESET}")
        else:
            print(f"{Color.YELLOW}[WARN] Python: {pkg} missing. Run: {install_cmd}{Color.RESET}")
            issues += 1

    # 4. CJK font check (quick heuristic)
    if not IS_WIN:
        # Check for common CJK fonts on Unix
        try:
            result = subprocess.run(
                ["fc-list", ":lang=zh"], capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip():
                print(f"{Color.GREEN}[OK] CJK fonts available{Color.RESET}")
            else:
                print(f"{Color.YELLOW}[WARN] No CJK fonts detected (Chinese labels may fail){Color.RESET}")
                issues += 1
        except Exception:
            pass
    else:
        print(f"{Color.GREEN}[OK] CJK fonts: Windows (assumed available){Color.RESET}")

    # Summary
    print()
    print(f"{Color.BOLD}=== Summary ==={Color.RESET}")
    if errors == 0 and issues == 0:
        print(f"{Color.GREEN}All checks passed. Ready to generate figures.{Color.RESET}")
        sys.exit(0)
    elif errors == 0:
        print(f"{Color.YELLOW}{issues} warning(s). Figures can be generated but some features limited.{Color.RESET}")
        sys.exit(1)
    else:
        print(f"{Color.RED}{errors} error(s), {issues} warning(s). Fix errors first.{Color.RESET}")
        sys.exit(2)


if __name__ == "__main__":
    main()
