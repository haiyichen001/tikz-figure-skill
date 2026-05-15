#!/usr/bin/env python3
r"""
TikZ Layout Engine — graphdrawing mode.
AI defines nodes and edges in a JSON spec. LuaLaTeX computes all positions
and routes edges at compile time via Sugiyama layered layout algorithm.
No manual coordinates. No overlap. No edge-crossing-boxes.

Usage:
  python layout-engine.py spec.json --output file.tex
  python layout-engine.py spec.json --compile

Spec format:
{
  "canvas": {"border": 15},
  "title": {"text": "Figure Title", "subtitle": "Subtitle line"},
  "styles": {
    "my_style": {
      "font": "footnotesize/sffamily", "fill": "acaBlueFill", "draw": "acaBlueLine",
      "inner_sep": 6, "rounded": 3
    }
  },
  "nodes": [
    {"id": "a", "text": "Node A", "style": "my_style", "layer": 0},
    {"id": "b", "text": "Node B", "style": "my_style", "layer": 1}
  ],
  "edges": [
    {"from": "a", "to": "b"},
    {"from": "a", "to": "c", "style": "dashed,red!50", "label": "skip"}
  ]
}
"""

import json
import sys
import os
import subprocess

ACADEMIC_COLORS = r"""\definecolor{acaBlueLine}{HTML}{6080B0}
\definecolor{acaBlueFill}{HTML}{DBEAFE}
\definecolor{acaGreenLine}{HTML}{30A060}
\definecolor{acaGreenFill}{HTML}{A0D0A0}
\definecolor{acaOrangeLine}{HTML}{D06020}
\definecolor{acaOrangeFill}{HTML}{FFE6CC}
\definecolor{acaPurpleLine}{HTML}{6020D0}
\definecolor{acaPurpleFill}{HTML}{E1D5E7}
\definecolor{acaRedLine}{HTML}{B05050}
\definecolor{acaRedFill}{HTML}{F8CECC}
\definecolor{acaGreyLine}{HTML}{666666}
\definecolor{acaGreyFill}{HTML}{F5F5F5}"""


def generate(spec: dict) -> str:
    border = spec.get("canvas", {}).get("border", 15)
    styles = spec.get("styles", {})
    nodes = spec.get("nodes", [])
    edges = spec.get("edges", [])
    title = spec.get("title")
    lines = []

    # Preamble
    lines.append(r"\documentclass[tikz,border=" + str(border) + r"pt]{standalone}")
    lines.append(r"\usepackage{tikz}")
    lines.append(r"\usepackage{amsmath,amssymb}")
    lines.append(r"\usetikzlibrary{graphs,graphdrawing,arrows.meta,bbox}")
    lines.append(r"\usegdlibrary{layered,force}")
    lines.append("")
    lines.append(ACADEMIC_COLORS)
    lines.append("")
    lines.append(r"\begin{document}")
    lines.append(r"\begin{tikzpicture}[arr/.style={->,>=Stealth,thick,color=black!55}]")

    # Title inside tikzpicture
    if title:
        lines.append(r"\node[font=\Large\bfseries\sffamily,align=center] at (10,3) {"
                     + title["text"] + r"};")
        if title.get("subtitle"):
            lines.append(r"\node[font=\normalsize\sffamily,color=acaGreyLine] at (10,2.3) {"
                         + title["subtitle"] + r"};")

    # Style definitions
    # TikZ reserved keys that conflict with style names
    TIKZ_RESERVED = {"out", "in", "to", "edge", "node", "graph", "draw", "fill",
                     "path", "scope", "pic", "label", "pin", "alias", "matrix",
                     "align", "text", "font", "anchor", "scale", "rotate", "x", "y",
                     "at", "name", "shape", "inner", "outer", "minimum", "maximum"}
    lines.append(r"\tikzset{")
    for sname, sdef in styles.items():
        if sname in TIKZ_RESERVED:
            sname = "s_" + sname  # prefix to avoid collision
        fill = sdef.get("fill", "white")
        draw = sdef.get("draw", "black")
        rounded = sdef.get("rounded", 3)
        font = sdef.get("font", "footnotesize/sffamily")
        inner = sdef.get("inner_sep", 6)
        font_cmd = "\\" + font.replace("/", "\\")
        lines.append(f"  {sname}/.style={{rectangle,rounded corners={rounded}pt,"
                     f"align=center,font={font_cmd},inner sep={inner}pt,"
                     f"fill={fill},draw={draw}}},")
    lines.append("}")

    # Graph
    lines.append(r"\graph[")
    lines.append(r"  layered layout,")
    lines.append(r"  grow=right,")
    lines.append(r"  level distance=2.8cm,")
    lines.append(r"  sibling distance=1.0cm,")
    lines.append(r"  nodes={align=center,inner sep=6pt,font=\footnotesize\sffamily},")
    lines.append(r"  edges={arr},")
    lines.append(r"] {")

    # Group nodes by layer
    layers = {}
    for n in nodes:
        layer = n.get("layer", 0)
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(n)

    for layer_idx in sorted(layers.keys()):
        layer_nodes = layers[layer_idx]
        ids = []
        for n in layer_nodes:
            # Convert | to LaTeX line break \\, escape special chars
            txt = n["text"].replace("|", r"\\")
            # Protect # and unbalanced braces
            txt = txt.replace("#", "\\#")
            st = n["style"]
            if st in TIKZ_RESERVED:
                st = "s_" + st
            ids.append(f'{n["id"]}/"{txt}" [{st}]')
        lines.append("  " + ", ".join(ids) + ";")

    # Edges
    for e in edges:
        fid, tid = e["from"], e["to"]
        style = e.get("style", "")
        label = e.get("label", "").replace("|", r"\\")
        if label and style:
            lines.append(f'  ({fid}) ->["{label}" {style}] ({tid});')
        elif label:
            lines.append(f'  ({fid}) ->["{label}"] ({tid});')
        elif style:
            lines.append(f'  ({fid}) ->[{style}] ({tid});')
        else:
            lines.append(f'  ({fid}) -> ({tid});')

    lines.append("};")
    lines.append(r"\end{tikzpicture}")
    lines.append(r"\end{document}")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python layout-engine.py spec.json [--compile] [--output file.tex]")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        spec = json.load(f)

    tex = generate(spec)

    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        out_tex = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else spec.get("output", "layout_output.tex")
    elif "--compile" in sys.argv:
        out_tex = spec.get("output", "layout_output.tex")
    else:
        print(tex)
        return

    with open(out_tex, "w", encoding="utf-8") as f:
        f.write(tex)
    print(f"Wrote: {out_tex}", file=sys.stderr)

    if "--compile" in sys.argv:
        cwd = os.path.dirname(os.path.abspath(out_tex))
        base = os.path.splitext(os.path.basename(out_tex))[0]
        subprocess.run(["lualatex", "-interaction=nonstopmode", out_tex],
                       check=True, timeout=120, cwd=cwd)
        # Auto-crop with pdfcrop if available
        pdf = os.path.join(cwd, base + ".pdf")
        cropped = os.path.join(cwd, base + "_cropped.pdf")
        try:
            subprocess.run(["pdfcrop", pdf, cropped],
                           check=True, timeout=30, cwd=cwd)
            os.replace(cropped, pdf)
            print("Compiled + cropped with lualatex", file=sys.stderr)
        except Exception:
            print("Compiled with lualatex (pdfcrop not available)", file=sys.stderr)


if __name__ == "__main__":
    main()
