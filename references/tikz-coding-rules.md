# TikZ Coding Rules

Mandatory conventions for all AI-generated TikZ code. Load before writing any `.tex` file.

## Rule 0: Graphdrawing Only (MANDATORY)

**AI must define diagrams as `\graph` structures. Never write manual coordinates.**

LuaLaTeX + graphdrawing computes all node positions and edge routes at compile time:
- Sugiyama layered layout for hierarchical DAGs
- Force-based spring layout for free-form graphs
- Automatic edge routing that avoids node boxes
- Zero manual y-position math, zero overlap risk

**Wrong — manual coordinates (AI can't verify):**
```latex
\node at (12.0,-3.5) {Kriging};
\node at (12.0,-4.3) {RBF};
```

**Correct — graph structure (lualatex handles layout):**
```latex
\graph[layered layout, grow=right] {
  a/"Kriging" -> b/"RBF";
};
```

Use the layout-engine.py to generate `\graph` syntax from a JSON spec.
For simple ad-hoc diagrams, write `\graph` directly; NEVER fall back to manual `at (x,y)`.

## Language
- English labels (concise). CJK only when user explicitly requests Chinese.
- **No `rotate=90` with CJK** — xelatex renders it as unreadable blocks.

## Code Standards
- `\documentclass[tikz,border=...]{standalone}` as first line
- Color definitions in preamble, before `\begin{document}`
- All `\\` in nodes require `align=center` (or `align=left`)
- `scale=0.8` must be paired with `every node/.style={scale=0.8}`
- No unclosed braces.

## Arrow Rules
- Horizontal arrows: label with `above` or `below`
- Vertical arrows: label with `left` or `right`
- Never `node[midway]` without positional keyword
- Use `-|` or `|-` for L-shaped bends

## Node Rules
- `base_box` minimum height: 0.85cm, `inner sep` >= 8pt
- Multi-line node: `align=center` + `text width` 15% wider than estimate
- Hero box: >= 5cm wide, >= 3x sub-elements inside
- Zone titles: `label={[font=\small\bfseries]above:Title}`

## Defensive Patterns
- Arrow tips: `shorten >=2pt, shorten <=1pt` — prevent arrowhead piercing node borders
- Colored fills in `background` layer, text in `main` layer
- `inner sep=10pt` in `base_box` — defensive against tight text
