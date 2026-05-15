# TikZ Graphdrawing: Automatic Layout & Collision Avoidance

When diagrams grow beyond ~20 nodes, manual coordinate placement becomes unsustainable. TikZ's `graphdrawing` library uses LuaLaTeX to run layout algorithms at **compile time** — nodes auto-arrange, edges auto-route, collisions are mathematically avoided.

## When to Use Graphdrawing vs Manual Layout

| Scenario | Method | Engine |
|----------|--------|--------|
| <= 15 nodes, layered/linear | Manual coordinates (`at (x,y)`) | pdflatex |
| 15–40 nodes, complex topology | `graphdrawing` + layered layout | LuaLaTeX |
| > 40 nodes, free-form graph | `graphdrawing` + force-based | LuaLaTeX |
| Edges cross many nodes | `routing` library edge routing | LuaLaTeX |
| Tree structure | `graphdrawing` + tree layout | LuaLaTeX |

## Prerequisites

```latex
\usepackage{tikz}
\usetikzlibrary{graphs, graphdrawing, arrows.meta, positioning}
\usegdlibrary{layered, force, trees, circular, routing}

% Must compile with: lualatex file.tex
% pdflatex will FAIL — graphdrawing requires Lua
```

## Layout Algorithm Cheat Sheet

### 1. Layered Layout (Hierarchical)

Best for: architecture diagrams, DAGs, pipelines, tree-like structures.

```latex
\begin{tikzpicture}
\graph[layered layout,
       sibling distance=1.2cm,
       level distance=2cm,
       nodes={draw=acaBlueLine, fill=acaBlueFill, rounded corners=2pt,
              minimum width=2.5cm, minimum height=0.7cm,
              font=\footnotesize\sffamily},
       edges={->, >=Stealth, thick, color=black!60}]
{
    User\ Prompt -> Routing -> Local\ LLM -> External\ LLM;
    Routing -> {[edges={dashed, red!60}] Context\ Manager};
    External\ LLM -> Orchestrator -> {MAPDL\ Engine, Recovery\ Ladder};
    Recovery\ Ladder ->[bend right=30] Orchestrator;
};
\end{tikzpicture}
```

Key parameters:
- `level distance` = vertical spacing between layers
- `sibling distance` = horizontal spacing within a layer
- `layered layout` auto-computes node positions top-to-bottom

### 2. Force-Based Layout (Spring Embedder)

Best for: knowledge graphs, relationship networks, citation graphs.

```latex
\begin{tikzpicture}
\graph[spring layout,
       node distance=2cm,
       nodes={draw=acaBlueLine, fill=acaBlueFill, circle, minimum size=0.8cm,
              font=\tiny\sffamily},
       edges={->, >=Stealth, gray!60}]
{
    % Spring layout finds equilibrium — no manual positions needed
    LLM -> {Agent, Harness, Solver};
    Agent -> {Context, Tool, State};
    Harness -> {Recovery, Orchestrator};
    Solver -> {MAPDL, ErrorLog, Output};
    Recovery -> LLM;  % feedback loop
};
\end{tikzpicture}
```

Key parameters:
- `node distance` = preferred edge length (spring rest length)
- `spring layout` iterates until forces converge
- Best for non-hierarchical graphs

### 3. Circular Layout

Best for: lifecycle diagrams, cyclic processes, round-robin architectures.

```latex
\begin{tikzpicture}
\graph[simple necklace layout,
       node distance=0cm,  % nodes on circle edge
       nodes={draw=acaGreenLine, fill=acaGreenFill, circle, minimum size=1cm,
              font=\footnotesize\sffamily},
       edges={->, >=Stealth, thick, acaOrangeLine}]
{
    Analyze -> Design -> Simulate -> Validate -> Analyze;
};
\end{tikzpicture}
```

### 4. Tree Layout (Binary / N-ary)

Best for: decision trees, parse trees, organizational charts.

```latex
\begin{tikzpicture}
\graph[tree layout,
       level distance=1.5cm, sibling distance=1cm,
       grow=down,  % root at top
       nodes={draw=acaPurpleLine, fill=acaPurpleFill, rounded corners=2pt,
              minimum size=0.6cm, font=\tiny\sffamily},
       edges={->, >=Stealth, thick, acaPurpleLine!60}]
{
    Recovery\ Strategy
    -> {no\_recovery, rule\_only, model\_only};
    rule\_only -> {mesh\ fix, convergence\ fix, element\ fix, post\ fix};
    model\_only -> {error\ log\ read, LLM\ regen, context\ enrich};
};
\end{tikzpicture}
```

### 5. Edge Routing (Auto-Avoid Nodes)

Edges can be automatically routed to avoid node intersection.

```latex
% Requires: \usegdlibrary{routing}
\begin{tikzpicture}
\graph[layered layout,
       edge routing=necklace routing,  % edges follow necklace paths
       nodes={draw=acaBlueLine, fill=acaBlueFill, minimum width=2cm},
       edges={->, >=Stealth, thick}]
{
    A -> B -> C -> D -> E;
    A ->[bend left] E;  % long-distance edge routed around, not through
};
\end{tikzpicture}
```

## Collision Avoidance Mechanisms

Graphdrawing provides three layers of collision prevention:

### Layer 1: Layout Algorithm (automatic)
- Node positions are computed to minimize edge crossings and overlaps
- Algorithms guarantee minimum node separation based on `node distance`
- No two nodes can occupy the same position

### Layer 2: Edge Routing (automatic)
- `routing` library computes edge paths that detour around nodes
- No edge will pass through any node's bounding box
- Multi-segment orthogonal paths (like our manual `-|` but computed)

### Layer 3: Post-Layout Math Checks (our additions)
- Even after automatic layout, run `tikz-validator.py` for:
  - Bezier curve label collisions (bend arrows in graphs)
  - Edge clipping at canvas boundaries
  - Label-to-shape boundary clearance

## Transition Strategy: pdflatex -> LuaLaTeX

1. **Simple diagrams (< 15 nodes)**: Keep pdflatex, manual coordinates, run `tikz-validator.py`
2. **Complex diagrams (15–40 nodes)**: Switch to LuaLaTeX + `graphdrawing layered layout`
3. **Dense graphs (> 40 nodes)**: LuaLaTeX + `spring layout` + `routing`

### Detection Rule

In SKILL.md analysis step (step 1), count nodes:

```
if node_count <= 15:
    use pdflatex, manual layout, run tikz-validator.py
elif node_count <= 40:
    use lualatex, \usegdlibrary{layered}
else:
    use lualatex, \usegdlibrary{force}
```

## Common Pitfalls

1. **Graphdrawing needs LuaLaTeX** — `pdflatex` will error with "undefined control sequence"
2. **No CJK in LuaLaTeX by default** — use `\usepackage{luatexja}` or stick to English labels
3. **Layout can differ between compiles** — force-based may converge differently; fix random seed with `spring layout / random seed=42`
4. **Edge labels in automatic layout** — use `edge node {label}` syntax, not manual `\node at`
5. **Performance** — force-based layout on >100 nodes takes seconds per compile; use `draft` mode during development
