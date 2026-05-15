# tikz-figure-skill v1.2

A Claude Code skill that generates publication-ready LaTeX/TikZ diagrams with built-in collision detection, PGFPlots data charts, and LuaLaTeX graphdrawing auto-layout. Zero-collision academic figures by default.

## Features

- **AI-driven TikZ generation** -- describe your diagram in natural language
- **PGFPlots data charts** -- 6 templates for bar/line/scatter/heatmap/box plots from CSV
- **Graphdrawing auto-layout** -- LuaLaTeX for >15 node graphs: layered/force/circular/tree + edge routing
- **Collision detection (10 checks)** -- Bezier curve math, label gap formulas, edge clipping, boundary clearance
- **Post-compile PDF validation** -- text overlap, line-crossings, off-center detection
- **Auto-retry & recovery** -- compile errors auto-diagnosed and fixed, max 3 rounds before escalation
- **3 output modes** -- `--draft` (fast preview), `--final` (full QA), `--data` (CSV chart mode)
- **Cross-platform** -- macOS/Linux/Windows, auto-detects LaTeX distro, CJK fonts
- **context: fork isolation** -- runs in subagent, doesn't pollute main session
- **Academic design system** -- 11-color palette, 9 visual patterns, 44-item review checklist

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

## Structure

```
tikz-figure-skill/
  SKILL.md                          -- Main skill definition (299 lines)
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

## Requirements

- LaTeX distribution (MiKTeX / TeX Live / MacTeX)
- Python 3.10+ with `pdfplumber` (optional, for PDF validation)
- Optional: `lualatex` for graphdrawing, `xelatex` for CJK, `pdftoppm` for PNG preview

## Changelog

- **v1.2** — Full YAML frontmatter (version/author/allowed-tools/model/tags), SKILL.md slimmed to 299 lines, `context: fork` isolation, `scripts/check-env.py` cross-platform checker, 3 output modes, auto-retry on compile failure, `references/design-philosophy.md`
- **v1.1** — PGFPlots 6 templates, graphdrawing auto-layout guide, collision detection references
- **v1.0** — Initial release: thesis-figure-skill base + collision detection (10 checks in tikz-validator.py)

## Credits

Built on [thesis-figure-skill](https://github.com/0xE1337/thesis-figure-skill) by 0xE1337. Collision detection from [MixtapeTools](https://github.com/scunning1975/MixtapeTools) by scunning1975. License: MIT
