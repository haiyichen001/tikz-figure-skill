# Visual Patterns Library

Reusable TikZ drawing patterns for rich, publication-quality figures. Must use >=3 patterns per figure.

## Pattern 1: Hero Box with Internal Sub-Structure

Core modules need expanded internals — not just text in a box.

```latex
% Outer hero box
\node[herobox,fill=acaGreenFill,draw=acaGreenLine!80!black,
      minimum width=5.6cm,minimum height=3.2cm] (hero) at (x,y) {
    \textbf{Module Name}\\[4pt]
    \begin{tabular}{ll}
    \scriptsize$\bullet$ Feature A & \scriptsize$\bullet$ Feature B\\
    \end{tabular}};
```

## Pattern 2: Heatmap Matrix (TikZ-native)

For attention maps, confusion matrices, correlation plots. No pgfplots needed.

```latex
% NxN grid of colored cells
\foreach \i in {1,...,4} {
    \foreach \j in {1,...,4} {
        \pgfmathsetmacro\val{...}  % value 0-1
        \pgfmathsetmacro\shade{int(100 - \val * 80)}
        \fill[blue!\shade!white] (\i*1.2, -\j*1.2) rectangle +(1.0,1.0);
        \node[font=\tiny] at (\i*1.2+0.5, -\j*1.2-0.5) {\pgfmathprintnumber{\val}};
    }
}
```

## Pattern 3: Bar Chart (TikZ-native, no pgfplots)

For quick embedded comparisons inside architecture boxes.

```latex
% Single bar
\fill[acaBlueFill,draw=acaBlueLine] (x,0) rectangle +(0.6,value*scale);
\node[font=\tiny,above] at (x+0.3, value*scale) {3.59};
```

## Pattern 4: Line Plot (TikZ-native)

For convergence curves, training progress within a node.

```latex
\draw[acaBlueLine,thick] plot coordinates {(0,0)(1,1.5)(2,2.0)(3,2.3)(4,2.5)};
\draw[acaOrangeLine,thick,dashed] plot coordinates {(0,0)(1,1.2)(2,1.8)(3,2.0)(4,2.1)};
% Axes
\draw[->,gray] (0,0) -- (4.5,0) node[right] {\tiny epoch};
\draw[->,gray] (0,0) -- (0,3) node[above] {\tiny loss};
```

## Pattern 5: Scatter Plot

```latex
\foreach \x/\y in {1/0.5,1.5/1.2,2/1.8,2.5/2.1,3/2.3} {
    \fill[acaBlueLine] (\x,\y) circle (2pt);
}
```

## Pattern 6: Stage Labels (Zone Headers)

Each logical zone gets a rounded stage tag at top-left.

```latex
\node[stagelbl,fill=acaBlueFill!60,draw=acaBlueLine,rounded corners=2pt,
      font=\footnotesize\bfseries\sffamily,inner sep=3pt]
      at (zone.north west) {Stage 1: Extraction};
```

## Pattern 7: Pipeline Summary Bar (Bottom)

Color-chain summary at figure bottom. Width matches figure.

```latex
\node[box,fill=acaBlueFill,draw=acaBlueLine,minimum width=3cm] (s1) at (...) {Input};
\node[box,fill=acaGreenFill,draw=acaGreenLine,minimum width=3cm,right=0.5cm of s1] (s2) {Encode};
\node[box,fill=acaOrangeFill,draw=acaOrangeLine,minimum width=3cm,right=0.5cm of s2] (s3) {Output};
\draw[->,>=Stealth,thick,acaOrangeLine] (s1) -- (s2) -- (s3);
```

## Pattern 8: Cross-Layer Rail System

Reserve left/right rail for vertical cross-zone arrows. Allocate rail x-coordinates:

```latex
% Left rail at x=0.5cm, right rail at x=total_width-0.5cm
% Cross-layer arrows route through rails:
\draw[arr] (bottom_node.east) -| (right_rail, y_mid) |- (top_node.east);
```

## Pattern 9: Font Size Rules for Embedded Visualizations

| Context | Minimum font | Forbidden |
|---------|-------------|-----------|
| Axis labels | `\tiny` (5pt) | `\fontsize{4}` |
| Bar value labels | `\tiny` | smaller than `\tiny` |
| Legend text | `\footnotesize` | `\tiny` in legend |
| Zone stage labels | `\footnotesize\bfseries` | `\tiny` for zone headers |
| Main node text | `\footnotesize` | `\scriptsize` for multi-word labels |
