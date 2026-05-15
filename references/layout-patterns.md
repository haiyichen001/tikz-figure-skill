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

Trigger: "sequence", "interaction", "protocol flow", "时序", "交互", "UML"

### Layout
- Participants: absolute x coordinates, gap 5-6cm. 4 participants max width 17cm.
- Font: `\small\bfseries` for headers, `\footnotesize` for messages. **No `\scriptsize`** — sequence diagrams are tall.
- Vertical: intra-phase message gap 0.5-0.6cm, inter-phase gap 0.8-1.0cm. Total height 17-20cm (<=6 phases).
- Message label color: unified `black!80`. Only critical failures use red. Arrow color matches sender.

### Style Definitions
```latex
participant/.style={rectangle,rounded corners=4pt,align=center,
    minimum height=1.1cm,minimum width=2.8cm,drop shadow={opacity=0.15},thick,font=\small\bfseries},
activation/.style={fill=#1!30,draw=#1!80,thick,rounded corners=1pt,minimum width=0.45cm},
lifeline/.style={dashed,thick,color=#1!80},  % >=!80 visibility on light bg
msg/.style={-{Stealth[scale=1.0]},thick,color=#1},
selfcall/.style={-{Stealth[scale=0.9]},thick,rounded corners=3pt,color=#1},
phase/.style={font=\small\bfseries,text=acaRedLine,fill=acaRedFill,inner sep=5pt,rounded corners=3pt},
note/.style={rectangle,rounded corners=3pt,draw=acaGreyLine!60,fill=acaGoldFill,
    align=left,font=\footnotesize,inner sep=6pt,text width=3.8cm},
```

### Activation Bars (MUST get right)
- Segment activation bars per interaction, NOT one continuous bar from top to bottom.
- Each segment: start y = first_received_message_y - 0.15cm, end y = last_reply_y + 0.15cm.
- Idle gaps between segments show "busy vs waiting" rhythm.
- Arrows must start/finish at activation bar **edges**, not lifeline center:
  ```latex
  % Rightbound message: from sender's right edge to receiver's left edge
  \draw[msg=blue] ([xshift=0.225cm]sender |- 0,-2) -- ([xshift=-0.225cm]receiver |- 0,-2);
  ```
- Absolute y coordinates only. Never `++(0,-offset)` for activation bars — misaligns with messages.

### UML Combined Fragments (par/loop/alt/opt)
```latex
combo/.style={rectangle,draw=acaGreyLine!90,fill=none,dashed,inner sep=0pt,line width=1.2pt},
combo_label/.style={rectangle,fill=acaGreyFill,draw=acaGreyLine!90,font=\small\bfseries,inner sep=4pt},
```
- Box bounds: left=leftmost_participant_x - 1.0cm, right=rightmost_participant_x + 2.5cm.
- Type label at box.north west inset.
- alt divider: horizontal dashed line at y = midpoint between branches, guard label `[condition]` below.
- Nesting: inner box inset 0.3cm, lighter dash color.

### Fill Empty Space
- Self-call arcs width >= 2.0cm. Rightmost participant's self-call arcs go **left**.
- Note boxes between lifelines (not at right edge where they get clipped).
- Phase background stripes: `\fill[color!15]` per phase zone for visual rhythm.

### Quick Checks
- Global font >= `\small` on tall figures
- Rightmost participant self-calls bend left (not right → overflow)
- Activation bars visible at 300dpi (width >= 0.45cm)
- Lifelines drawn LAST (on top of everything)
- No all-empty lifeline columns
- `border >= 25pt` to avoid clip
