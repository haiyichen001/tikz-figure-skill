---
name: tikz-figure-skill
version: 1.2.0
author: haiyichen
description: |
  Generate publication-ready LaTeX/TikZ diagrams with built-in collision detection.
  Combines AI-driven TikZ code generation, pre-compilation mathematical gap checks
  (Bezier curves, label spacing, bounding boxes), post-compilation PDF overlap validation,
  and PGFPlots data charts from CSV. Supports LuaLaTeX graphdrawing auto-layout for
  complex graphs. Zero-collision academic figures by default.
  Triggers when user says: 画论文图, 画架构图, 画流程图, TikZ画图, 论文配图,
  tikz diagram, latex figure, 生成tikz, 技术路线图, draw architecture diagram,
  make a figure, generate TikZ code, 画个图, 帮我画图.
allowed-tools:
  - Bash(pdflatex*)
  - Bash(lualatex*)
  - Bash(xelatex*)
  - Bash(python*)
  - Bash(pdftoppm*)
  - Bash(gs*)
  - Bash(magick*)
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - WebSearch
  - WebFetch
argument-hint: "[diagram description | --draft | --final | --data]"
model: opus
tags:
  - tikz
  - latex
  - academic
  - figure-generation
  - pgfplots
  - data-visualization
  - collision-detection
user-invocable: true
context: fork
---

# tikz-figure-skill

Generate publication-quality LaTeX/TikZ diagrams with automated collision detection, PGFPlots data charts, and LuaLaTeX graphdrawing auto-layout. Works cross-platform (macOS/Linux/Windows).

## Quickstart

Say `/tikz-figure-skill Draw a 3-layer system architecture with LLM Service, Agent Harness, and Solver Backend` and the skill will:

1. Analyze → output drawing plan
2. Auto-detect platform and available LaTeX engines
3. Generate TikZ code with academic color scheme
4. Run pre-compilation collision validator
5. Compile → run PDF overlap checker → self-score → iterate until clean

## Output Modes

| Mode | Trigger | Compile | Validate | Engines |
|------|---------|---------|----------|---------|
| `--draft` | Quick preview | 1 pass, skip bibtex | Skip validation | pdflatex only |
| `--final` (default) | Production quality | 2 passes | Full 10 checks + PDF overlap | pdflatex or lualatex |
| `--data` | CSV-driven charts | 1 pass | Data-specific checks | pdflatex |

Modes auto-select based on context. Complex architectures (>15 nodes) default to LuaLaTeX graphdrawing.

## Environment Check (auto-run before first compile)

The skill auto-detects missing dependencies. Run manually anytime:

```bash
python scripts/check-env.py
```
```powershell
python scripts\check-env.py
```

Required: `pdflatex` (or `lualatex`). Optional: `pdftoppm` for PNG, Python `pdfplumber`/`pymupdf` for validation.

## Core Workflow

```
User Input (text / sketch / paper excerpt)
    ↓
Step 1 — Analyze & Plan: identify domain, extract modules, plan layout, choose format
    ↓
Step 2 — Load References: match chart type → load template + collision rules + patterns
    ↓
Step 3 — Generate Code: TikZ .tex or draw.io .xml
    ↓
Step 3.5b — Pre-compile Validate: run tikz-validator.py (10 checks)
    ↓
Step 4 — Compile: pdflatex (or lualatex for graphdrawing)
    ↓
Step 5 — Post-compile Validate: run pdf-overlap-checker.py, render PNG, self-score
    ↓
Step 6 — Recover: if compile/validation fails, diagnose root cause, fix, re-run (max 3 retries)
    ↓
Deliver: .tex + .pdf + .png + QA report
```

## Auto-Retry & Recovery

If compilation fails, the skill does NOT ask the user to fix it. Instead:

1. **Parse compiler log** — extract error line, missing package, undefined command
2. **Diagnose category**: missing package, syntax error, font issue, incompatible engine
3. **Apply fix**: install package (`tlmgr install`), switch engine (pdflatex→lualatex), fix syntax
4. **Re-compile** — max 3 attempts per error category
5. **Escalate** — if 3 attempts fail, report exact error + attempted fixes to user

If collision validation fails, iterate on coordinates up to 3 rounds, then report remaining warnings.

## Design Philosophy

The full design philosophy is in `references/design-philosophy.md`. Core rules:

