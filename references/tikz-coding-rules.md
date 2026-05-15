# TikZ Coding Rules

Mandatory conventions for all AI-generated TikZ code. Load before writing any `.tex` file.

## Rule 0: Absolute Coordinates Only (MANDATORY)

**AI must use `at (x,y)` for every node. Never use relative positioning.**

`below=of X`, `right=of Y`, `above left=of Z` — these are for humans saving keystrokes. AI has no keystrokes to save.

**Why relative positioning fails with AI:**

1. **Accumulation drift**: `below=0.3cm of A` → `below=0.3cm of B` → `below=0.3cm of C`. The visual gap is NOT 0.3cm — it's `0.3 + half_height_of_B + half_height_of_C`. Since A/B/C have different `minimum height`, each gap is different. AI can't see this.

2. **Center vs edge confusion**: `below=0.3cm` means center-to-center distance, not edge-to-edge. A node with `minimum height=2.2cm` followed by one with `minimum height=0.7cm` placed `below=0.3cm` of it will have a visual gap of `0.3 - 1.1 - 0.35 = -1.15cm` (OVERLAP). AI can't calculate this for every pair.

3. **No visual feedback**: pdflatex gives zero warnings about overlapping nodes. The AI declares "done" while boxes sit on top of each other.

**The fix is trivial for AI:**

```latex
% WRONG — relative, AI can't verify
\node[box,below=0.3cm of e2] (m2a) {Kriging};
\node[box,below=0.1cm of m2a] (m2b) {RBF};

% CORRECT — absolute, no ambiguity
\node[box] (m2a) at (12.0,-3.5) {Kriging};
\node[box] (m2b) at (12.0,-4.3) {RBF};
```

**How to compute absolute y for stacked nodes:**

```
y_next = y_prev - half_height_prev - gap - half_height_next

Example:
  e1: center at y=-1.8, height=2.2cm  (half=1.1)
  m2a: center at y=-3.5, height=0.7cm (half=0.35)
  gap between e1.bottom and m2a.top = (-3.5+0.35) - (-1.8-1.1) = -3.15 - (-2.9) = -0.25
  Wait, that's overlapping. Let's fix:
  
  e1.bottom at y = -1.8 - 1.1 = -2.9
  We want 0.3cm gap below e1.bottom
  m2a.top should be at y = -2.9 - 0.3 = -3.2
  m2a.center = m2a.top - half_height = -3.2 - 0.35 = -3.55
  
  So: m2a at (12.0, -3.55)
```

Every time a node is stacked below another, compute y explicitly from the bottom edge of the node above, adding the desired gap, then subtract half the new node's height.

## Language
- English labels (concise). CJK only when user explicitly requests Chinese.
- **No `rotate=90` with CJK** — xelatex renders it as unreadable blocks.

## Layout
- **Canvas-to-font ratio**: if figure height > 12cm, use `\small` globally.
- **Fill empty areas**: any blank region > 3cm x 2cm filled with note/legend.
- **Cross-layer arrows never pass through nodes**: check all y-values on path for bounding box intersections.
- **Zone left-right alignment**: all zones share identical left/right boundaries. Use invisible anchor nodes.
- **Layer titles use absolute x**: all layer titles share one absolute x-coordinate.
- Side-by-side comparison: center channel >= 3cm gap.

## Node Sizing: Compute from Text, Not Fixed Numbers

**MANDATORY: Node sizes must be derived from text content, not arbitrary fixed values.**

`minimum width` and `minimum height` in TikZ are **floors**, not ceilings. TikZ always auto-grows the box to fit text. Setting them larger than the text creates empty space. Setting them too small causes overlap with adjacent nodes.

### How to size nodes correctly:

1. **For single-line text**: do NOT set `minimum width`. TikZ auto-sizes: `text_width + 2 * inner_sep`.
   ```latex
   % CORRECT — auto-sized to text
   \node[draw,rounded corners=2pt,inner sep=6pt] at (5,0) {Short label};
   ```

2. **For multi-line text**: use `text width` + `align=center`, do NOT set `minimum height`. Height auto-computes from line count.
   ```latex
   % CORRECT — width fixed for wrapping, height auto
   \node[draw,text width=4cm,align=center,inner sep=6pt] at (5,0) {Long text that wraps};
   ```

3. **When boxes in a column must align (same width)**: compute the max text width first, then set `minimum width` to that value, not an arbitrary number.
   ```
   Step 1: estimate width of each label (char_count * font_coefficient)
   Step 2: max_width = max(all label widths)
   Step 3: minimum width = max_width + 2 * inner_sep + 0.3  (0.3cm safety margin)
   ```

4. **Font width estimation for sizing**:
   | Font command | cm per char |
   |-------------|-------------|
   | `\tiny` | 0.08 |
   | `\scriptsize` | 0.10 |
   | `\footnotesize` | 0.12 |
   | `\small` | 0.15 |
   | `\normalsize` | 0.18 |

5. **For stacked nodes, compute y from actual dimensions**:
   ```
   y_next = y_prev - (height_prev / 2) - gap - (height_next / 2)
   
   where height = (number_of_lines * line_height) + 2 * inner_sep
   and line_height ≈ font_size_cm * 1.5
   ```

### Anti-patterns to avoid:
```latex
% WRONG — 4cm box for 3-character text "RBF"
\node[minimum width=4cm,minimum height=0.65cm] {RBF};

% WRONG — all boxes forced to same arbitrary size
\node[box,minimum width=3.8cm,minimum height=0.7cm] {Tiny};  % too big
\node[box,minimum width=3.8cm,minimum height=0.7cm] {Very long description};  % may overflow
```

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
