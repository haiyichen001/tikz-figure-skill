# PGFPlots Data Visualization Templates

Generate publication-quality data charts directly in LaTeX from CSV files or inline data — no matplotlib/Python needed.

## Why PGFPlots

- Fonts match the paper text automatically (same LaTeX font)
- Pure vector output, no resolution limits
- Data lives in CSV — update numbers, recompile, done
- No `\includegraphics` of external PNGs with mismatched fonts

## Prerequisites

```latex
\usepackage{pgfplots}
\usepackage{pgfplotstable}
\pgfplotsset{compat=1.18}  % latest compatibility mode
\usetikzlibrary{pgfplots.groupplots}  % for multi-panel layouts
```

## Design Rules for Academic Charts

1. **Remove chartjunk**: no top/right axis lines, no background fill, minimal grid
2. **Grey grid, not black**: `grid=major, grid style={gray!30}` not default black
3. **Labels match body text**: use `\footnotesize` for tick labels, `\small` for axis labels
4. **Fill bars with academic palette**: use the skill's color scheme (acaBlueFill etc.)
5. **No 3D effects, no shadows, no gradients**: flat design is standard in top venues
6. **Error bars with cap**: `error bars/y dir=both, error bars/y explicit` always

---

## Template 1: Bar Chart (ybar) — from CSV

Best for: strategy comparison, ablation studies, benchmark results.

```latex
% CSV file: results.csv
% Strategy,Completion,TaskScore,TotalScore
% model_only,0.9267,3.59,9.16
% rule_only,0.7733,3.17,7.03
% no_recovery,0.6933,2.74,5.60

\begin{tikzpicture}
\begin{axis}[
    width=8cm, height=5cm,
    ybar,                     % vertical bars
    bar width=0.6cm,
    enlarge x limits=0.3,     % gap between bar groups
    ymin=0, ymax=10,
    ylabel={Score},
    xlabel={Recovery Strategy},
    xtick=data,
    xticklabels from table={results.csv}{Strategy},
    xticklabel style={font=\footnotesize, text width=2cm, align=center},
    yticklabel style={font=\footnotesize},
    ylabel style={font=\small},
    xlabel style={font=\small},
    grid=major,
    grid style={gray!25, dashed},
    axis lines=left,           % no top/right border
    legend style={
        font=\footnotesize,
        legend columns=-1,     % horizontal legend
        at={(0.5,1.05)},       % above plot
        anchor=south,
    },
    % Value labels on bars
    nodes near coords,
    nodes near coords style={font=\tiny\bfseries},
    nodes near coords align=vertical,
]

% Series 1: Completion Rate
\addplot[draw=acaBlueLine, fill=acaBlueFill!60]
    table[x expr=\coordindex, y=Completion] {results.csv};
\addlegendentry{Completion Rate}

% Series 2: Task Score (/4)
\addplot[draw=acaGreenLine, fill=acaGreenFill!60]
    table[x expr=\coordindex, y=TaskScore] {results.csv};
\addlegendentry{Task Score (/4)}

% Series 3: Total Score (/10)
\addplot[draw=acaOrangeLine, fill=acaOrangeFill!60]
    table[x expr=\coordindex, y=TotalScore] {results.csv};
\addlegendentry{Total Score (/10)}

\end{axis}
\end{tikzpicture}
```

## Template 2: Line Plot — from CSV

Best for: convergence curves, training progress, time series.

```latex
% CSV file: convergence.csv
% Epoch,TrainLoss,ValLoss
% 1,2.34,2.45
% 2,1.87,2.01
% 3,1.45,1.67
% ...

\begin{tikzpicture}
\begin{axis}[
    width=10cm, height=5cm,
    xlabel={Epoch},
    ylabel={Loss},
    xmin=0, xmax=50,
    ymin=0,
    xlabel style={font=\small},
    ylabel style={font=\small},
    xticklabel style={font=\footnotesize},
    yticklabel style={font=\footnotesize},
    grid=major,
    grid style={gray!25, dashed},
    axis lines=left,
    legend style={font=\footnotesize, at={(0.98,0.98)}, anchor=north east},
    cycle list={  % override default color cycle with academic palette
        {acaBlueLine, thick, mark=*, mark size=1.5pt},
        {acaOrangeLine, thick, mark=square*, mark size=1.5pt},
    },
]

\addplot table[x=Epoch, y=TrainLoss] {convergence.csv};
\addlegendentry{Train Loss}

\addplot table[x=Epoch, y=ValLoss] {convergence.csv};
\addlegendentry{Validation Loss}

\end{axis}
\end{tikzpicture}
```

## Template 3: Scatter Plot with Error Bars

Best for: benchmark scatter, per-case performance distribution.

```latex
% CSV file: scatter.csv
% CaseID,Score,ErrorMin,ErrorMax
% 1,3.5,3.0,4.0
% 2,4.0,3.5,4.0
% ...

\begin{tikzpicture}
\begin{axis}[
    width=10cm, height=5cm,
    xlabel={Case ID},
    ylabel={Score},
    ymin=0, ymax=5,
    xlabel style={font=\small},
    ylabel style={font=\small},
    xticklabel style={font=\footnotesize},
    yticklabel style={font=\footnotesize},
    grid=major,
    grid style={gray!25, dashed},
    axis lines=left,
]

\addplot[
    only marks,
    mark=*,
    mark size=2pt,
    acaBlueLine!80,
    error bars/y dir=both,
    error bars/y explicit,
    error bars/error bar style={line width=0.5pt},
    error bars/error mark options={
        rotate=90,
        mark size=2pt,
        line width=0.5pt,
    },
] table[x=CaseID, y=Score, y error minus=ErrorMin, y error plus=ErrorMax]
    {scatter.csv};

\end{axis}
\end{tikzpicture}
```

