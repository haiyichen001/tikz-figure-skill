#!/usr/bin/env python3
r"""
TikZ Layout Engine v3 — compute-then-render pipeline.

Phase 1 (Python): estimate text sizes → stack nodes → assign (x,y)
Phase 2 (LaTeX):  output \node at (x,y) + orthogonal \draw -| edges

AI writes zero coordinates. Engine does all the math.
Output: professional orthogonal edges with rounded corners.

Usage:
  python layout-engine.py spec.json --output file.tex
  python layout-engine.py spec.json --compile

Spec:
{
  "title": {"text": "...", "subtitle": "..."},
  "layout": {"column_gap": 3.5, "row_gap": 0.35, "rail_pad": 1.2},
  "styles": {"my": {"font":"footnotesize/sffamily","fill":"acaBlueFill","draw":"acaBlueLine","inner_sep":8,"rounded":4}},
  "groups": [
    {"x": 1.5, "label": "Timeline", "nodes": [{"id":"a","text":"Node","style":"my"}]},
    {"x": 10.0, "label": "Main", "nodes": [{"id":"b","text":"Node","style":"my"}]}
  ],
  "edges": [
    {"from":"a","to":"b","type":"main"},
    {"from":"c","to":"d","type":"feedback"}
  ],
  "edge_types": {
    "main":     "thick,acaOrangeLine,rounded corners=6pt",
    "flow":     "thick,black!55,rounded corners=4pt",
    "feedback": "dashed,acaRedLine!60,rounded corners=6pt"
  }
}
"""

import json, sys, os, re, subprocess

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

TIKZ_RESERVED = {"out","in","to","edge","node","graph","draw","fill",
    "path","scope","pic","label","pin","alias","matrix",
    "align","text","font","anchor","scale","rotate","x","y",
    "at","name","shape","inner","outer","minimum","maximum"}

FONT_W = {"tiny":0.08,"scriptsize":0.10,"footnotesize":0.12,
          "small":0.15,"normalsize":0.18,"large":0.22,"Large":0.26}
LINE_H = 0.22  # cm per line
INNER_SEP_CM = 0.035  # per pt, approximate

def make_style_defs(styles):
    lines = [r"\tikzset{"]
    for sname, sdef in styles.items():
        safe = f"s_{sname}" if sname in TIKZ_RESERVED else sname
        fill = sdef.get("fill","white"); draw = sdef.get("draw","black")
        rounded = sdef.get("rounded",3); inner = sdef.get("inner_sep",6)
        font = sdef.get("font","footnotesize/sffamily")
        font_cmd = "\\" + font.replace("/","\\")
        lines.append(f"  {safe}/.style={{rectangle,rounded corners={rounded}pt,"
                     f"align=center,font={font_cmd},inner sep={inner}pt,"
                     f"fill={fill},draw={draw}}},")
    lines.append("}")
    return "\n".join(lines)

def safe_style(name):
    return f"s_{name}" if name in TIKZ_RESERVED else name

def est_text_dims(text, font_str):
    """Estimate rendered text width and height in cm."""
    parts = font_str.split("/")
    size = "footnotesize"
    bold = any(p in font_str for p in ["bf","bfseries"])
    for p in parts:
        if p in FONT_W:
            size = p; break
    cw = FONT_W.get(size, 0.12) * (1.10 if bold else 1.0)
    lines = text.replace("|","\n").split("\n")
    max_w = 0
    for line in lines:
        clean = re.sub(r'\$[^$]*\$','XXX',line)  # math as 3 chars
        clean = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})*','',clean)
        clean = re.sub(r'[{}]','',clean)
        max_w = max(max_w, len(clean) * cw)
    return max_w, len(lines) * LINE_H

