# tikz-figure-skill v1.3

A Claude Code skill that generates publication-ready LaTeX/TikZ diagrams with built-in collision detection, PGFPlots data charts, and LuaLaTeX graphdrawing auto-layout. Features a fully integrated tool pipeline with shared parser, auto-fix routing, and cross-platform environment checks.

## Features

- **AI-driven TikZ generation** -- describe your diagram in natural language
- **PGFPlots data charts** -- 6 templates for bar/line/scatter/heatmap/box plots from CSV
- **Graphdrawing auto-layout** -- LuaLaTeX for >15 node graphs: layered/force/circular/tree + edge routing
- **Collision detection (10 checks)** -- Bezier curve math, label gap formulas, edge clipping, boundary clearance
- **Auto-fix pipeline** -- line-crossing triggers `tikz-path-router --auto-fix`, compile failures auto-retry
- **Shared parser** -- `tikz_parser.py` used by all validation/routing tools, no duplicated code
- **Cross-platform** -- macOS/Linux/Windows, `check-env.py` auto-runs on startup
- **context: fork isolation** -- runs in subagent, doesn't pollute main session
- **Academic design system** -- 11-color palette, 9 visual patterns

## Install

```bash
mkdir -p .claude/skills/tikz-figure-skill
cp SKILL.md .claude/skills/tikz-figure-skill/
cp -r references/ .claude/skills/tikz-figure-skill/
cp -r scripts/ .claude/skills/tikz-figure-skill/
```

Optional: run `python scripts/check-env.py` to verify dependencies.

## Quick Start

```
/tikz-figure-skill Draw a 3-layer system architecture with LLM Service,
Agent Harness, and Solver Backend. Include feedback loops.

/tikz-figure-skill --data Generate a grouped bar chart from results.csv

/tikz-figure-skill --draft Quick sketch of a transformer architecture
```

## Output Modes

| Mode | Use case | Validation | Engine |
|------|----------|-----------|--------|
| `--draft` | Quick preview, iterate on layout | Skip | pdflatex |
| `--final` | Production, paper-ready (default) | Full 10 checks + PDF | pdflatex or lualatex |
| `--data` | CSV-driven charts | Data-specific | pdflatex |

## Collision Detection (10 checks + Auto-Layout)

| # | Check | Detects |
|---|-------|---------|
| 1 | Micro-slopes | Diagonal lines that should be axis-aligned |
| 2 | Direction reversal | Arrow midpoints overshoot target |
| 3 | Container overflow | Nodes beyond zone boundaries |
| 4 | Label collision | Overlapping node bounding boxes |
| 5 | Arrow length | Arrows too short (<1.2cm) or too long (>4cm) |
| 6 | **Bezier collision** | Labels inside bent arrow arcs |
| 7 | **Label gaps** | Text too wide for inter-node gap |
| 8 | **Edge clipping** | Elements <0.5cm from canvas edge |
| 9 | **Boundary clearance** | Labels <0.4cm from adjacent shapes |
| 10 | PDF post-checks | Text overlap, line crossing, off-center |
| 11 | **Graphdrawing** | LuaLaTeX auto-layout: layered/force/circular/tree |

## PGFPlots Data Charts

| Template | Chart Type | Input |
|----------|-----------|-------|
| 1 | Bar chart | CSV + column names |
| 2 | Line plot | CSV + x/y columns |
| 3 | Scatter + error bars | CSV + y error columns |
| 4 | Groupplot (multi-panel) | Multiple CSV files |
| 5 | Heatmap matrix | Inline data table |
| 6 | Box plot | Pre-computed quartiles |

## Structure (13 references, ~110 KB)

```
tikz-figure-skill/
  SKILL.md                          -- Main skill definition (~275 lines)
  scripts/
    check-env.py                    -- Cross-platform dependency checker (auto-run)
  references/
    tikz_parser.py                  -- Shared .tex parser (used by all tools)
    tikz-validator.py               -- Pre-compile 10-check validator (auto-run)
    tikz-path-router.py             -- A* auto-routing, accepts --from-tex
    pdf-overlap-checker.py          -- Post-compile PDF overlap detector (auto-run)
    figure-diff.py                  -- SSIM comparison (auto-run if reference exists)
    design-philosophy.md            -- Core design principles + quality gates
    tikz-coding-rules.md            -- Mandatory TikZ conventions
    layout-patterns.md              -- Architecture, pipeline, sequence, 3-column
    visual-patterns.md              -- 9 reusable drawing patterns + font rules
    collision-detection.md          -- Bezier formulas, clearance tables
    pgfplots-templates.md           -- 6 CSV-driven chart templates
    graphdrawing-guide.md           -- LuaLaTeX auto-layout guide
    geometry-math.md                -- Coordinate systems, formulas
```

## Requirements

- LaTeX distribution (MiKTeX / TeX Live / MacTeX)
- Python 3.10+ with `pdfplumber` (optional, for PDF validation)
- Optional: `lualatex` for graphdrawing, `xelatex` for CJK, `pdftoppm` for PNG preview

## Changelog

- **v1.3** — Shared parser `tikz_parser.py` eliminates duplicate code across tools. `tikz-path-router` now accepts `--from-tex` and `--auto-fix`. `tikz-validator` rewritten with clean imports. `geometry-math.md` slimmed to English. SKILL.md: full auto-pipeline (check-env → validate → auto-fix-route → compile → overlap-check → figure-diff).
- **v1.2.1** — Flattened references: 20 → 13 files (-35% files, -62% size)
- **v1.2** — Full YAML frontmatter, `context: fork`, `check-env.py`, 3 modes, auto-retry
- **v1.1** — PGFPlots templates, graphdrawing guide, collision detection
- **v1.0** — Initial release

## Credits

Built on [thesis-figure-skill](https://github.com/0xE1337/thesis-figure-skill) by 0xE1337. Collision detection from [MixtapeTools](https://github.com/scunning1975/MixtapeTools) by scunning1975. License: MIT
