# TikZ Collision Detection Rules

Pre-compilation mathematical checks to prevent visual collisions that `pdflatex` never warns about.

## Core Principle

These errors compile cleanly — no warning, no exit code — so AI agents cannot detect them without explicit checking. The fix is pre-compilation math, not post-render eyeballing.

## Check 1: Bezier Curve Label Collisions

A curved arrow (`bend left=N` / `bend right=N`) bows away from the chord between endpoints. Labels placed near the chord midpoint risk being crossed by the arc.

### Formula

```
max_depth  = (chord_length / 2) * tan(bend_angle / 2)
safe_zone  = max_depth + 0.5 cm
```

| Bend angle | tan(angle/2) | Half-chord multiplier |
|---|---|---|
| 20deg | 0.176 | x 0.18 |
| 25deg | 0.222 | x 0.22 |
| 30deg | 0.268 | x 0.27 |
| 35deg | 0.315 | x 0.32 |
| 40deg | 0.364 | x 0.36 |
| 45deg | 0.414 | x 0.41 |
| 50deg | 0.466 | x 0.47 |
| 55deg | 0.521 | x 0.52 |
| 60deg | 0.577 | x 0.58 |

### Example
Arrow 8.4cm wide with `bend left=35`: half-chord = 4.2, depth = 4.2 x 0.315 = **1.32cm**, safe_zone = 1.32 + 0.5 = **1.82cm**. Any label closer than 1.82cm to the chord baseline (in the bend direction) must be moved.

### Fix
- Move label further outside the arc
- Reduce bend angle (e.g. 45 -> 30)
- Place label as separate `\node` at calculated safe position, not as inline edge label

## Check 2: Label Gap Calculation

### Formula

```
available_gap = (center_dist) - (half_width_A) - (half_width_B)
usable_space  = available_gap - 0.6 cm  (0.3cm padding each side)
```

### Label width estimation

| Font size | Width per char | Bold (+10%) | Monospace (+15%) |
|---|---|---|---|
| `\tiny` | 0.08 cm | 0.088 | 0.092 |
| `\scriptsize` | 0.10 cm | 0.11 | 0.115 |
| `\footnotesize` | 0.12 cm | 0.132 | 0.138 |
| `\small` | 0.15 cm | 0.165 | 0.173 |
| `\normalsize` | 0.18 cm | 0.198 | 0.207 |

If `estimate_width > usable_space`: collision guaranteed. Fix: move label above/below or shorten text.

### Example
Two boxes 5cm wide each, 4cm apart edge-to-edge:
- available_gap = 6.5 - 2.5 - 2.5 = 1.5cm
- usable = 1.5 - 0.6 = 0.9cm
- Label "via the terminal" = 16 chars x 0.10 = 1.6cm > 0.9cm -> COLLISION

## Check 3: Arrow Label Positioning

Every arrow label MUST have a positional keyword:
```latex
% GOOD
\draw[->] (A) -- (B) node[midway, above] {label};

% BAD - label sits ON the arrow
\draw[->] (A) -- (B) node[midway] {label};
```
- Horizontal arrows: `above` or `below`
- Vertical arrows: `left` or `right`
- Diagonal: whichever side has more space

## Check 4: Label-to-Shape Boundary Clearance

Every label near a drawn shape must be >= 0.4cm from the shape's boundary.

```latex
% WRONG - label at y=2.0 sits on circle top edge (r=1.5, center at y=0.5)
\node at (4, 2.0) {Sample};

% RIGHT - 0.4cm above top edge
\node at (4, 2.4) {Sample};  % 0.5 + 1.5 + 0.4 = 2.4
```

Never share y-coordinates across different-sized shapes — a y that's safe for one may clip another.

## Check 5: Edge Clipping

Every element must be >= 0.5cm from the canvas edge:
```latex
% Declare explicit bounds
\useasboundingbox (-0.5,-0.5) rectangle (18.5,14.5);
```

## Minimum Clearance Reference

| Object pair | Minimum |
|---|---|
| Label <-> label | 0.3 cm |
| Label <-> drawn shape | 0.4 cm |
| Label <-> arrow/line | 0.3 cm |
| Node edge <-> node edge | 0.8 cm |
| Any object <-> canvas edge | 0.5 cm |

## Workflow

1. Generate TikZ code
2. Run `python references/tikz-validator.py file.tex` (pre-compilation)
3. Compile: `pdflatex file.tex`
4. Run `python references/pdf-overlap-checker.py file.pdf` (post-compilation)
5. Review PNG visually for remaining issues
6. Fix all ERROR items, fix or annotate WARN items
7. Repeat until both validators return PASS