def compute_layout(spec):
    """Phase 1: compute absolute (x,y) for every node."""
    groups = spec.get("groups",[])
    styles = spec.get("styles",{})
    cfg = spec.get("layout",{})
    col_gap = cfg.get("column_gap",3.8)
    row_gap = cfg.get("row_gap",0.5)
    all_nodes = []
    x_positions = {}
    col_extents = {}  # col_idx -> (x, max_width, y_min, y_max)

    for gi, grp in enumerate(groups):
        gx = grp["x"]
        col_nodes = grp.get("nodes",[])
        max_w = 0
        positioned = []
        prev_y = None
        prev_h = 0

        for ns in col_nodes:
            nid = ns["id"]; text = ns.get("text","")
            st_name = ns.get("style","default")
            st = styles.get(st_name,{})
            font = st.get("font","footnotesize/sffamily")
            inner = st.get("inner_sep",6)
            tw, th = est_text_dims(text, font)
            pad = inner * INNER_SEP_CM
            nw = tw + 2*pad + 0.2  # + safety margin
            nh = th + 2*pad + 0.1
            max_w = max(max_w, nw)

            if prev_y is None:
                ny = 0.0  # first node at y=0
            else:
                # stack below
                ny = prev_y - prev_h/2 - row_gap - nh/2

            positioned.append({"id":nid,"text":text,"style":st_name,
                               "width":nw,"height":nh,"y":ny,
                               "x":gx,"group":gi})
            prev_y = ny; prev_h = nh

        # Center nodes within column
        for pn in positioned:
            pn["x"] = gx

        col_extents[gi] = {"x":gx, "max_w":max_w,
                           "y_top":positioned[0]["y"]+positioned[0]["height"]/2 if positioned else 0,
                           "y_bot":positioned[-1]["y"]-positioned[-1]["height"]/2 if positioned else 0}
        all_nodes.extend(positioned)
        x_positions[gi] = gx

    # Compute rail positions (right side of all content, left side)
    if all_nodes:
        rightmost = max(n["x"]+n["width"]/2 for n in all_nodes)
        leftmost  = min(n["x"]-n["width"]/2 for n in all_nodes)
        rail_pad = cfg.get("rail_pad",1.5)
        right_rail = rightmost + rail_pad
        left_rail  = leftmost  - rail_pad
    else:
        right_rail, left_rail = 15, -1

    meta = {"right_rail":right_rail, "left_rail":left_rail,
            "column_gap":col_gap, "row_gap":row_gap,
            "x_positions":x_positions, "col_extents":col_extents}
    return all_nodes, meta

