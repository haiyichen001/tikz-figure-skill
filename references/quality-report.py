#!/usr/bin/env python3
"""
Quality Report Sensor — measures, never enforces.
Outputs structured findings. The AI model (Claude) reads the report
and decides whether each finding needs a fix.

Usage: python quality-report.py output.tex [output.pdf]
"""

import sys, re, json

def parse_dimensions(tex_path, pdf_path=None):
    """Extract canvas dimensions from .tex or .pdf."""
    w_pt, h_pt = 0, 0
    # Try PDF first
    if pdf_path:
        try:
            import fitz
            doc = fitz.open(pdf_path)
            page = doc[0]
            w_pt = page.rect.width
            h_pt = page.rect.height
            doc.close()
            return w_pt, h_pt
        except: pass
    # Fallback: estimate from tex
    try:
        with open(tex_path, encoding='utf-8') as f:
            tex = f.read()
        # Find node coordinates
        ys = [float(m.group(2)) for m in re.finditer(r'at\s*\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)', tex)]
        xs = [float(m.group(1)) for m in re.finditer(r'at\s*\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)', tex)]
        if xs and ys:
            w_cm = (max(xs) - min(xs)) * 1.3 + 3
            h_cm = (max(ys) - min(ys)) * 1.3 + 3
            w_pt = w_cm * 28.35
            h_pt = h_cm * 28.35
    except: pass
    return w_pt, h_pt

def findings(tex_path, pdf_path=None):
    """Generate sensor readings. Never modifies anything."""
    results = []
    w_pt, h_pt = parse_dimensions(tex_path, pdf_path)

    # 1. Aspect ratio
    if w_pt > 0 and h_pt > 0:
        ratio = w_pt / h_pt if h_pt > 0 else 0
        single_col = 252  # pt, Nature/IEEE single column
        double_col = 504  # pt
        if ratio > 3.5:
            results.append({"level":"WARN","check":"aspect-ratio",
                "message":f"Aspect ratio {ratio:.1f}:1 — very wide. May need figure* (double column) or rotate.",
                "data":{"ratio":round(ratio,1),"width_pt":round(w_pt),"height_pt":round(h_pt),
                "fits_single_col":w_pt <= single_col,"fits_double_col":w_pt <= double_col}})
        elif ratio > 2.5:
            results.append({"level":"WARN","check":"aspect-ratio",
                "message":f"Aspect ratio {ratio:.1f}:1 — moderately wide. Check if single column works.",
                "data":{"ratio":round(ratio,1)}})

    # 2. Content density
    if pdf_path:
        try:
            import fitz
            doc = fitz.open(pdf_path)
            page = doc[0]
            # Get all drawings and text blocks
            drawings = page.get_drawings()
            text_blocks = page.get_text("blocks")
            total = w_pt * h_pt if w_pt > 0 else 1
            content_area = 0
            for d in drawings:
                r = d["rect"]
                content_area += (r.x1-r.x0) * (r.y1-r.y0)
            for t in text_blocks:
                content_area += (t[2]-t[0]) * (t[3]-t[1])
            density = content_area / total * 100 if total > 0 else 0
            results.append({"level":"WARN","check":"content-density",
                "message":f"Content fills {density:.1f}% of canvas.",
                "data":{"density_pct":round(density,1)}})
            if density < 3:
                results.append({"level":"WARN","check":"content-density",
                    "message":f"Very sparse ({density:.1f}%). Consider reducing canvas or adding zones."})
            doc.close()
        except: pass

    # 3. Orphan nodes (nodes with no edges)
    try:
        with open(tex_path, encoding='utf-8') as f:
            tex = f.read()
        nodes = set(re.findall(r'\\node\[[^\]]*\]\s*\((\w+)\)', tex))
        edges_from = set(re.findall(r'\((\w+)\)\s*[-|]', tex))
        edges_to = set(re.findall(r'[-|]\s*\((\w+)\)', tex))
        # also catch -- and -> patterns
        edges_from |= set(re.findall(r'\((\w+)\.(?:east|west|north|south)\)', tex))
        edges_to   |= set(re.findall(r'(?:east|west|north|south)\)\s*[-|].*\((\w+)\.(?:east|west|north|south)', tex))
        connected = edges_from | edges_to
        orphans = nodes - connected - {'title','subtitle','legend','input','output','probs'}
        if orphans:
            results.append({"level":"WARN","check":"orphan-nodes",
                "message":f"Nodes with no visible edges: {', '.join(sorted(orphans))}. Intentional or missing connections?"})
    except: pass

    # 4. Balance (left-right weight distribution)
    try:
        xs = [float(m.group(1)) for m in re.finditer(r'at\s*\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)', tex)]
        if xs:
            mid = (min(xs) + max(xs)) / 2
            left_count = sum(1 for x in xs if x < mid)
            right_count = sum(1 for x in xs if x > mid)
            imbalance = abs(left_count - right_count) / max(len(xs), 1) * 100
            if imbalance > 40:
                results.append({"level":"WARN","check":"layout-balance",
                    "message":f"Layout imbalance: {left_count} nodes left, {right_count} right ({imbalance:.0f}% skew)."})
            elif imbalance > 25:
                results.append({"level":"WARN","check":"layout-balance",
                    "message":f"Moderate imbalance: {left_count} left, {right_count} right ({imbalance:.0f}%)."})
    except: pass

    # 5. Font readability — estimate if scaled text is readable
    if w_pt > 0:
        scale_to_single = 252 / w_pt if w_pt > 252 else 1.0
        tiny_size = 5 * scale_to_single  # 5pt tiny scaled to single column
        if tiny_size < 4:
            results.append({"level":"WARN","check":"font-scaling",
                "message":f"When scaled to single column (252pt), tiny text shrinks to {tiny_size:.1f}pt. May be unreadable."})

    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python quality-report.py output.tex [output.pdf]")
        sys.exit(1)
    tex = sys.argv[1]
    pdf = sys.argv[2] if len(sys.argv) > 2 else None
    report = findings(tex, pdf)
    if not report:
        print("PASS — no quality concerns detected")
    else:
        errors = [r for r in report if r["level"]=="ERROR"]
        warns  = [r for r in report if r["level"]=="WARN"]
        infos  = [r for r in report if r["level"]=="INFO"]
        print(f"{'='*60}")
        print(f"Quality Report: {tex}")
        print(f"{'='*60}")
        if errors:
            print(f"\nERROR ({len(errors)}) — model should fix:")
            for i, r in enumerate(errors, 1):
                print(f"  {i}. [{r['check']}] {r['message']}")
        if warns:
            print(f"\nWARN ({len(warns)}) — model decides:")
            for i, r in enumerate(warns, 1):
                print(f"  {i}. [{r['check']}] {r['message']}")
        if infos:
            print(f"\nINFO ({len(infos)}):")
            for i, r in enumerate(infos, 1):
                print(f"  {i}. [{r['check']}] {r['message']}")
        print(f"\nTotal: {len(errors)} errors, {len(warns)} warnings, {len(infos)} info")
    # Output JSON for machine parsing
    print("\n--- JSON ---")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
