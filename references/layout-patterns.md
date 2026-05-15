# Layout Patterns

Pattern-specific rules for common TikZ diagram layouts. Load when chart type matches.

## Layered Architecture (Bottom-Up)

Trigger: "system architecture", "layered", "multi-tier", "3-layer", "分层架构"

Rules:
- Bottom layer = infrastructure/solver > middle = orchestration > top = user interface
- Each layer gets a `zone` rectangle with light fill color (`zoneBlueBg`, `zoneGreenBg`, `zoneRedBg`)
- Layer label at top-right corner of zone: `\node[stagelbl,acaBlueLine] at (zone.north east)...`
- Cross-layer arrows route via left or right rail (x-coordinate reserved for vertical paths)
- Nodes within a layer share y-coordinate (horizontal alignment)
- Hero element (orchestrator/core) centered, 2-3x size of support modules

Common dimensions:
```
Zone padding: 0.5cm from content edges
Layer height: 3.5-5cm depending on node count
Rail width: 0.8cm reserved for cross-layer vertical arrows
```

## Data Pipeline (Left-to-Right)

Trigger: "pipeline", "data flow", "processing chain", "流水线", "处理流程"

Rules:
- Horizontal串联: Input → Stage1 → Stage2 → ... → Output
- Each stage can be a different node shape: process=rectangle, decision=diamond, storage=cylinder
- Arrow labels use `above` (not `midway` without positional keyword)
- If >4 stages, wrap to 2 rows with clear row separator
- Stage number label at top of each node: `\node[above=-2pt] at (box.north) {\scriptsize Stage N};`

Stage spacing:
```
Stage gap: 2.0-3.0cm center-to-center
Node width: 2.8cm for simple stages, 4.0cm+ for stages with sub-text
```

## Three-Column Mapping

Trigger: "mapping", "conversion", "three columns", "三栏", "映射", "转换"

Rules:
- Three equal-width columns: Left | Center | Right
- Column width = (total_width - 2*gap) / 3
- Column titles centered above each column
- Cross-column arrows connect specific items (not column-to-column)
- If mapping is many-to-many, add a summary node below showing total mapping count

Coordinate template:
```
Column 1: x = 3.0cm   (left third)
Column 2: x = 8.5cm   (center third)
Column 3: x = 14.0cm  (right third)
for total width ~18cm
```

## Sequence Diagram

Trigger: "sequence", "interaction", "protocol flow", "时序", "交互"

Rules:
- Each participant is a vertical lifeline column
- Participant header: rectangle with `\small\bfseries` name
- Messages: horizontal arrows between lifelines, label `above` or `below`
- Activation bars: narrow rectangles on lifelines during active period
- Time flows top-to-bottom
- Return/dashed arrows for responses

Spacing:
```
Lifeline gap: 3.0-4.0cm
Message vertical spacing: 1.0cm
Header height: 0.9cm
```
