# tikz-figure-skill

A Claude Code skill that generates publication-ready LaTeX/TikZ diagrams with built-in collision detection. Combines AI-driven TikZ code generation, pre-compilation mathematical gap checks (Bezier curves, label spacing, bounding boxes), and post-compilation PDF overlap validation to ensure zero-collision academic figures.

## Features

- **AI-driven TikZ generation** -- describe your architecture, pipeline, or flowchart in natural language
- **Pre-compilation collision detection** -- mathematical gap formulas catch Bezier curve overlaps, label-to-shape collisions, and edge clipping before compilation
- **Post-compilation PDF validation** -- automated coordinate-level overlap checking on rendered output
- **Academic color schemes** -- ready-to-use Blue/Green/Orange/Purple/Red/Grey palettes tuned for print and screen
- **Multi-format output** -- standalone `.tex` files with `pdflatex`/`xelatex` support

## Install

```bash
mkdir -p .claude/skills/tikz-figure-skill
cp SKILL.md .claude/skills/tikz-figure-skill/
cp -r references/ .claude/skills/tikz-figure-skill/
```

Restart Claude Code, or `/tikz-figure-skill <your diagram description>`.

## Quick Start

```
> /tikz-figure-skill Draw a 3-layer system architecture diagram with
  LLM Service, Agent Harness, and Solver Backend. Include feedback loops.
```

## Requirements

- LaTeX distribution (MiKTeX or TeX Live) with `pdflatex`
- Python 3.10+ with `pdfplumber`, `pymupdf` (for PDF validation)
- Optional: `xelatex` for CJK text support

## License

MIT
