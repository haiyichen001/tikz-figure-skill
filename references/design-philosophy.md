# Design Philosophy

These principles guide every figure this skill produces. Read once to understand the WHY behind the rules.

## Core Philosophy

**Every figure should make the reader think "this author cares."**

Not "good enough." Not "all the information is there." You want figures that readers pause to look at twice. Top-venue papers don't look good because they're bug-free — they look good because the designer invested in information density, visual hierarchy, and spatial rhythm. Think like a designer, not a programmer stacking code.

## The Four-Step Loop

1. **Define success**: What does this figure communicate? What should the reader understand? How many modules, layers, what visual hierarchy? This is the anchor for every decision.

2. **Choose the starting point**: TikZ vs draw.io based on content. Layout direction based on information flow. Reference the capability boundaries table.

3. **Validate in progress**: Every result is evidence. Compile errors may signal the layout approach itself is wrong. Large empty areas may mean module granularity is off. Use results to calibrate direction.

4. **Decide when done**: 30/30 score against the checklist. But don't over-polish — readers won't zoom in to check 0.1cm spacing.

## Fighting Model Inertia

Claude's default behavior patterns to consciously override:

- **"I know what I'm doing, skip to code"** — most dangerous. Must output explicit drawing plan first. Thinking and writing are different — rail conflicts, label overlap, bad module placement only surface when written down.
- **"Architecture diagram = bottom-up layers"** — not always. Side-by-side or center-radial may be better.
- **"Compile error = fix syntax"** — first diagnose: syntax or fundamental layout flaw?
- **"Whitespace = add filler"** — first ask if module placement is wrong.
- **"TikZ can't do it = switch to draw.io"** — first confirm it's a TikZ limitation, not a code issue.
- **"Reference image = 1:1 copy"** — first assess if the reference layout is optimal.
- **"I can eyeball proportions"** — no. Your proportion intuition is systematically biased 15-20%. Measure pixel ratios.
- **"Boxes can be roughly square"** — reference figures use wide boxes (w:h ≈ 2:1 to 3:1).
- **"Fill the space"** — reference figures leave 20-30% breathing room. Target 60-70% fill, not 90%.
- **"After 3 rounds, good enough"** — standards don't lower with effort.
- **"Tiny overlap, reader won't notice"** — they always notice. 0.2cm = 24px at 300dpi.

## Design Ambition (Minimum Bar)

Don't fail these before writing code:

| Dimension | Minimum | Fail Indicator |
|-----------|---------|---------------|
| Information density | >= 30 visual elements (nodes + edges + labels + embedded charts + decorations) | Only 10-15 boxes with straight connectors |
| Visual hierarchy | >= 3 size levels (hero >=5cm / standard / tiny), hero box has sub-structure | All boxes same size |
| Embedded visualizations | >= 3 hand-drawn charts (heatmap/curve/bar/scatter/matrix), each >=2.5cm | All text-only boxes |
| Edge richness | >= 3 line types (thick orange data + black control + blue dashed feedback) | All same arrow style |
| Space utilization | >= 75% fill rate, prefer horizontal expansion | Narrow waterfall, lots of empty sides |
| Bottom panel | Complex figures have bottom result panel (2-3 side-by-side charts) or pipeline summary bar | Figure ends with the last box |
| Zone backgrounds | Each logical zone has light fill + stage label | Plain white or dashed-only zones |

## Making Figures "Alive"

Don't draw schematics. Draw infographics.

- **Schematic**: A→B→C→D, four identical boxes, four identical arrows. Reader yawns.
- **Infographic**: A is small input, B is large processing module (with sub-structure), C has embedded data visualization, D uses accent color. Reader thinks "this figure is dense."

Specific techniques:
1. **Size contrast**: Core modules 3x larger than helpers (hero >=5cm×3.5cm vs standard 2.8cm×0.9cm)
2. **Hero box internals**: >=3 sub-nodes + formula/chart inside complex modules
3. **Fine visualizations**: Every embedded chart needs axes, ticks, labels, legend. Heatmaps need row/col labels and colorbar.
4. **Horizontal multi-stage**: Favor horizontal expansion (5 stages left-to-right). Don't stack everything vertically.
5. **Bottom experiment panel**: 2-3 side-by-side result charts at figure bottom.
6. **Pipeline summary bar**: Color-chain summary at very bottom (Input → Encode → Process → Output).
7. **Zone backgrounds**: Each zone has light fill background + rounded stage label at top-left.
8. **Compact density**: Element spacing is "just enough to breathe" — academic beauty comes from density, not sprawling whitespace.
