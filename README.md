# tikz-figure-skill v3.2

A Claude Code skill that generates publication-ready LaTeX/TikZ diagrams. Template-first always. Engine is quality inspector, not generator.

## How It Works

```
User describes diagram
        ↓
  ① Template Match (187 verified templates, 4 sources)
     └─ grep keywords → list matches
        ↓
  ├─ FULL MATCH → use directly (change text/colors)
  ├─ PARTIAL MATCH → adapt: rename labels, add/remove layers, stitch parts
  └─ STILL NO MATCH → extract structural skeleton from closest template,
      rebuild content around it. Only as absolute last resort generate
      from scratch.
        ↓
  ② Compile (pdflatex)
        ↓
  ③ Quality Inspection (MANDATORY, AI-driven, not hardcoded)
     ├─ tikz-validator.py (11 checks): overflow, collision, gaps, Bezier, edges
     └─ pdf-overlap-checker.py: text overlap, line crossing, off-center
        ↓
  ④ AI reads inspection report → intelligently fixes issues
     No hardcoded auto-fix. Claude understands the problem and decides.
     - Oversized box? Reduce minimum_width or adjust text.
     - Title off-center? Recompute x position.
     - Overlapping nodes? Adjust spacing or re-route edges.
     - 3 layers → 4 layers broke layout? Add row, recompute y positions.
     Re-compile, re-inspect. Max 3 rounds.
        ↓
  ⑤ Deliver: .tex + .pdf + .png + inspection summary
```

## What Makes This Different

- **Template-first, always.** 187 human-reviewed TikZ templates from 4 proven sources. The engine does NOT generate diagrams — it only inspects quality.
- **AI-driven inspection loop.** Validator finds issues. Claude reads the report, understands the root cause, and fixes it intelligently. No hardcoded auto-fixer.
- **Quality, not quantity.** 187 templates kept from 402 — only academic-grade sources retained (janosh 488*, PetarV- 1.4K*, NNTikZ 70*, pgf-umlsd CTAN).
- **All parameters configurable.** Every spacing, color, and font exposed for override. Sensible defaults.

## Template Library

| Source | Stars | Count | Covers |
|--------|-------|-------|--------|
| janosh/diagrams | 488 | 111 | Physics, chemistry, ML concepts |
| PetarV-/TikZ | 1.4K | 43 | GNN, GAN, CNN, RL, graphs, networks |
| pgf-umlsd | CTAN | 22 | UML sequence diagrams |
| NNTikZ + custom | 70 | 11 | Transformer, LSTM, GRU, RNN, CAX-Agent |

## Install

```bash
git clone https://github.com/haiyichen001/tikz-figure-skill.git \
  ~/.claude/skills/tikz-figure-skill
```

## Quality Inspection Tools

| Tool | Runs | Checks |
|------|------|--------|
| `tikz-validator.py` | Pre-compile | Micro-slopes, direction reversal, container overflow, label collision, arrow length, Bezier arc, label gaps, edge clipping, boundary clearance, line crossings, oversize nodes |
| `pdf-overlap-checker.py` | Post-compile | Text overlap, text overflow, content centering, text-line intersection, line crossings |

Both tools report to Claude — the AI decides what to fix and how. No Python auto-fix loop.

## Requirements

- LaTeX distribution (MiKTeX / TeX Live / MacTeX)
- Python 3.10+ (optional: `pdfplumber`, `pymupdf`)

## License

MIT
