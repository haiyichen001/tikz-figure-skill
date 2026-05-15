#!/usr/bin/env python3
"""
TikZ Layout Engine — computes exact (x,y) coordinates from text dimensions.
AI defines nodes and stacking order; the engine does the math. No guessing.

Usage:
  python layout-engine.py spec.json > output.tex
  python layout-engine.py spec.json --compile   # also runs pdflatex

Spec format:
{
  "canvas": {"border": 15},                     # standalone border in pt
  "font_coeffs": {                               # cm per char (optional, has defaults)
    "tiny": 0.08, "scriptsize": 0.10, "footnotesize": 0.12,
    "small": 0.15, "normalsize": 0.18
  },
  "line_height_coeff": {"single": 0.22, "double": 0.36},
  "styles": {
    "era": {
      "font": "small/bfseries/sffamily",        # font size/style
      "fill": "acaGreyFill", "draw": "acaGreyLine",
      "inner_sep": 10, "rounded": 6,
      "min_width": null, "min_height": null      # null = auto-size to text
    },
    "method": {
      "font": "footnotesize/sffamily",
      "fill": "acaBlueFill", "draw": "acaBlueLine",
      "inner_sep": 6, "rounded": 3,
      "min_width": null, "min_height": 0.65
    }
  },
  "columns": [                                    # vertical stacks (left to right)
    {
      "x": 1.5,                                   # cm from left
      "nodes": [
        {"id": "e1", "text": "Classical\\nSurrogates", "style": "era", "zone": "grey"},
        {"id": "m1", "text": "PRS", "style": "method", "zone": "grey"},
        {"id": "z_end_1", "text": null}           # marks end of zone 1
      ]
    },
    {"x": 11.5, "nodes": [...]}
  ],
  "gap": 0.25,                                    # cm between stacked nodes
  "zone_padding": 0.3,                            # cm above/below zone content
  "zones": {                                      # background rectangles (optional)
    "grey":  {"fill": "acaGreyFill!30",  "y_start": "auto", "y_end": "auto"},
    "blue":  {"fill": "acaBlueFill!25",  "y_start": "auto", "y_end": "auto"}
  },
  "title": {"text": "Figure Title", "subtitle": "Subtitle line", "y": null},
  "speedup_labels": [...],                        # annotation labels
  "cross_arrows": [...],                          # cross-column arrows
  "callouts": [...]                               # callout boxes
}
"""

import json
import sys
import math
import os
import subprocess
import re
from dataclasses import dataclass, field

# ─── Font metrics ───
DEFAULT_FONT_COEFFS = {
    "tiny": 0.08, "scriptsize": 0.10, "footnotesize": 0.12,
    "small": 0.15, "normalsize": 0.18, "large": 0.22,
    "Large": 0.26, "LARGE": 0.30,
}
DEFAULT_LINE_HEIGHTS = {"single": 0.22, "double": 0.36}

# ─── Academic palette (copied from skill) ───
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


@dataclass
class NodeBox:
    id: str
    text: str
    style: str
    x: float = 0.0
    y: float = 0.0
    width: float = 2.8
    height: float = 0.9
    zone: str = ""
    lines: list[str] = field(default_factory=list)


def estimate_text_size(text: str, font_name: str, font_coeffs: dict,
                       line_heights: dict) -> tuple[float, float, list[str]]:
    """Estimate rendered width and height of text in cm. Returns (w, h, lines)."""
    if not text or text.strip() == "":
        return 0.0, 0.0, [""]

    # Split into lines
    lines = text.split("\\n")

    # Determine font size category
    font_parts = font_name.split("/")
    size_cat = "footnotesize"
    is_bold = "bf" in font_name or "bfseries" in font_name
    is_mono = "tt" in font_name or "ttfamily" in font_name
    for part in font_parts:
        if part in font_coeffs:
            size_cat = part
            break

    char_w = font_coeffs.get(size_cat, 0.12)
    if is_bold:
        char_w *= 1.10
    if is_mono:
        char_w *= 1.15

    line_h = line_heights.get("single", 0.22)

    # Compute max line width
    max_line_w = 0.0
    clean_lines = []
    for line in lines:
        # Strip LaTeX commands for width estimation
        clean = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})*', '', line)
        clean = re.sub(r'[{}$$\\]', '', clean)
        clean = clean.strip()
        clean_lines.append(clean if clean else line)
        w = len(clean) * char_w if clean else 1.0
        max_line_w = max(max_line_w, w)

    total_h = len(lines) * line_h
    return max_line_w, total_h, clean_lines


