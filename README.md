# tikz-figure-skill

A Claude Code skill that generates publication-ready LaTeX/TikZ diagrams with built-in collision detection. Combines AI-driven TikZ code generation, pre-compilation mathematical gap checks (Bezier curves, label spacing, bounding boxes), and post-compilation PDF overlap validation to ensure zero-collision academic figures.

## Features

- **AI-driven TikZ generation** -- describe your diagram in natural language, get compilable `.tex` code
- **Pre-compilation collision detection** -- 10 mathematical checks before `pdflatex`: Bezier curve arcs, label-to-shape gaps, edge clipping, arrow direction reversal, and more
- **Post-compilation PDF validation** -- `pdf-overlap-checker.py` detects text overlaps, line-crossings, off-center content, and text-line intersections in rendered PDF
- **Dual output formats** -- TikZ for papers (+ CJK support via `xelatex`) and draw.io XML for presentations
- **Academic design system** -- 11-color palette, 9 visual patterns, 44-item review checklist
- **Automatic iteration** -- compile -> validate -> score -> fix loop until 30/30 quality score

## Install

```bash
mkdir -p .claude/skills/tikz-figure-skill
cp SKILL.md .claude/skills/tikz-figure-skill/
cp -r references/ .claude/skills/tikz-figure-skill/
```

Restart Claude Code, then use `/tikz-figure-skill <description>`.

## Quick Start

```
/tikz-figure-skill Draw a 3-layer system architecture with LLM Service,
Agent Harness, and Solver Backend. Include Bezier-curved feedback loops.
```

The skill will:
1. Analyze your description and output a drawing plan
2. Generate TikZ code with academic color scheme
3. Run `tikz-validator.py` for pre-compilation collision detection
4. Compile with `pdflatex`, run `pdf-overlap-checker.py`
5. Convert to PNG and self-score, iterating until collision-free

## Collision Detection (10 checks)

| # | Check | Detects |
|---|-------|---------|
| 1 | Micro-slopes | Diagonal lines that should be axis-aligned |
| 2 | Direction reversal | Arrow midpoints that overshoot the target |
| 3 | Container overflow | Nodes beyond zone boundaries |
| 4 | Label collision | Overlapping node bounding boxes |
| 5 | Arrow length | Arrows too short (<1.2cm) or too long (>4cm) |
| 6 | **Bezier collision** | Labels inside bent arrow arcs (new) |
| 7 | **Label gaps** | Text too wide for inter-node gap (new) |
| 8 | **Edge clipping** | Elements <0.5cm from canvas edge (new) |
| 9 | **Boundary clearance** | Labels <0.4cm from adjacent shapes (new) |
| 10 | PDF post-checks | Text overlap, line crossing, off-center, text-line intersection |

## Structure

```
tikz-figure-skill/
  SKILL.md                          -- Main skill definition
  references/
    collision-detection.md           -- Bezier formulas, clearance tables
    tikz-validator.py                -- Pre-compilation 10-check validator
    pdf-overlap-checker.py           -- Post-compilation PDF overlap detector
    tikz-global-rules.md             -- TikZ coding conventions
    visual-patterns.md               -- 9 reusable visual patterns
    review-checklist.md              -- 44-item visual quality checklist
    data-visualization.md            -- Embedded charts (heatmaps, bar charts, etc.)
    layered-architecture.md          -- Zone alignment, cross-layer connections
    sequence-diagram.md              -- Lifeline spacing, activation bars
    data-pipeline.md                 -- Node shapes, legends, line wrapping
    three-column-mapping.md          -- Three-column coordinate system
    geometry-math.md                 -- Coordinate systems, formula boxes
    drawio-modes.md                  -- 6 draw.io modes (A-F)
    figure-diff.py                   -- SSIM comparison tool
    tikz-path-router.py              -- A*-based automatic path planning
    experience-log.md                -- Accumulated debugging experience
    evolution.md                     -- Verified best-practice parameters
```

## Requirements

- LaTeX distribution (MiKTeX or TeX Live) with `pdflatex`
- Python 3.10+ with `pdfplumber` (`pip install pdfplumber`)
- Optional: `xelatex` for CJK text, `pymupdf` for PDF-to-PNG conversion

## Credits

Built on [thesis-figure-skill](https://github.com/0xE1337/thesis-figure-skill) by 0xE1337, with collision detection rules from [MixtapeTools](https://github.com/scunning1975/MixtapeTools) by scunning1975.

## License

MIT