def generate_tex(all_nodes, meta, spec):
    """Phase 2: output .tex with absolute coords + orthogonal edges."""
    border = spec.get("canvas",{}).get("border",15)
    styles = spec.get("styles",{})
    edges = spec.get("edges",[])
    edge_types = spec.get("edge_types",{
        "main":"thick,acaOrangeLine,rounded corners=6pt",
        "flow":"thick,black!55,rounded corners=4pt",
        "feedback":"dashed,acaRedLine!60,rounded corners=6pt"})
    title = spec.get("title")
    groups = spec.get("groups",[])
    node_map = {n["id"]:n for n in all_nodes}
    rail = meta["right_rail"]
    left_rail = meta["left_rail"]
    lines = []

    # Preamble
    lines.append(r"\documentclass[tikz,border="+str(border)+r"pt]{standalone}")
    lines.append(r"\usepackage{tikz,amsmath,amssymb}")
    lines.append(r"\usetikzlibrary{arrows.meta,backgrounds}")
    lines.append("")
    lines.append(ACADEMIC_COLORS)
    lines.append(r"\pgfdeclarelayer{bg}")
    lines.append(r"\pgfsetlayers{bg,main}")
    lines.append("")
    lines.append(r"\begin{document}")
    lines.append(r"\begin{tikzpicture}[")
    lines.append(r"  >={Stealth},line cap=round,")
    lines.append(r"  every node/.style={outer sep=3pt},")
    lines.append(r"]")

    # Title
    cx = (meta["left_rail"]+rail)/2 if all_nodes else 10
    if title:
        lines.append(f"\\node[font=\\Large\\bfseries\\sffamily,align=center] at ({cx:.1f},1.5) {{{title['text']}}};")
        if title.get("subtitle"):
            lines.append(f"\\node[font=\\footnotesize\\sffamily,color=acaGreyLine] at ({cx:.1f},0.7) {{{title['subtitle']}}};")

    # Style defs
    lines.append(make_style_defs(styles))

    # Nodes
    lines.append("\n% === Nodes ===")
    for n in all_nodes:
        st = safe_style(n["style"])
        txt = n["text"].replace("|","\\\\")
        parts = txt.split("\\\\"); wrapped = []
        for p in parts:
            p = p.strip()
            if (("^" in p or "_" in p) and not p.startswith("$")): p = "$" + p + "$"
            wrapped.append(p)
        txt = "\\\\".join(wrapped)
        lines.append(f"\\node[{st}] ({n['id']}) at ({n['x']:.2f},{n['y']:.2f}) {{{txt}}};")

    # Edges — orthogonal routing via rail
    lines.append("\n% === Edges ===")
    for e in edges:
        fid, tid = e["from"], e["to"]
        etype = e.get("type","flow")
        estyle = edge_types.get(etype, edge_types["flow"])
        label = e.get("label","")

        src = node_map.get(fid)
        dst = node_map.get(tid)
        if not src or not dst:
            lines.append(f"% Edge {fid}->{tid}: node not found")
            continue

        sx, sy = src["x"], src["y"]
        dx, dy = dst["x"], dst["y"]
        sw, sh = src["width"], src["height"]
        dw, dh = dst["width"], dst["height"]

        # Straight when aligned, L-shaped only when y differs.
        # shorten only for horizontal/cross-column (gap is large).
        # No shorten for vertical (row_gap=0.3cm is already tight).
        is_vert = abs(sx - dx) < 0.5
        lbl = f" node[midway,above,font=\\tiny\\sffamily,color=acaGreyLine] {{{label}}}" if label else ""
        if is_vert:
            lines.append(f"\\draw[{estyle}] ({fid}.south) -- ({tid}.north){lbl};")
        elif abs(sy - dy) < 0.3:
            if sx < dx:
                lines.append(f"\\draw[{estyle}] ({fid}.east) -- ({tid}.west){lbl};")
            else:
                lines.append(f"\\draw[{estyle}] ({fid}.west) -- ({tid}.east){lbl};")
        elif sx < dx:
            lines.append(f"\\draw[{estyle}] ({fid}.east) -| ({tid}.west){lbl};")
        else:
            lines.append(f"\\draw[{estyle}] ({fid}.west) -| ({tid}.east){lbl};")

    # Zone backgrounds
    if groups:
        lines.append("\n% === Zones ===")
        lines.append(r"\begin{pgfonlayer}{bg}")
        zone_colors = ["acaBlueFill!15","acaGreenFill!15","acaPurpleFill!15",
                       "acaOrangeFill!15","acaRedFill!15"]
        for gi, grp in enumerate(groups):
            col = meta["col_extents"].get(gi,{})
            if not col: continue
            zc = zone_colors[gi % len(zone_colors)]
            x0 = col["x"] - col["max_w"]/2 - 0.5
            x1 = col["x"] + col["max_w"]/2 + 0.5
            y0 = col["y_bot"] - 0.4
            y1 = col["y_top"] + 0.4
            lines.append(f"  \\fill[{zc},rounded corners=6pt] ({x0:.1f},{y0:.1f}) rectangle ({x1:.1f},{y1:.1f});")
            # Zone label
            label = grp.get("label","")
            if label:
                lines.append(f"  \\node[font=\\tiny\\sffamily\\bfseries,acaGreyLine] at ({x0+0.5:.1f},{y1-0.15:.1f}) {{{label}}};")
        lines.append(r"\end{pgfonlayer}")

    lines.append(r"\end{tikzpicture}")
    lines.append(r"\end{document}")
    return "\n".join(lines)

def generate(spec):
    nodes, meta = compute_layout(spec)
    return generate_tex(nodes, meta, spec)

def main():
    if len(sys.argv) < 2:
        print("Usage: python layout-engine.py spec.json [--compile] [--output file.tex]")
        sys.exit(1)
    with open(sys.argv[1],"r",encoding="utf-8") as f:
        spec = json.load(f)
    tex = generate(spec)
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        out = sys.argv[idx+1] if idx+1<len(sys.argv) else spec.get("output","layout_output.tex")
    elif "--compile" in sys.argv:
        out = spec.get("output","layout_output.tex")
    else:
        print(tex); return
    with open(out,"w",encoding="utf-8") as f:
        f.write(tex)
    print(f"Wrote: {out}",file=sys.stderr)
    if "--compile" in sys.argv:
        cwd = os.path.dirname(os.path.abspath(out))
        subprocess.run(["lualatex","-interaction=nonstopmode",out],check=True,timeout=120,cwd=cwd)
        print("Compiled",file=sys.stderr)

if __name__ == "__main__":
    main()
