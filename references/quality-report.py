#!/usr/bin/env python3
"""
Quality Report — all thresholds relative to image diagonal.
Usage: python quality-report.py output.tex [output.pdf]
"""

import sys, re, json, math

def parse_dimensions(tex_path, pdf_path=None):
    w_pt, h_pt = 0, 0
    if pdf_path:
        try:
            import fitz
            doc = fitz.open(pdf_path)
            page = doc[0]
            w_pt, h_pt = page.rect.width, page.rect.height
            doc.close()
            return w_pt, h_pt
        except: pass
    try:
        with open(tex_path, encoding='utf-8') as f:
            tex = f.read()
        ys = [float(m.group(2)) for m in re.finditer(r'at\s*\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)', tex)]
        xs = [float(m.group(1)) for m in re.finditer(r'at\s*\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)', tex)]
        if xs and ys:
            w_pt = ((max(xs) - min(xs)) * 1.3 + 3) * 28.35
            h_pt = ((max(ys) - min(ys)) * 1.3 + 3) * 28.35
    except: pass
    return w_pt, h_pt

def findings(tex_path, pdf_path=None):
    results = []
    w_pt, h_pt = parse_dimensions(tex_path, pdf_path)
    diag = math.sqrt(w_pt**2 + h_pt**2) if w_pt > 0 else 0

    # 1. Aspect ratio: >4:1 or <1:4 triggers warn
    if w_pt > 0 and h_pt > 0:
        ratio = max(w_pt/h_pt, h_pt/w_pt)
        if ratio > 4:
            results.append({"level":"WARN","check":"aspect-ratio",
                "message":f"Aspect ratio {w_pt/h_pt:.1f}:1 — extreme. Check paper column fit.",
                "data":{"ratio":round(w_pt/h_pt,1)}})

    # 2. Content density: flag if <1.5% of canvas area
    if pdf_path and diag > 0:
        try:
            import fitz
            doc = fitz.open(pdf_path)
            page = doc[0]
            total = w_pt * h_pt
            content_area = 0
            for d in page.get_drawings():
                r = d["rect"]
                content_area += (r.x1-r.x0)*(r.y1-r.y0)
            for t in page.get_text("blocks"):
                content_area += (t[2]-t[0])*(t[3]-t[1])
            density = content_area/total*100 if total > 0 else 0
            if density < 1.5:
                results.append({"level":"WARN","check":"content-density",
                    "message":f"Content only {density:.1f}% of canvas — very sparse.",
                    "data":{"density_pct":round(density,1)}})
            doc.close()
        except: pass

    # 3. Orphan nodes
    try:
        with open(tex_path, encoding='utf-8') as f:
            tex = f.read()
        nodes = set(re.findall(r'\\node\[[^\]]*\]\s*\((\w+)\)', tex))
        edges_from = set(re.findall(r'\((\w+)\)\s*[-|]', tex))
        edges_to = set(re.findall(r'[-|]\s*\((\w+)\)', tex))
        edges_from |= set(re.findall(r'\((\w+)\.(?:east|west|north|south)\)', tex))
        connected = edges_from | edges_to
        orphans = nodes - connected - {'title','subtitle','legend','input','output','probs'}
        if orphans:
            results.append({"level":"WARN","check":"orphan-nodes",
                "message":f"Nodes with no edges: {', '.join(sorted(orphans))}."})
    except: pass

    # 4. Balance: >50% skew triggers warn
    try:
        xs = [float(m.group(1)) for m in re.finditer(r'at\s*\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)', tex)]
        if xs:
            mid = (min(xs)+max(xs))/2
            left = sum(1 for x in xs if x < mid)
            right = sum(1 for x in xs if x > mid)
            skew = abs(left-right)/max(len(xs),1)*100
            if skew > 50:
                results.append({"level":"WARN","check":"layout-balance",
                    "message":f"Balance skewed {skew:.0f}% ({left}L/{right}R)."})
    except: pass

    # 5. Font scaling: relative to single-column paper width
    if w_pt > 0:
        single = 252  # pt
        scale = single/w_pt if w_pt > single else 1.0
        tiny = 5 * scale
        if tiny < 4:
            results.append({"level":"WARN","check":"font-scaling",
                "message":f"Scaled to single column, tiny text → {tiny:.1f}pt (<4pt unreadable)."})

    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python quality-report.py output.tex [output.pdf]")
        sys.exit(1)
    tex = sys.argv[1]
    pdf = sys.argv[2] if len(sys.argv) > 2 else None
    report = findings(tex, pdf)
    if not report:
        print("PASS")
    else:
        print(f"{'='*60}")
        print(f"Quality Report ({len(report)} warnings)")
        print(f"{'='*60}")
        for i, r in enumerate(report, 1):
            print(f"  {i}. [{r['check']}] {r['message']}")
        print(f"\nAll WARN. Model decides.")
    print("--- JSON ---")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
