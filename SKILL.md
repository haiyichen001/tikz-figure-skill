---
name: tikz-figure-skill
version: 2.0.0
author: haiyichen
description: |
  Generate publication-ready LaTeX/TikZ diagrams with built-in collision detection,
  PGFPlots data charts, and LuaLaTeX graphdrawing auto-layout. Zero-collision academic
  figures by default.
when_to_use: |
  Use when the user explicitly asks to create a figure, diagram, chart, or illustration
  for an academic paper, thesis, report, or publication. Triggers on: 画论文图, 画架构图,
  画流程图, TikZ画图, 论文配图, tikz diagram, latex figure, 生成tikz, 技术路线图,
  draw architecture diagram, make a figure for my paper, generate TikZ code, 画个图,
  帮我画图, pgfplots chart from data, CSV to bar chart.
  Do NOT trigger on: quick sketch, whiteboard doodle, "show me an example", general
  questions about TikZ syntax (use WebSearch instead), or user explicitly wanting a
  raster/bitmap tool like Photoshop/Figma/Canva.
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

## When to Use

- User explicitly asks to create a diagram, figure, chart, or illustration
- The output is for a paper, thesis, report, slide deck, or publication
- User provides a paper excerpt, data file (CSV), or architectural description
- User wants TikZ code, pgfplots chart, or LuaLaTeX graphdrawing

## When NOT to Use

- **Quick sketch / whiteboard doodle** — this skill does full validation pipeline, overkill for napkin sketches
- **"Show me an example of X"** — user is browsing, not requesting a figure
- **General TikZ syntax questions** — use WebSearch, don't load the entire skill
- **Raster/bitmap tools** — user explicitly wants Photoshop, Figma, Canva, or similar
- **Non-academic graphics** — memes, social media banners, casual illustrations
- **Data analysis without visualization** — user wants statistics, not charts
- **Already-rendered figure review** — user has a PNG and wants feedback on it (not generating)

## Quickstart

Say `/tikz-figure-skill Draw a 3-layer system architecture` and the skill will:

1. **Env check** — auto-run `scripts/check-env.py`, detect LaTeX/Python/fonts
2. **Analyze** — output drawing plan with module list + layout strategy
3. **Generate** — produce TikZ `\graph` syntax. lualatex + graphdrawing computes all node positions and edge routes at compile time via Sugiyama layered layout. No manual coordinates. No overlap. No edge-crossing-boxes.
4. **Validate** — `tikz-validator.py` (10 checks)
5. **Compile** — lualatex (default, for graphdrawing support) or pdflatex fallback, auto-retry on failure (max 3)
6. **Post-check** — `pdf-overlap-checker.py`, if reference image exists → auto-call `figure-diff.py`
7. **Deliver** — .tex + .pdf + .png + validation report

## Output Modes

| Mode | Trigger | Compile | Validate | Engine |
|------|---------|---------|----------|--------|
| `--draft` | Quick preview | 1 pass | Skip | pdflatex |
| `--final` (default) | Production | 2 passes | Full 10 + PDF | **lualatex** (graphdrawing) |
| `--data` | CSV charts | 1 pass | Data checks | pdflatex |

Default engine is **lualatex** for automatic graphdrawing layout and edge routing. Falls back to pdflatex if lualatex unavailable (losing graphdrawing features).

## Environment Check (auto-run on skill startup)

Skill automatically runs `scripts/check-env.py` on first invocation. Reports: LaTeX engines found, PDF-to-PNG tool, Python deps, CJK fonts. Missing optional deps show install hints. Missing required deps (pdflatex) block skill execution.

Run manually: `python scripts/check-env.py`

## Core Workflow

```
User Input (text / sketch / paper excerpt)
    ↓
Step 1 — Analyze & Plan: identify domain, extract modules, plan layout, choose format
    ↓
Step 2 — Load References: match chart type → load template + collision rules + patterns
    ↓
Step 3 — Generate Code: TikZ `\graph` syntax `.tex`
    ↓
Step 3.5b — Pre-compile Validate: run tikz-validator.py (10 checks)
    ↓
Step 4 — Compile: lualatex (auto graphdrawing layout + edge routing)
    ↓
Step 5 — Post-compile Validate: run pdf-overlap-checker.py, render PNG, self-score
    ↓
Step 6 — Recover: if compile/validation fails, diagnose root cause, fix, re-run (max 3 retries)
    ↓
Deliver: .tex + .pdf + .png + QA report
```

## Auto-Retry & Recovery (AI-driven, not hardcoded)

Compile errors and validation warnings are handled by Claude intelligently:

