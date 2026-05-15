# TikZ Coding Rules

Mandatory conventions for all generated TikZ code. Load before writing any `.tex` file.

## Language
- English labels (concise). CJK only when user explicitly requests Chinese.
- **No `rotate=90` with CJK** — xelatex renders it as unreadable blocks. All labels must stay horizontal.

## Layout
- **Canvas-to-font ratio**: if figure height > 12cm, use `\small` globally. If <= 12cm, `\footnotesize` is OK.
- **Fill empty areas**: any blank region > 3cm x 2cm must be filled with a note box, formula box, or legend.
- **Absolute coordinates > relative positioning** for multi-column alignment (sequence diagrams, comparison charts). Relative positioning accumulates drift in deep nesting.
- **Cross-layer arrows never pass through nodes**: Before routing, check all y-values on the path for node bounding box intersections. If conflict, route through the nearest empty gap.
- **Short-distance bends go to empty side first**: When source-target are diagonally adjacent (<3cm gap), route horizontally into open space first, then turn.
- **Zone left-right alignment**: multi-layer zones must share identical left/right boundaries. Use invisible anchor nodes: `\node[inner sep=0pt,minimum size=0pt](anchor_L) at (x_min-1,0) {};` then `fit=(anchor_L)(...node)(anchor_R)`.
- **Layer titles use absolute x**: don't use `$(zone.west)+(-2,0)$` which varies by zone width. All layer titles share the same absolute x-coordinate.
- Side-by-side comparison: center channel >= 3cm gap.
- Multi-instance: horizontal 3-column layout, column gap 2.5-3cm.

## Code Standards
- `\documentclass[tikz,border=...]{standalone}` as first line
- Color definitions in preamble, before `\begin{document}`
- All `\\` in nodes require `align=center` (or `align=left`)
- `scale=0.8` must be paired with `every node/.style={scale=0.8}` — scale shrinks coords but NOT text
- No unclosed braces. Count `{` vs `}` per `\node` / `\draw`.

## Arrow Rules
- Horizontal arrows: label with `above` or `below`
- Vertical arrows: label with `left` or `right`
- Never `node[midway]` without positional keyword (label sits ON the arrow)
- Use `-|` or `|-` for automatic L-shaped bends — prefer over manual midpoints
- Tree forks: draw trunk+crossbar as one continuous `\draw` (no arrow, no shorten), then branches separately

## Node Rules
- `base_box` minimum height: 0.85cm, `inner sep` >= 8pt (text doesn't touch border)
- Multi-line node: `align=center` + `text width` 15% wider than estimate
- Hero box: >= 5cm wide, >= 3x sub-elements inside
- Zone titles: use `label={[font=\small\bfseries]above:Title}` — avoids overlap with zone content

## Staggering Crowded Labels
- Alternate `above`/`below` for consecutive arrow labels
- Use `pos=0.3` and `pos=0.7` instead of `midway` for parallel arrows
- `near start` / `near end` for very crowded diagrams

## Defensive Patterns
- Arrow tips: `shorten >=2pt, shorten <=1pt` to prevent arrowhead piercing node borders
- Colored fills in `background` layer, text in `main` layer
- `inner sep=10pt` in `base_box` — defensive against tight text
- Skip `scope` content in micro-slope checks (embedded visualizations use diagonal lines intentionally)