def build_spec(spec: dict) -> tuple[list[NodeBox], dict, dict]:
    """Process spec, compute all positions, return (nodes, zones_info, meta)."""
    font_coeffs = {**DEFAULT_FONT_COEFFS, **spec.get("font_coeffs", {})}
    line_heights = {**DEFAULT_LINE_HEIGHTS, **spec.get("line_height_coeff", {})}
    gap = spec.get("gap", 0.25)
    zone_pad = spec.get("zone_padding", 0.3)
    styles = spec.get("styles", {})
    columns = spec.get("columns", [])
    zones_cfg = spec.get("zones", {})

    all_nodes = []
    zone_bounds = {}  # zone_name -> (y_min, y_max)

    for col in columns:
        col_x = col["x"]
        current_y = None  # will be set by first node or title

        # Collect active zones in this column
        col_zones = {}

        for node_spec in col["nodes"]:
            nid = node_spec["id"]
            text = node_spec.get("text") or ""
            style_name = node_spec.get("style", "default")
            zone = node_spec.get("zone", "")
            style = styles.get(style_name, {})

            if not text and not style:
                # Zone marker only
                if zone and zone not in col_zones:
                    col_zones[zone] = {"y_start": current_y}
                continue

            # Estimate text dimensions
            font = style.get("font", "footnotesize/sffamily")
            text_w, text_h, lines = estimate_text_size(text, font, font_coeffs, line_heights)

            inner_sep = style.get("inner_sep", 6) / 28.35  # pt to cm approximate
            inner_sep_cm = style.get("inner_sep", 6) * 0.035  # pt to cm

            # Compute node dimensions
            node_w = text_w + 2 * inner_sep_cm + 0.15  # + safety
            node_h = text_h + 2 * inner_sep_cm + 0.1

            # Apply min dimensions from style
            min_w = style.get("min_width")
            min_h = style.get("min_height")
            if min_w and node_w < min_w:
                node_w = min_w
            if min_h and node_h < min_h:
                node_h = min_h

            # Compute y position
            if current_y is None:
                # First node in column
                current_y = spec.get("start_y", 0.0)
                # Account for half height
                node_y = current_y - node_h / 2
            else:
                # Stack below previous: prev_bottom = prev_y - prev_h/2
                # this_top = prev_bottom - gap
                # this_center = this_top + this_h/2
                prev = all_nodes[-1]
                prev_bottom = prev.y - prev.height / 2
                node_y = prev_bottom - gap - node_h / 2

            # Track zone start
            if zone and zone not in col_zones:
                col_zones[zone] = {"y_start": node_y + node_h / 2}

            # Track zone end
            if zone:
                col_zones[zone] = {"y_start": col_zones.get(zone, {}).get("y_start", node_y + node_h / 2),
                                   "y_end": node_y - node_h / 2}

            node = NodeBox(
                id=nid, text=text, style=style_name,
                x=col_x, y=node_y,
                width=node_w, height=node_h,
                zone=zone, lines=lines
            )
            all_nodes.append(node)

            # Update zone end
            if zone:
                col_zones[zone]["y_end"] = node_y - node_h / 2

        # Merge column zone bounds into global
        for zname, bounds in col_zones.items():
            if zname not in zone_bounds:
                zone_bounds[zname] = {"y_top": bounds["y_start"] + zone_pad,
                                       "y_bot": bounds["y_end"] - zone_pad}
            else:
                zone_bounds[zname]["y_top"] = max(zone_bounds[zname]["y_top"],
                                                   bounds["y_start"] + zone_pad)
                zone_bounds[zname]["y_bot"] = min(zone_bounds[zname]["y_bot"],
                                                   bounds["y_end"] - zone_pad)

    # Compute canvas bounds
    if all_nodes:
        min_x = min(n.x - n.width / 2 for n in all_nodes) - 1.0
        max_x = max(n.x + n.width / 2 for n in all_nodes) + 1.0
        min_y = min(n.y - n.height / 2 for n in all_nodes) - 1.0
        max_y = max(n.y + n.height / 2 for n in all_nodes) + 1.0
    else:
        min_x, max_x, min_y, max_y = -1, 20, -23, 2

    meta = {
        "canvas": {"x0": min_x, "x1": max_x, "y0": min_y, "y1": max_y,
                   "width": max_x - min_x, "height": max_y - min_y},
        "border": spec.get("canvas", {}).get("border", 15),
        "zone_bounds": zone_bounds,
        "zones_cfg": zones_cfg,
        "title": spec.get("title"),
        "gap": gap,
    }
    return all_nodes, meta, styles