## Template 4: Groupplot — Multi-Panel Comparison

Best for: three strategies side-by-side, ablation panels.

```latex
\begin{tikzpicture}
\begin{groupplot}[
    group style={
        group size=3 by 1,
        horizontal sep=1.2cm,
        xlabels at=edge bottom,
        ylabels at=edge left,
    },
    width=0.32\textwidth, height=5cm,
    ybar, bar width=0.5cm,
    ymin=0,
    grid=major, grid style={gray!25, dashed},
    axis lines=left,
    xticklabel style={font=\tiny, rotate=45, anchor=east},
    yticklabel style={font=\footnotesize},
    nodes near coords,
    nodes near coords style={font=\tiny},
    nodes near coords align=vertical,
]

% Panel 1: Static tasks
\nextgroupplot[title={Static Analysis (n=35)}]
\addplot[draw=acaBlueLine, fill=acaBlueFill!60]
    table[x expr=\coordindex, y=Completion] {static.csv};

% Panel 2: Modal tasks
\nextgroupplot[title={Modal Analysis (n=10)}]
\addplot[draw=acaGreenLine, fill=acaGreenFill!60]
    table[x expr=\coordindex, y=Completion] {modal.csv};

% Panel 3: Thermal tasks
\nextgroupplot[title={Thermal Analysis (n=5)}]
\addplot[draw=acaOrangeLine, fill=acaOrangeFill!60]
    table[x expr=\coordindex, y=Completion] {thermal.csv};

\end{groupplot}
\end{tikzpicture}
```

## Template 5: Heatmap / Matrix Visualization

Best for: confusion matrices, correlation matrices, attention maps.

```latex
% Inline data approach for small matrices
\begin{tikzpicture}
\begin{axis}[
    width=6cm, height=6cm,
    colorbar,
    colorbar style={font=\tiny, ylabel={Value}},
    xlabel={Predicted},
    ylabel={Actual},
    xtick=data,
    ytick=data,
    xticklabels={A,B,C},
    yticklabels={C,B,A},
    xticklabel style={font=\footnotesize},
    yticklabel style={font=\footnotesize},
    xlabel style={font=\small},
    ylabel style={font=\small},
    axis on top,  % grid under data
]

\addplot[matrix plot, nodes near coords, point meta=explicit]
    table[x=x, y=y, meta=value] {
        x y value
        1 3 0.92
        2 3 0.04
        3 3 0.04
        1 2 0.05
        2 2 0.89
        3 2 0.06
        1 1 0.03
        2 1 0.07
        3 1 0.90
    };

\end{axis}
\end{tikzpicture}
```

## Template 6: Box Plot / Distribution

Best for: score distributions, runtime distributions, interquartile ranges.

```latex
% Use pgfplots boxplot (requires pgfplots.statistics)
\usetikzlibrary{pgfplots.statistics}

\begin{tikzpicture}
\begin{axis}[
    width=8cm, height=5cm,
    boxplot/draw direction=y,
    xlabel={Strategy},
    ylabel={Score},
    xtick={1,2,3},
    xticklabels={no\_recovery, rule\_only, model\_only},
    xticklabel style={font=\footnotesize, text width=2cm, align=center},
    yticklabel style={font=\footnotesize},
    ylabel style={font=\small},
    axis lines=left,
    grid=major,
    grid style={gray!25, dashed},
]

% Data format: each row is one sample
\addplot+[acaBlueFill, draw=acaBlueLine, thick]
    boxplot prepared={
        lower whisker=1.0, lower quartile=2.0,
        median=2.74, upper quartile=3.5, upper whisker=4.0,
    } coordinates {};
\addplot+[acaGreenFill, draw=acaGreenLine, thick]
    boxplot prepared={
        lower whisker=1.5, lower quartile=2.5,
        median=3.17, upper quartile=3.8, upper whisker=4.0,
    } coordinates {};
\addplot+[acaOrangeFill, draw=acaOrangeLine, thick]
    boxplot prepared={
        lower whisker=2.5, lower quartile=3.2,
        median=3.59, upper quartile=4.0, upper whisker=4.0,
    } coordinates {};

\end{axis}
\end{tikzpicture}
```

## Workflow: CSV -> PGFPlots

1. User provides CSV data (or inline numbers)
2. Identify chart type from data structure:
   - categorical x + numeric y -> bar chart
   - numeric x + numeric y -> line plot
   - x + y + error -> scatter + error bars
   - matrix -> heatmap
   - distributions -> box plot
3. Generate standalone `.tex` with `pgfplots` using the matching template
4. Compile with `pdflatex` (no LuaLaTeX needed for pgfplots)
5. Enforce design rules from section above

## Anti-Patterns to Avoid

- Using `compat` older than 1.8 (default placement differs)
- `\addplot` without `table` for more than 3 data points (hardcoded values)
- Mixing pgfplots with TikZ `\draw plot` (use one or the other)
- Plotting from raw data inline when a CSV file is cleaner
- 3D bar charts (hard to read, avoid unless absolutely necessary)
- Rainbow color cycles (use academic palette instead)
