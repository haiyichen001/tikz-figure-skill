---
name: tikz-figure-skill
version: 3.3.0
author: haiyichen
description: |
  Generate publication-ready LaTeX/TikZ diagrams. Template-first always.
  Engine is quality inspector only — never generates diagrams.
when_to_use: |
  Use when user asks to create a figure, diagram, chart, or illustration
  for an academic paper, thesis, report, or publication. Triggers on: 画论文图,
  画架构图, 画流程图, TikZ画图, 论文配图, tikz diagram, latex figure,
  生成tikz, 技术路线图, draw architecture diagram, make a figure for my paper.
  Do NOT trigger on: quick sketch, "show me an example", TikZ syntax questions,
  raster/bitmap tools (Photoshop/Figma/Canva).
allowed-tools:
  - Bash(pdflatex*)
  - Bash(lualatex*)
  - Bash(python*)
  - Read, Write, Edit, Grep, Glob
  - WebSearch, WebFetch
argument-hint: "[diagram description]"
model: opus
tags: [tikz, latex, academic, figure-generation, collision-detection]
user-invocable: true
context: fork
---

# tikz-figure-skill

Template-first always. Engine is quality inspector only — never generates diagrams.

## Before Anything: Environment Setup

On FIRST invocation:

1. If `.venv/` does not exist in the skill directory, run setup:
   `bash setup.sh` (macOS/Linux) or `.\setup.ps1` (Windows)
   This creates a local venv and installs pymupdf, pdfplumber, Pillow inside it.
   Zero system pollution.

2. For all Python commands, use the venv Python directly:
   `SKILL_DIR/.venv/bin/python` (macOS/Linux) or `SKILL_DIR\.venv\Scripts\python` (Windows)
   Each Bash call spawns a fresh shell — absolute venv path is the only reliable way.

3. Verify pdflatex exists. If missing, YOU (Claude) help the user install it.
   You know their OS, package manager, and preferences (conda, brew, apt, winget).
   Use whatever method fits this specific user best — not a hardcoded command.

## Core Workflow (MANDATORY)

```
User describes diagram
        ↓
STEP 1 — Template Match (ALWAYS first, never skip):
        grep -l -i "<keywords>" references/templates/*.tex
        Output matched template list. If zero, broaden keywords.
        ↓
  ├─ FULL MATCH → copy template, edit labels/colors. Compile.
  ├─ PARTIAL MATCH → adapt the closest template skeleton:
  │     rename labels, add/remove nodes, adjust coordinates,
  │     stitch parts from 2+ templates if needed.
  │     If 3 layers → 4: insert new row, shift everything below.
  └─ NO SIMILAR STRUCTURE → still use the most structurally similar
        template as starting skeleton. Never generate from nothing.
        ↓
STEP 2 — Compile: pdflatex. Serial only. Verify .tex exists and >0 bytes.
        ↓
STEP 3 — Inspection (one command, 15 checks, all WARN):
        python references/inspect.py output.tex output.pdf
        ↓
        All 15 checks output WARN only. No ERROR, no PASS/FAIL.
        Never modifies anything. Reports to YOU (the model).
        ↓
STEP 4 — Model Judges Each WARN (template-first mindset):
        For EVERY WARN, go back to the original template and ask:
        "Was this in the template before I touched it?"
        │
        ├─ YES, it's template design intent → SKIP.
        │     Examples: curved residual arrows crossing lines,
        │     tightly stacked ladder steps, long cross-layer arrows,
        │     feedback loops creating line crossings.
        │     These are WHY the template looks good. Don't ruin them.
        │
        └─ NO, it appeared after my edits → FIX.
              Examples: label got longer and overflowed the zone,
              added a layer and nodes now collide,
              changed text and box is now way too wide.
              These are adaptation bugs. Fix them.
        │
        The goal is zero WARNs from adaptation.
        Template-inherited WARNs are acceptable — the human designer
        chose them intentionally.
        │
        Fix by editing .tex or adjusting template coordinates.
        Re-compile, re-inspect. Max 3 rounds.
        ↓
Deliver: .tex + .pdf + .png + inspection summary
```

## What This Skill Can and Cannot Do

| Category | Can do | Cannot do |
|----------|--------|-----------|
| **ML/DL architectures** | Generate directly from 187 templates (Transformer, LSTM, GNN, GAN, VAE, etc.) | Invent new architectures — needs a template to adapt |
| **Custom system architectures** | Build from template skeleton by adapting labels, adding/removing layers | Generate pixel-perfect from scratch without human review |
| **UML diagrams** | Class, sequence, state-machine from pgf-umlsd templates | Complex UML with all edge cases |
| **Flowcharts / pipelines** | Template-adapt or engine-generate with inspection | Guarantee zero warnings on first compile |
| **Data charts (CSV)** | PGFPlots bar, line, scatter, heatmap from data | Interactive or 3D charts |
| **Scientific concept figures** | 111 physics/chemistry figures from janosh/diagrams | Biology pathway diagrams, chemical structures |
| **Quality inspection** | 15 automated checks (collision, overflow, balance, readability) | Judge visual aesthetics — needs human review |
| **Color customization** | Academic palette with all parameters configurable | Match arbitrary brand colors automatically |
| **Hand-drawn / sketch style** | Not supported | Excalidraw, draw.io, Figma style |