def generate_tex(nodes: list[NodeBox], meta: dict, styles: dict, spec: dict) -> str:
    """Generate complete standalone .tex from computed positions."""
    border = meta["border"]
    lines = []

    # Preamble
    lines.append(r"\documentclass[tikz,border=" + str(border) + r"pt]{standalone}")
    lines.append(r"\usepackage{tikz}")
    lines.append(r"\usepackage{amsmath,amssymb}")
    lines.append(r"\usetikzlibrary{arrows.meta,shadows,backgrounds}")
    lines.append("")
    lines.append(ACADEMIC_COLORS)
    lines.append(r"\pgfdeclarelayer{bg}")
    lines.append(r"\pgfsetlayers{bg,main}")
    lines.append("")

    # Style definitions
    lines.append(r"\begin{document}")
    lines.append(r"\begin{tikzpicture}[")
    for sname, sdef in styles.items():
        fill = sdef.get("fill", "white")
        draw = sdef.get("draw", "black")
        rounded = sdef.get("rounded", 3)
        font = sdef.get("font", "footnotesize/sffamily")
        font_cmd = "\\" + font.replace("/", "\\")
        inner = sdef.get("inner_sep", 6)
        lines.append(f"    {sname}/.style={{rectangle,rounded corners={rounded}pt,"
                     f"align=center,font={font_cmd},inner sep={inner}pt,"
                     f"fill={fill},draw={draw}}},")
    lines.append("    arr/.style={->,>=Stealth,line width=1.2pt,color=black!55},")
    lines.append("    darr/.style={->,>=Stealth,line width=0.7pt,dashed,color=black!45},")
    lines.append("]")
    lines.append("")

    # Zone backgrounds
    zone_bounds = meta.get("zone_bounds", {})
    zones_cfg = meta.get("zones_cfg", {})
    if zone_bounds:
        lines.append(r"% === Zone backgrounds ===")
        lines.append(r"\begin{pgfonlayer}{bg}")
        canvas = meta["canvas"]
        for zname, zcfg in zones_cfg.items():
            if zname not in zone_bounds:
                continue
            zb = zone_bounds[zname]
            fill = zcfg.get("fill", "white")
            yt = zb["y_top"]
            yb = zb["y_bot"]
            lines.append(f"  \\fill[{fill},rounded corners=8pt] "
                         f"({canvas['x0']:.1f},{yt:.1f}) rectangle ({canvas['x1']:.1f},{yb:.1f});")
        lines.append(r"\end{pgfonlayer}")
        lines.append("")

    # Title
    title = meta.get("title")
    if title:
        title_y = meta["canvas"]["y1"] - 0.8
        lines.append(f"\\node[font=\\Large\\bfseries\\sffamily] at "
                     f"({(meta['canvas']['x0']+meta['canvas']['x1'])/2:.1f},{title_y:.1f}) "
                     f"{{{title['text']}}};")
        if title.get("subtitle"):
            lines.append(f"\\node[font=\\footnotesize\\sffamily,acaGreyLine] at "
                         f"({(meta['canvas']['x0']+meta['canvas']['x1'])/2:.1f},{title_y-0.6:.1f}) "
                         f"{{{title['subtitle']}}};")
            meta["canvas"]["y1"] = title_y + 0.5
        lines.append("")

    # Nodes
    lines.append(r"% === Nodes ===")
    for node in nodes:
        style = node.style
        sdef = styles.get(style, {})
        fill = sdef.get("fill", "white")
        draw = sdef.get("draw", "black")
        rounded = sdef.get("rounded", 3)
        font = sdef.get("font", "footnotesize/sffamily")
        font_cmd = "\\" + font.replace("/", "\\")
        inner = sdef.get("inner_sep", 6)
        drop_shadow = "drop shadow={opacity=0.12}," if style == "era" else ""

        # Skip null-text nodes (zone markers)
        if not node.text or not node.text.strip():
            continue

        # Escape text for LaTeX (preserve math mode and LaTeX commands)
        raw = node.text.replace("\\n", "\\\\")
        # Protect math mode sections from escaping
        parts = re.split(r'(\$[^$]*\$)', raw)
        escaped_parts = []
        for part in parts:
            if part.startswith("$") and part.endswith("$"):
                escaped_parts.append(part)  # keep math mode intact
            else:
                p = part.replace("_", "\\_")
                p = p.replace("&", "\\&")
                p = p.replace("%", "\\%")
                p = p.replace("#", "\\#")
                escaped_parts.append(p)
        escaped = "".join(escaped_parts)

        # For tiny sub-labels on era nodes
        if "\\n" in node.text:
            parts = node.text.split("\\n")
            if len(parts) == 2 and style == "era":
                escaped = f"{parts[0]}\\\\[-2pt]\\scriptsize {parts[1]}"

        lines.append(f"\\node[{style}] ({node.id}) at ({node.x:.2f},{node.y:.2f}) {{{escaped}}};")

    lines.append("")

    # Cross-column arrows
    cross_arrows = spec.get("cross_arrows", [])
    if cross_arrows:
        lines.append(r"% === Cross arrows ===")
        for arrow in cross_arrows:
            from_id = arrow["from"]
            to_id = arrow["to"]
            style = arrow.get("style", "arr")
            lbl = arrow.get("label", "")
            # Find nodes
            from_node = next((n for n in nodes if n.id == from_id), None)
            to_node = next((n for n in nodes if n.id == to_id), None)
            if from_node and to_node:
                if lbl:
                    lines.append(f"\\draw[{style}] ({from_id}.east) -| "
                                 f"({(from_node.x+to_node.x)/2:.1f},{from_node.y:.1f}) |- "
                                 f"({to_id}.east) node[lbl,pos=0.6,right=1pt] {{{lbl}}};")
                else:
                    lines.append(f"\\draw[{style}] ({from_id}.west) -| "
                                 f"({(from_node.x+to_node.x)/2:.1f},{(from_node.y+to_node.y)/2:.1f}) |- "
                                 f"({to_id}.west);")
        lines.append("")

    # Timeline arrows between eras
    timeline = spec.get("timeline", [])
    if timeline:
        lines.append(r"% === Timeline arrows ===")
        # Draw vertical backbone
        t_x = spec["columns"][0]["x"]
        y_top = max(n.y for n in nodes) + 0.5
        y_bot = min(n.y for n in nodes) - 0.5
        lines.append(f"\\draw[line width=3pt,acaGreyLine!30,rounded corners=4pt] "
                     f"({t_x:.1f},{y_top:.1f}) -- ({t_x:.1f},{y_bot:.1f});")
        for t in timeline:
            lines.append(f"\\draw[arr,acaOrangeLine!80,line width=1.5pt] "
                         f"({t['from']}.west) -| ({t_x:.1f},{t['mid_y']:.1f}) |- ({t['to']}.west);")
        lines.append("")

    # Speedup labels (annotations on timeline)
    speedup = spec.get("speedup_labels", [])
    for sl in speedup:
        lines.append(f"\\node[font=\\tiny\\sffamily\\bfseries,acaOrangeLine] "
                     f"at ({sl['x']:.1f},{sl['y']:.1f}) {{{sl['text']}}};")
    if speedup:
        lines.append("")

    # Callouts
    callouts = spec.get("callouts", [])
    for co in callouts:
        lines.append(f"\\node[draw=acaRedLine!80,fill=acaRedFill!30,rounded corners=4pt,"
                     f"font=\\tiny\\sffamily,text width={co.get('width',3.4)}cm,"
                     f"align=left,inner sep=4pt] at ({co['x']:.1f},{co['y']:.1f}) {{{co['text']}}};")
        lines.append(f"\\draw[arr,acaRedLine] ({co['x']:.1f},{co['y']+co.get('h',0.6):.1f}) "
                     f"-- ({co['x']:.1f},{co['y']+co.get('h',0.6)+0.5:.1f});")
    if callouts:
        lines.append("")

    # Close
    lines.append(r"\end{tikzpicture}")
    lines.append(r"\end{document}")

    return "\n".join(lines)


