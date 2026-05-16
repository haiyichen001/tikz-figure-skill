#!/usr/bin/env python3
"""
Unified Quality Inspector — one script, 15 checks, all WARN, model decides.
Usage: python inspect.py output.tex [output.pdf]
"""

import sys, os, subprocess, re, json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_sensor(script, *args):
    """Run a sensor script, capture its JSON output."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, script)] + list(args),
                          capture_output=True, text=True, timeout=60)
        # Extract JSON block from output
        out = r.stdout + r.stderr
        m = re.search(r'--- JSON ---\s*\n(.*)', out, re.DOTALL)
        if m: return json.loads(m.group(1))
        # Fallback: parse warning counts
        warns = re.findall(r'(\d+) warnings?', out)
        if warns: return [{"level":"WARN","check":script,"message":f"{warns[-1]} findings"}]
        return []
    except Exception as e:
        return [{"level":"WARN","check":script,"message":str(e)}]

def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect.py output.tex [output.pdf]")
        sys.exit(1)

    tex = sys.argv[1]
    pdf = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"{'='*60}")
    print(f"Quality Inspection: {tex}")
    print(f"{'='*60}")

    # 1. Pre-compile: interference checks
    print("\n--- Sensor 1: tikz-validator (interference) ---")
    r1 = run_sensor("tikz-validator.py", tex)

    # 2. Post-compile: PDF overlap
    if pdf:
        print("\n--- Sensor 2: pdf-overlap-checker (PDF) ---")
        r2 = run_sensor("pdf-overlap-checker.py", pdf)
    else:
        r2 = []
        print("  (no PDF — skip)")

    # 3. Quality: aspect, density, balance, orphans, font
    print("\n--- Sensor 3: quality-report (layout) ---")
    r3 = run_sensor("quality-report.py", tex, pdf) if pdf else run_sensor("quality-report.py", tex)

    all_warns = r1 + r2 + r3

    # Unified report
    print(f"\n{'='*60}")
    print(f"UNIFIED REPORT: {len(all_warns)} warnings total")
    print(f"{'='*60}")
    for i, w in enumerate(all_warns, 1):
        check = w.get("check","?")
        msg = w.get("message","")
        print(f"  {i}. [{check}] {msg}")

    print(f"\nAll findings are WARN. Model decides what to fix.")
    print(f"--- JSON ---")
    print(json.dumps(all_warns, indent=2))

if __name__ == "__main__":
    main()
