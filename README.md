# tikz-figure-skill v3.0

A Claude Code skill that generates publication-ready LaTeX/TikZ diagrams. Template-first, engine-fallback, always validated.

## How It Works

```
User describes diagram
        ↓
  ① Template Match (402 templates from 6 libraries)
        ↓
  ├─ Full match → use directly (customize colors/text)
  ├─ Partial match → stitch 2+ templates together
  └─ No match → layout-engine.py (JSON spec)
        ↓
  ② Compile (pdflatex)
        ↓
  ③ Validate (tikz-validator: 11 checks)
        ↓
  ④ PDF Overlap Check (pdf-overlap-checker)
        ↓
  ⑤ AI reads warnings → adjusts → re-compiles (max 3 rounds)
        ↓
  ⑥ Deliver: .tex + .pdf + .png
```

## What Makes This Different

- **Template-first with intelligent stitching.** 402 human-reviewed TikZ templates matched by keyword. Partial matches get merged — take the encoder from Transformer, the decoder from Mamba. Only falls back to algorithmic layout as last resort.
- **AI-driven validation loop.** Not a hardcoded auto-fixer. Claude reads validator output, understands the issues, and intelligently adjusts — because the skill is a system prompt that teaches the model how to use its tools.
- **All config, no hardcode.** Every parameter (spacing, colors, fonts, zones) exposed through JSON spec with sensible defaults. User or AI can override anything.
- **Cross-platform.** macOS, Linux, Windows. Auto-detects LaTeX distro, CJK fonts, Python deps.

## Template Library

402 templates from 6 open-source libraries, MIT/GPL/CC licensed:

| Source | Stars | Covers |
|--------|-------|--------|
| NNTikZ | 70 | Transformer, LSTM, GRU, RNN, Attention, Dropout |
| PetarV-/TikZ | 1.4K | GNN, GAN, Autoencoder, CNN, CycleGAN, RL |
| janosh/diagrams | 488 | Physics, Chemistry, ML concepts (111 figures) |
| FriendlyUser/LatexDiagrams | 205 | Software architecture, circuits, flowcharts, Gantt |
| andreas-bauer/TikZ | 17 | VM vs container, data poisoning, timelines |
| pgf-umlsd | CTAN | UML sequence diagrams (22 examples) |

## Install

```bash
git clone https://github.com/haiyichen001/tikz-figure-skill.git \
  ~/.claude/skills/tikz-figure-skill
```

Restart Claude Code. `/tikz-figure-skill` is ready.

## Quick Start

```
/tikz-figure-skill Draw a Transformer encoder-decoder architecture
/tikz-figure-skill Draw our company's 3-layer microservice deployment
/tikz-figure-skill UML sequence diagram for user login flow
```

## Validation Pipeline

All generated diagrams pass through:

| Tool | When | Checks |
|------|------|--------|
| `tikz-validator.py` | Pre-compile | 11 checks: micro-slopes, overflow, collision, Bezier, gaps, edge clip |
| `pdf-overlap-checker.py` | Post-compile | Text overlap, line crossing, off-center, text-line intersection |

## Requirements

- LaTeX distribution (MiKTeX / TeX Live / MacTeX)
- Python 3.10+ (optional: `pdfplumber`, `pymupdf`)

## Structure

```
tikz-figure-skill/
  SKILL.md                    -- Skill definition & workflow
  README.md
  install.sh / install.ps1
  scripts/
    check-env.py              -- Cross-platform dependency checker
  references/
    layout-engine.py          -- JSON spec → .tex generator (engine fallback)
    tikz-validator.py         -- Pre-compile 11 checks
    pdf-overlap-checker.py    -- Post-compile PDF overlap detector
    figure-diff.py            -- SSIM comparison
    tikz_parser.py            -- Shared .tex parser
    tikz-coding-rules.md      -- Coding conventions
    design-philosophy.md      -- Design principles
    collision-detection.md    -- Bezier formulas, clearance tables
    layout-patterns.md        -- Layout rules
    visual-patterns.md        -- Drawing patterns
    pgfplots-templates.md     -- CSV chart templates
    graphdrawing-guide.md     -- LuaLaTeX layout guide
    geometry-math.md          -- Coordinate systems
    templates/                -- 402 flat templates (*.tex)
```

## Credits

Templates: NNTikZ (fraserlove), PetarV-/TikZ, janosh/diagrams, FriendlyUser/LatexDiagrams, andreas-bauer/TikZ, pgf-umlsd. Validation: MixtapeTools (scunning1975). Built on thesis-figure-skill (0xE1337).

## License

MIT