def validate_no_overlaps(nodes: list[NodeBox], gap: float) -> list[str]:
    """Check for overlapping nodes. Returns list of warnings."""
    warnings = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            # Only check same-column nodes
            if abs(a.x - b.x) > 0.1:
                continue
            # Check vertical overlap
            a_bot = a.y - a.height / 2
            a_top = a.y + a.height / 2
            b_bot = b.y - b.height / 2
            b_top = b.y + b.height / 2
            # Determine which is above
            if a.y > b.y:
                upper, lower = a, b
                upper_bot = a_bot
                lower_top = b_top
            else:
                upper, lower = b, a
                upper_bot = b_bot
                lower_top = a_top
            edge_gap = lower_top - upper_bot
            if edge_gap > -0.01:
                warnings.append(f"OVERLAP: '{upper.id}' (bot={upper_bot:.2f}) "
                                f"and '{lower.id}' (top={lower_top:.2f}), "
                                f"gap={edge_gap:.3f}cm (need <-0.01)")
    return warnings


# ─── Main ───

def main():
    if len(sys.argv) < 2:
        print("Usage: python layout-engine.py spec.json [--compile]")
        print("       python layout-engine.py spec.json > output.tex")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        spec = json.load(f)

    nodes, meta, styles = build_spec(spec)
    tex = generate_tex(nodes, meta, styles, spec)

    # Check for overlaps before output
    gap = spec.get("gap", 0.25)
    warnings = validate_no_overlaps(nodes, gap)
    if warnings:
        print("% ⚠ Layout warnings:", file=sys.stderr)
        for w in warnings:
            print(f"%   {w}", file=sys.stderr)
        print("%", file=sys.stderr)
    else:
        print("% ✓ No overlaps detected", file=sys.stderr)

    if "--compile" in sys.argv or "--output" in sys.argv:
        out_tex = spec.get("output", "layout_output.tex")
        if "--output" in sys.argv:
            idx = sys.argv.index("--output")
            if idx + 1 < len(sys.argv):
                out_tex = sys.argv[idx + 1]
        with open(out_tex, "w", encoding="utf-8") as f:
            f.write(tex)
        print(f"% Wrote {out_tex}", file=sys.stderr)
        if "--compile" in sys.argv:
            for engine in ["pdflatex", "lualatex", "xelatex"]:
                try:
                    subprocess.run([engine, "-interaction=nonstopmode", out_tex],
                                   check=True, timeout=60, cwd=os.path.dirname(os.path.abspath(out_tex)))
                    print(f"% Compiled with {engine}", file=sys.stderr)
                    break
                except Exception:
                    continue
    else:
        print(tex)


if __name__ == "__main__":
    main()
