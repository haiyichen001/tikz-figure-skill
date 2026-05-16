# tikz-figure-skill v3.3

A Claude Code skill for publication-ready LaTeX/TikZ diagrams. Template-first. AI-driven inspection loop.

## Workflow

```
User describes diagram
    ↓
① Template match (187 verified templates, 4 sources)
   Full match → use directly
   Partial → adapt, stitch, merge
   ↓
② Compile (pdflatex)
   ↓
③ Inspect (one command, 15 checks, all WARN)
   python references/inspect.py output.tex output.pdf
   ↓
④ Model judges each WARN:
   Template-inherited? → SKIP (design intent)
   Adapted/added?    → FIX
   ↓
Deliver: .tex + .pdf + .png + inspection report
```

## Template Library (187 verified)

| Source | Stars | Count | Covers |
|--------|-------|-------|--------|
| janosh/diagrams | 488 | 111 | Physics, chemistry, ML concepts |
| PetarV-/TikZ | 1.4K | 43 | GNN, GAN, CNN, RL, graphs |
| pgf-umlsd | CTAN | 22 | UML sequence diagrams |
| NNTikZ + custom | 70 | 11 | Transformer, LSTM, GRU, CAX-Agent |

## Inspection (15 checks, all relative to image diagonal)

| # | Check | Threshold |
|---|-------|-----------|
| 1 | collision | D × 0.5% |
| 2 | overflow | D × 1% |
| 3 | edge-clip | D × 2% |
| 4 | tight-clearance | D × 1% |
| 5 | oversize | > 3× text |
| 6 | text-overlap | IoU > 3% |
| 7 | text-overflow | D × 0.15% |
| 8 | off-center | margin ratio > 4:1 |
| 9 | text-line | D × 0.15% |
| 10 | line-crossing | segment > D × 1.5% |
| 11 | aspect-ratio | > 4:1 |
| 12 | content-density | < 1.5% |
| 13 | orphan-nodes | any found |
| 14 | layout-balance | skew > 50% |
| 15 | font-scaling | < D × 0.4% |

All WARN. Model decides. Zero absolute thresholds.

## Install

```bash
git clone https://github.com/haiyichen001/tikz-figure-skill.git \
  ~/.claude/skills/tikz-figure-skill
```

## Credits

Templates: janosh, PetarV-, pgf-umlsd, NNTikZ. Validation: MixtapeTools. Built on thesis-figure-skill. MIT.
