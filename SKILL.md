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
STEP 3 — Quality Inspection (MANDATORY, one command, 15 checks, all WARN):
        python references/inspect.py output.tex output.pdf
        ↓
        Runs 3 sensors — 15 checks total. Single unified report.
        All findings are WARN. No ERROR, no INFO, no PASS/FAIL.
        Never modifies anything. Feeds YOU (the model).
        ↓
STEP 4 — Model Decides (strict — fix as much as possible):
        Read all 3 reports. Default is to FIX, not to skip.
        For each WARN, ask: can this be improved without breaking
        the diagram's structure? If yes, fix it.
        Only skip when: intentional design (tight stack, curved arrow),
        or fixing would break the template's layout.
        │
        Quality dimensions the model evaluates:
        │  Layout: aspect ratio, balance, orphans, content density
        │  Spacing: collision, overflow, edge clip, tight clearance  
        │  Semantics: do inputs/outputs connect? Are labels clear?
        │  Usability: will it fit in a paper column? Is text readable?
        │
        Fix by editing .tex or adjusting template coordinates.
        Re-compile, re-sense. Max 3 rounds.
        ↓
STEP 5 — MANDATORY Fix Loop (at least 1 round):
        After first compile + sensors, you MUST find and fix at least
        one WARN before delivering. Even if all warnings seem minor,
        pick the most impactful one and fix it.
        Re-compile → re-sense → if warnings remain, decide again.
        Deliver only after at least 1 fix round completed.
        ↓
Deliver: .tex + .pdf + .png + inspection summary
```

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
