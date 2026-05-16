#!/usr/bin/env python3
"""
tikz-figure-skill environment check + auto-install.
Detects platform, LaTeX, Python deps. Auto-installs what it can.
Run once on skill startup.

Usage: python scripts/check-env.py
Exit: 0=ready, 1=issues, 2=missing LaTeX (will not work)
"""

import os, sys, shutil, subprocess, platform as plat

REQUIRED_LATEX = ["pdflatex"]

PY_DEPS = {
    "fitz": "pymupdf",        # PDF to PNG
    "pdfplumber": "pdfplumber",  # PDF overlap check
    "PIL": "Pillow",          # Image analysis
}

LATEX_PKGS = [
    "standalone", "tikz", "amsmath", "amssymb",
    "graphicx", "xcolor", "booktabs", "pgfplots",
]

IS_WIN = plat.system() == "Windows"
IS_MAC = plat.system() == "Darwin"

C_RED, C_GRN, C_YEL, C_RST = ("","","","") if IS_WIN else ("\033[91m","\033[92m","\033[93m","\033[0m")

def cmd_ok(name): return shutil.which(name) is not None

def pkg_ok(name):
    try: __import__(name); return True
    except: return False

def latex_hint():
    if IS_MAC: return "brew install --cask mactex-no-gui"
    if IS_WIN: return "winget install MiKTeX.MiKTeX  or  https://miktex.org/download"
    return "sudo apt install texlive-latex-recommended"

def check_kpse(pkg):
    try:
        r = subprocess.run(["kpsewhich", f"{pkg}.sty"], capture_output=True, text=True, timeout=10)
        return r.returncode == 0 and r.stdout.strip() != ""
    except: return False

def main():
    errs = 0; warns = 0
    print(f"{C_YEL}=== tikz-figure-skill Setup ==={C_RST}")
    print(f"Platform: {plat.system()} {plat.release()}")
    print()

    # 1. LaTeX — dealbreaker
    latex = [c for c in REQUIRED_LATEX if cmd_ok(c)]
    if not latex:
        print(f"{C_RED}[MISSING] No LaTeX engine. This skill will not work.{C_RST}")
        print(f"  Install: {latex_hint()}")
        sys.exit(2)
    print(f"{C_GRN}[OK]{C_RST} LaTeX: {', '.join(latex)}")

    # 2. LaTeX packages — check kpsewhich first
    if cmd_ok("kpsewhich"):
        missing = [p for p in LATEX_PKGS if not check_kpse(p)]
        if missing:
            print(f"{C_YEL}[WARN]{C_RST} LaTeX packages missing: {', '.join(missing)}")
            print(f"  pdflatex will auto-install them on first use (MiKTeX) or run: tlmgr install {' '.join(missing)}")
            warns += 1
        else:
            print(f"{C_GRN}[OK]{C_RST} LaTeX packages: all found")
    else:
        print(f"{C_GRN}[OK]{C_RST} LaTeX packages: will auto-install on first compile")

    # 3. Python deps — auto-install
    for imp, pip_name in PY_DEPS.items():
        if pkg_ok(imp):
            print(f"{C_GRN}[OK]{C_RST} Python: {pip_name}")
        else:
            print(f"{C_YEL}[INSTALL]{C_RST} Python: {pip_name} ...", end=" ", flush=True)
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", pip_name, "-q"],
                              capture_output=True, timeout=60)
                if pkg_ok(imp):
                    print(f"{C_GRN}OK{C_RST}")
                else:
                    print(f"{C_RED}FAILED{C_RST}")
                    errs += 1
            except:
                print(f"{C_RED}FAILED (run: pip install {pip_name}){C_RST}")
                errs += 1

    # Summary
    print()
    print(f"{C_YEL}=== Summary ==={C_RST}")
    if errs == 0 and warns == 0:
        print(f"{C_GRN}All checks passed. Ready.{C_RST}")
    elif errs == 0:
        print(f"{C_YEL}{warns} warning(s) — skill works, some features limited.{C_RST}")
    else:
        print(f"{C_RED}{errs} error(s) — fix before using.{C_RST}")
    sys.exit(0 if errs == 0 else 1)

if __name__ == "__main__":
    main()