### Compile Error Recovery
1. **Parse compiler log** — extract error line, missing package, undefined command
2. **Diagnose category**: missing package, syntax error, font issue, incompatible engine
3. **Apply fix**: install package (`tlmgr install`), switch engine (pdflatex→lualatex), fix syntax
4. **Re-compile** — max 3 attempts per error category
5. **Escalate** — if 3 attempts fail, report exact error + attempted fixes to user

### Validation Auto-Fix Loop (crucial)

After generating .tex, YOU MUST run the validator and act on its output:

```bash
python references/tikz-validator.py output.tex
```

Read the validator output carefully. **Do not ignore warnings.** For each warning:

| Warning Type | What Claude Should Do |
|---|---|
| `short-arrow` / `collision` / `tight-clearance` | Increase `row_gap` or `column_gap` in the JSON spec, or adjust node `x` positions in `groups`. Re-generate. |
| `overflow` | Expand zone boundaries by adjusting group `x` spacing or increasing `column_gap`. |
| `oversize` | Remove `minimum width`/`minimum height` from the style, or reduce to match text. |
| `bezier-collision` / `line-crossing` | Re-route edges using `-|`/`|-` paths, or add intermediate rail nodes. |
| `edge-clip` | Increase `canvas.border` or move nodes inward. |
| `label-gap` | Shorten label text, move it above/below the edge, or widen the gap between source and target nodes. |

**Loop**: generate → validate → read warnings → adjust spec → re-generate. Max 3 iterations. If warnings persist after 3 rounds, report them to the user but deliver the best version achieved.

**Goal**: 0 errors, minimal warnings. This loop is what makes the skill "zero-collision" — it's Claude intelligently fixing issues the validator finds, not a hardcoded script.

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
if node_count <= 15:  lualatex, layered layout (simple)
elif node_count <= 40: lualatex, layered layout (dense)
else:                  lualatex, spring layout + edge routing
```

## Output Format

Output is always standalone `.tex` with `\graph` syntax, compiled with lualatex.
For data charts, output uses pgfplots (works with lualatex and pdflatex).

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
| System architecture | Bottom-up layered | `references/layout-patterns.md` |
| Protocol/flowchart | Left→right or top→down | `references/layout-patterns.md` |
| Sequence diagram | Multi-column lifelines | `references/layout-patterns.md` |
| 3-column mapping | Left-center-right | `references/layout-patterns.md` |
| Geometry/math | Coordinate + geometric | `references/geometry-math.md` |
| Embedded visualizations | TikZ-native plots | `references/visual-patterns.md` |
| PGFPlots bar/line/scatter | CSV → `\addplot table` | `references/pgfplots-templates.md` |
| Graphdrawing auto-layout | LuaLaTeX layered/spring/circular/tree | `references/graphdrawing-guide.md` |

## Reference Loading Index

All TikZ figures must load:
- `references/collision-detection.md` — pre-compile collision rules + Bezier formulas
- `references/tikz-coding-rules.md` — **Rule 0: always use graphdrawing `\graph` syntax. No manual coordinates.**
- `references/visual-patterns.md` — reusable drawing patterns (>=3 per figure)
- `references/design-philosophy.md` — design principles + quality gates

Layout-specific (pick one):
- `references/layout-patterns.md` — architecture, pipeline, sequence, 3-column mapping
- `references/geometry-math.md` — coordinate systems, formula boxes

Data-specific (optional):
- `references/pgfplots-templates.md` — CSV-driven bar/line/scatter/heatmap/box plots
- `references/graphdrawing-guide.md` — LuaLaTeX automatic layout

## Built-in Templates (19 diagrams — bypass layout engine)

Template library sourced from NNTikZ (70 stars, MIT) and PetarV-/TikZ (1.4K stars).
Use directly when user requests canonical architectures. All use academic color scheme.

| Template File | Diagram |
|---|---|
| `references/templates/transformer.tex` | Transformer Encoder-Decoder (Attention Is All You Need) |
| `references/templates/multihead_attention.tex` | Multi-Head Attention mechanism detail |
| `references/templates/hybrid_transformer_mamba.tex` | Hybrid: Transformer Encoder + Mamba Decoder |
| `references/templates/encoder_only.tex` | Encoder-only Transformer (BERT-style) |
| `references/templates/decoder_only.tex` | Decoder-only Transformer (GPT-style) |
| `references/templates/rnn_encoder_decoder_sutskever.tex` | RNN Seq2Seq with Attention |
| `references/templates/lstm.tex` | LSTM cell internal structure |
| `references/templates/gru.tex` | GRU cell internal structure |
| `references/templates/rnn.tex` | Recurrent Neural Network unrolled |
| `references/templates/neural_network.tex` | Feedforward neural network |
| `references/templates/dropout.tex` | Dropout regularization illustration |
| `references/templates/gat_layer.tex` | Graph Attention Network layer |
| `references/templates/2d_convolution.tex` | 2D Convolution operation |
| `references/templates/convolutional_autoencoder.tex` | Convolutional Autoencoder |
| `references/templates/cyclegan.tex` | CycleGAN architecture |
| `references/templates/1d-2d_cross-connection.tex` | 1D-2D cross-connection |
| `references/templates/bidirectional_long_short-term_memory.tex` | Bidirectional LSTM |
| `references/templates/deep_belief_network.tex` | Deep Belief Network |
| `references/templates/fully-connected_cross-connection.tex` | Fully-connected cross-connection |

**When to use template vs layout engine:**
Canonical DL architectures (Transformer, LSTM, GRU, CNN, GAN, etc.) → use template directly, customize colors/text. Custom pipeline/flowchart/novel architecture → layout-engine.py with JSON spec.

Quality tools (all based on shared `references/tikz_parser.py`):
- `references/tikz-validator.py` — pre-compile 10 checks (auto-run step 4)
- `references/pdf-overlap-checker.py` — post-compile PDF overlap (auto-run step 6)
- `references/figure-diff.py` — SSIM comparison, triggered if reference image provided (step 6)

## Quality Gates

Self-score after PNG render. Minimum pass: no ERROR items, <= 3 WARN items. If 3 rounds of iteration don't pass, the layout approach itself is wrong — restart from Step 1.

## Cross-Platform Notes

| Platform | LaTeX | Font for CJK | PDF→PNG |
|----------|-------|-------------|---------|
| macOS | `pdflatex` (MacTeX) | PingFang SC | `pdftoppm` (poppler) |
| Linux | `pdflatex` (TeX Live) | Noto Sans CJK SC | `pdftoppm` (poppler) |
| Windows | `pdflatex` (MiKTeX) | SimHei / Microsoft YaHei | `pdftoppm` or `magick` |

Python scripts use `python` or `python3` based on platform auto-detection. Paths use `os.path` or `/` which works cross-platform in modern tools.

## Quick Compile Templates

### Minimal standalone (graphdrawing)
```latex
\documentclass[tikz,border=15pt]{standalone}
\usepackage{tikz,amsmath,amssymb}
\usetikzlibrary{graphs,graphdrawing,arrows.meta}
\usegdlibrary{layered}
\begin{document}
\begin{tikzpicture}[arr/.style={->,>=Stealth,thick,color=black!55}]
% Style definitions
\tikzset{box/.style={rectangle,rounded corners=4pt,align=center,
    inner sep=8pt,font=\footnotesize\sffamily,draw=blue,fill=blue!10}}