## When to Use

- User asks to create a diagram, figure, chart, or illustration
- Output is for a paper, thesis, report, or publication

## When NOT to Use

- Quick sketches, browsing examples, TikZ syntax questions
- Raster tools (Photoshop, Figma, Canva)
- Memes, social media banners
- Data analysis without visualization

## Quality Inspection (one command, 15 checks)

```
python references/inspect.py output.tex output.pdf
```

| Sensor | Checks |
|--------|--------|
| Interference | collision, overflow, edge-clip, tight-clearance, oversize |
| PDF | text overlap, text overflow, off-center, text-line intersection, line crossing |
| Layout | aspect ratio, content density, orphan nodes, balance, font scaling |

All findings are WARN. Model decides. Never modifies anything.

## Template Library (187 verified, 4 sources)

| Source | Stars | Count | Covers |
|--------|-------|-------|--------|
| janosh/diagrams | 488 | 111 | Physics, chemistry, ML concepts |
| PetarV-/TikZ | 1.4K | 43 | GNN, GAN, CNN, RL, graphs |
| pgf-umlsd | CTAN | 22 | UML sequence diagrams |
| NNTikZ + custom | 70 | 11 | Transformer, LSTM, GRU, RNN, CAX-Agent |

## Reference Loading Index

Core tools (shared by sensor suite):
- `references/inspect.py` — unified inspector: one command, 15 checks, all WARN
- `references/tikz_parser.py` — shared .tex parser
- `references/tikz-validator.py` — pre-compile 5 interference checks (sensor)
- `references/pdf-overlap-checker.py` — post-compile PDF check (sensor)
- `references/quality-report.py` — aspect/density/balance/orphans (sensor)
- `references/layout-engine.py` — coordinate calculator (rare, engine fallback)
- `references/figure-diff.py` — SSIM comparison (if reference image exists)

Core (always load):
- `references/tikz-coding-rules.md` — coding conventions
- `references/collision-detection.md` — Bezier formulas, clearance tables
- `references/design-philosophy.md` — design principles
- `references/visual-patterns.md` — drawing patterns

Layout-specific (pick one):
- `references/layout-patterns.md` — architecture, pipeline, sequence
- `references/geometry-math.md` — coordinate systems

Data-specific (optional):
- `references/pgfplots-templates.md` — CSV-driven charts
- `references/graphdrawing-guide.md` — LuaLaTeX layout

## Academic Color Scheme

```latex
\definecolor{acaBlueLine}{HTML}{6080B0}   \definecolor{acaBlueFill}{HTML}{DBEAFE}
\definecolor{acaGreenLine}{HTML}{30A060}  \definecolor{acaGreenFill}{HTML}{A0D0A0}
\definecolor{acaOrangeLine}{HTML}{D06020} \definecolor{acaOrangeFill}{HTML}{FFE6CC}
\definecolor{acaPurpleLine}{HTML}{6020D0} \definecolor{acaPurpleFill}{HTML}{E1D5E7}
\definecolor{acaRedLine}{HTML}{B05050}    \definecolor{acaRedFill}{HTML}{F8CECC}
\definecolor{acaGreyLine}{HTML}{666666}   \definecolor{acaGreyFill}{HTML}{F5F5F5}
```

## Project Structure

```
tikz-figure-skill/
  SKILL.md                       -- Skill definition
  README.md
  install.sh / install.ps1
  scripts/check-env.py           -- Dependency checker
  references/
    tikz-validator.py            -- Pre-compile 11 checks (INSPECTOR)
    pdf-overlap-checker.py       -- Post-compile PDF overlap (INSPECTOR)
    figure-diff.py               -- SSIM comparison
    tikz_parser.py               -- Shared .tex parser
    layout-engine.py             -- Coordinate calculator (rarely used)
    tikz-coding-rules.md         -- Coding conventions
    design-philosophy.md         -- Design principles
    collision-detection.md       -- Bezier formulas
    layout-patterns.md           -- Layout rules
    visual-patterns.md           -- Drawing patterns
    pgfplots-templates.md        -- Data chart templates
    graphdrawing-guide.md        -- LuaLaTeX guide
    geometry-math.md             -- Coordinate systems
    templates/                   -- 187 verified .tex templates
```

## Credits

Templates: janosh/diagrams (488*), PetarV-/TikZ (1.4K*), NNTikZ (70*), pgf-umlsd (CTAN).
Validation: MixtapeTools (scunning1975). Built on thesis-figure-skill (0xE1337).
License: MIT
