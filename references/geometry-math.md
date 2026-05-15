# Geometry & Math Diagrams

Trigger: "geometry", "math visualization", "coordinate", "tree", "原理图", "数学"

## Multi-Region Composite Layout

- Absolute coordinates for regions: left x in [0,7], right x in [8,18], bottom formula full width
- 0.5-1cm gap between regions, different light background fills
- Region titles: rounded box with fill, not bare text

## Coordinate Systems

- Axes: `thick, -{Stealth}`, grid: `gray!12, thin` on background layer
- Curves: `smooth, samples=80`, precise `domain` to prevent crossing into other regions

## Tree Structures

- Normal edges: `black!35, semithick` (light grey). Highlighted paths: `very thick` color.
- **Highlighted path MUST use different anchor** than normal edge on same node pair.
- Left subtree: `parent.south west`, right subtree: `parent.south east` (mirror symmetry).
- Sibling labels: side tags (`anchor=west/east`) with background fill, not arrow-pointing.
- Dashed box content must stay >=0.3cm from box boundary.

## Cross-Region Connections

- **Never** long diagonal dashed lines between regions.
- Correct: down 0.3-0.5cm from source, then `-|` or `|-` with `rounded corners=10pt` to target anchor.
- Use semi-transparent colors (`blue!60`), not louder than main content.
- Labels at bend origin, not mid-segment.

## Formula Boxes

- Style: `formula_box`, `inner sep=8pt`, large formulas use `\normalsize`.
- Decomposition labels below the box, equally spaced, short dashed arrows to box bottom.

## Legend Placement

- Must NOT overlap any content. Gap >=0.5cm from nearest element.
- Default: bottom-right. If occupied, move to bottom-left or separate row below figure.
- **Post-render check**: confirm legend doesn't obscure anything.

## Curve Label Anti-Collision

- Point coordinates and labels must sit outside the curve (away from bend direction).
- If curve space is tight, use `pin` to route label to open area.
- Label font >= `\footnotesize`.

## Quick Checks

- [ ] Curve domain doesn't cross into other regions
- [ ] All labels within border (border >= 30pt)
- [ ] Cross-region links use L-shaped + rounded corners, no long diagonals
- [ ] Highlighted paths have clear visual hierarchy vs normal edges
- [ ] Formula box centered and width matches content