- Think like a designer, not a programmer stacking code
- Information density >= 30 visual elements
- >= 3 levels of visual hierarchy (hero boxes >=5cm vs standard vs tiny)
- >= 3 line types (thick data flow, solid control, dashed feedback)
- Zone backgrounds with stage labels
- Compact density — "just enough to breathe"

## Collision Detection (10 checks, auto-run pre-compile)

Loaded from `references/collision-detection.md`. Run manually:
```bash
python references/tikz-validator.py file.tex        # pre-compile
python references/pdf-overlap-checker.py file.pdf   # post-compile
```

Checks: micro-slopes, direction reversal, container overflow, label collision, arrow length, **Bézier arc labels**, **label-to-gap fit**, **edge clipping**, **boundary clearance**, PDF text/line overlap.

## PGFPlots Data Charts (6 templates)

Loaded from `references/pgfplots-templates.md`. CSV → compilable chart. Templates: bar chart (`ybar`), line plot, scatter+error bars, groupplot (multi-panel), heatmap matrix, box plot. All use academic palette, enforce chart design rules (no chartjunk, grey grid, left-only axes).

## Graphdrawing Auto-Layout

Loaded from `references/graphdrawing-guide.md`. For diagrams with >15 nodes, switch to LuaLaTeX + graphdrawing. Algorithms: layered (hierarchical), spring (force-based), circular, tree. Edge routing auto-avoids nodes.

Auto-switch rules:
```
if node_count <= 15:  pdflatex, manual coords, run tikz-validator
elif node_count <= 40: lualatex, layered layout
else:                  lualatex, spring layout + edge routing
```

## Tool Boundaries

| Dimension | TikZ | draw.io |
|-----------|------|---------|
| Best for | Architecture, data flow, math, paper embedding | Roadmaps, decorative presentations |
| Precise control | Absolute coords + relative positioning | Drag-edit, less precise |
| CJK support | xelatex + fontspec | Native |
| Math formulas | Native LaTeX | MathJax, mediocre |
| Visual effects | Limited (no gradient, basic shadow) | Rich (gradient, shadow, 3D) |
| Compile validation | xelatex/pdflatex + pdftoppm | drawio CLI → PDF → PNG |

Default to TikZ. Use draw.io only when: user requests it, needs heavy gradients/3D, or for decorative presentation slides (not papers).

## Academic Color Scheme

```latex
% Blues
\definecolor{acaBlueLine}{HTML}{6080B0}   \definecolor{acaBlueFill}{HTML}{DBEAFE}
% Greens
\definecolor{acaGreenLine}{HTML}{30A060}  \definecolor{acaGreenFill}{HTML}{A0D0A0}
% Oranges
\definecolor{acaOrangeLine}{HTML}{D06020} \definecolor{acaOrangeFill}{HTML}{FFE6CC}
% Purples
\definecolor{acaPurpleLine}{HTML}{6020D0} \definecolor{acaPurpleFill}{HTML}{E1D5E7}
% Reds
\definecolor{acaRedLine}{HTML}{B05050}    \definecolor{acaRedFill}{HTML}{F8CECC}
% Greys
\definecolor{acaGreyLine}{HTML}{666666}   \definecolor{acaGreyFill}{HTML}{F5F5F5}
% Zones
\definecolor{zoneBlueBg}{HTML}{E8EEF8}    \definecolor{zoneGreenBg}{HTML}{ECFDF5}
\definecolor{zoneRedBg}{HTML}{F8E8E8}
```

## Chart Type → Layout → File Map

| Chart Type | Layout | Reference File |
|------------|--------|---------------|
| System architecture | Bottom-up layered | `references/layered-architecture.md` |
| Protocol/flowchart | Left→right or top→down | `references/data-pipeline.md` |
| Sequence diagram | Multi-column lifelines | `references/sequence-diagram.md` |
| 3-column mapping | Left-center-right | `references/three-column-mapping.md` |
| Geometry/math | Coordinate + geometric | `references/geometry-math.md` |
| Data visualization mix | Block + embedded charts | `references/data-visualization.md` |
| PGFPlots bar/line/scatter | CSV → `\addplot table` | `references/pgfplots-templates.md` |
| Graphdrawing auto-layout | LuaLaTeX algorithm | `references/graphdrawing-guide.md` |
| Roadmaps (decorative) | draw.io modes A-F | `references/drawio-modes.md` |

## Reference Loading Index

Must load matching reference per chart type. All TikZ figures must also load:
- `references/collision-detection.md` (pre-compile collision rules)
- `references/visual-patterns.md` (9 reusable drawing patterns)
- `references/design-philosophy.md` (design principles)