\graph[layered layout, grow=right,
       level distance=2.5cm, sibling distance=1cm,
       nodes={align=center,inner sep=6pt,font=\footnotesize\sffamily},
       edges={arr}] {
    input/"Input" [box] -> process/"Process" [box] -> output/"Output" [box];
};
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
  SKILL.md                          -- Main skill definition
  scripts/
    check-env.py                    -- Cross-platform dependency checker (auto-run)
  references/
    tikz_parser.py                  -- Shared .tex parser (used by all tools)
    tikz-validator.py               -- Pre-compile 10-check validator (auto-run)
    layout-engine.py                -- JSON spec → \graph .tex generator
    pdf-overlap-checker.py          -- Post-compile PDF overlap detector (auto-run)
    figure-diff.py                  -- SSIM comparison (auto-run if reference exists)
    design-philosophy.md            -- Core design principles + quality gates
    tikz-coding-rules.md            -- Rule 0: graphdrawing syntax mandatory
    layout-patterns.md              -- Sequence diagram style definitions
    visual-patterns.md              -- 9 reusable drawing patterns + font rules
    collision-detection.md          -- Bezier formulas, clearance tables
    pgfplots-templates.md           -- 6 CSV-driven chart templates
    graphdrawing-guide.md           -- LuaLaTeX auto-layout guide
    geometry-math.md                -- Coordinate systems, formulas
```

## Credits

Built on [thesis-figure-skill](https://github.com/0xE1337/thesis-figure-skill) by 0xE1337.
Collision detection rules from [MixtapeTools](https://github.com/scunning1975/MixtapeTools) by scunning1975.
PGFPlots patterns from [TUGboat](https://tug.org/TUGboat/tb31-1/tb97wright-pgfplots.pdf) and [Overleaf guides](https://www.overleaf.com/learn/latex/Pgfplots_package).
Graphdrawing from [TikZ/PGF manual](https://tikz.dev/gd).
License: MIT