Quality gates loaded at step 5:
- `references/review-checklist.md` (44-item visual QA)
- `references/figure-diff.py` (SSIM comparison for reference-based work)

Post-completion:
- `references/experience-log.md` (read existing + append new)
- `references/evolution.md` (verified best-practice parameters)

## Quality Gates

Deliver only when 30/30 on the review checklist. The anti-cheat: after scoring, ask "what would a reviewer catch?" and fix anything found. If 3 rounds of iteration don't reach 30/30, the layout approach itself is wrong — restart from Step 1, don't keep patching.

## Cross-Platform Notes

| Platform | LaTeX | Font for CJK | PDF→PNG |
|----------|-------|-------------|---------|
| macOS | `pdflatex` (MacTeX) | PingFang SC | `pdftoppm` (poppler) |
| Linux | `pdflatex` (TeX Live) | Noto Sans CJK SC | `pdftoppm` (poppler) |
| Windows | `pdflatex` (MiKTeX) | SimHei / Microsoft YaHei | `pdftoppm` or `magick` |

Python scripts use `python` or `python3` based on platform auto-detection. Paths use `os.path` or `/` which works cross-platform in modern tools.

## Quick Compile Templates

### Minimal standalone TikZ (architecture)
```latex
\documentclass[tikz,border=15pt]{standalone}
\usepackage{tikz}
\usetikzlibrary{arrows.meta, positioning, fit, backgrounds, calc, shadows}
% Insert academic color definitions here
\begin{document}
\begin{tikzpicture}[
    box/.style={rectangle,rounded corners=3pt,align=center,minimum height=0.85cm,
        inner sep=8pt,line width=1.0pt,font=\footnotesize\sffamily},
    arr/.style={->,>=Stealth,line width=1.0pt,color=black!60},
]
% Nodes and edges
\end{tikzpicture}
\end{document}
```

### Minimal standalone PGFPlots (data chart)
```latex
\documentclass[tikz,border=10pt]{standalone}
\usepackage{pgfplots}\pgfplotsset{compat=1.18}
% Insert academic color definitions here
\begin{document}
\begin{tikzpicture}
\begin{axis}[
    width=8cm,height=5cm,ybar,bar width=0.6cm,
    enlarge x limits=0.3,ymin=0,
    grid=major,grid style={gray!25,dashed},axis lines=left,
]
\addplot[draw=acaBlueLine,fill=acaBlueFill!60] table[x expr=\coordindex,y=Value] {data.csv};
\end{axis}
\end{tikzpicture}
\end{document}
```

## Project Structure

```
tikz-figure-skill/
  SKILL.md                          -- Main skill definition (<500 lines)
  scripts/
    check-env.py                    -- Cross-platform dependency checker
  references/
    design-philosophy.md            -- Core design principles
    collision-detection.md          -- Bezier formulas, clearance tables
    pgfplots-templates.md           -- 6 CSV-driven chart templates
    graphdrawing-guide.md           -- LuaLaTeX auto-layout guide
    tikz-validator.py               -- Pre-compile 10-check validator
    pdf-overlap-checker.py          -- Post-compile PDF overlap detector
    tikz-global-rules.md            -- TikZ coding conventions
    visual-patterns.md              -- 9 reusable visual patterns
    review-checklist.md             -- 44-item visual quality checklist
    data-visualization.md           -- Embedded charts (heatmap, bars)
    layered-architecture.md         -- Zone alignment, cross-layer
    sequence-diagram.md             -- Lifeline spacing
    data-pipeline.md                -- Node shapes, legends
    three-column-mapping.md         -- Three-column coords
    geometry-math.md                -- Coordinate systems, formulas
    drawio-modes.md                 -- 6 draw.io modes (A-F)
    figure-diff.py                  -- SSIM comparison tool
    tikz-path-router.py             -- A* path planning
    experience-log.md               -- Debugging experience
    evolution.md                    -- Best-practice parameters
```

## Credits

Built on [thesis-figure-skill](https://github.com/0xE1337/thesis-figure-skill) by 0xE1337.
Collision detection rules from [MixtapeTools](https://github.com/scunning1975/MixtapeTools) by scunning1975.
PGFPlots patterns from [TUGboat](https://tug.org/TUGboat/tb31-1/tb97wright-pgfplots.pdf) and [Overleaf guides](https://www.overleaf.com/learn/latex/Pgfplots_package).
Graphdrawing from [TikZ/PGF manual](https://tikz.dev/gd).
License: MIT
