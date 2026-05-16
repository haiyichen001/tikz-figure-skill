#!/usr/bin/env python3
"""
TikZ pre-compile validator — 10 automated layout checks before pdflatex.
Usage: python tikz-validator.py <file.tex>

Checks: micro-slopes, direction reversal, container overflow, label collision,
arrow length, Bezier collision, label gaps, edge clipping, boundary clearance,
line crossings. Shared parser: tikz_parser.py.

Exit: 0=PASS, 1=WARN, 2=ERROR
"""

import re
import sys
from dataclasses import dataclass
from tikz_parser import (
    Node, Zone, Coord, parse_coords, parse_nodes, parse_zones
)


@dataclass
class Issue:
    level: str  # ERROR, WARN
    category: str
    line_no: int
    message: str


# ─── Bezier constants ───

BEND_ANGLE_TABLE = {
    20: 0.176, 25: 0.222, 30: 0.268, 35: 0.315,
    40: 0.364, 45: 0.414, 50: 0.466, 55: 0.521, 60: 0.577,
}

FONT_WIDTH_TABLE = {
    "tiny": 0.08, "scriptsize": 0.10, "footnotesize": 0.12,
    "small": 0.15, "normalsize": 0.18, "large": 0.22,
}

MIN_CLEARANCES = {
    "label_to_label": 0.3, "label_to_shape": 0.4,
    "label_to_arrow": 0.3, "node_edge_to_node_edge": 0.8,
    "any_to_canvas_edge": 0.5,
}


def parse_draw_coords(line: str) -> list[Coord]:
    return parse_coords(line)


# ─── Check 1: Micro-slopes ───

def check_micro_slopes(lines: list[str]) -> list[Issue]:
    issues = []
    TOLERANCE = 0.05
    scope_depth = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if '\\begin{scope}' in stripped:
            scope_depth += 1; continue
        if '\\end{scope}' in stripped:
            scope_depth = max(0, scope_depth - 1); continue
        if scope_depth > 0 or '\\draw' not in line or 'plot' in line:
            continue

        coords = parse_draw_coords(line)
        if len(coords) < 2:
            continue

        for j in range(len(coords) - 1):
            p1, p2 = coords[j], coords[j + 1]
            dx, dy = abs(p1.x - p2.x), abs(p1.y - p2.y)
            if dx > TOLERANCE and dy > TOLERANCE:
                if dx > 2.0 and dy > 2.0:
                    continue
                issues.append(Issue(
                    level="ERROR", category="micro-slope", line_no=i + 1,
                    message=f"Diagonal: ({p1.x},{p1.y})->({p2.x},{p2.y}) dx={dx:.2f} dy={dy:.2f}"
                ))
    return issues


# ─── Check 2: Direction reversal ───

def check_direction_reversal(lines: list[str]) -> list[Issue]:
    issues = []
    for i, line in enumerate(lines):
        if '\\draw' not in line:
            continue
        coords = parse_draw_coords(line)
        if len(coords) < 3:
            continue
        target = coords[-1]
        for j in range(1, len(coords) - 1):
            mid, prev = coords[j], coords[j - 1]
            if abs(mid.x - prev.x) < 0.05:
                if prev.y < target.y and mid.y > target.y + 0.1:
                    issues.append(Issue(level="ERROR", category="direction", line_no=i + 1,
                        message=f"Direction reversal: mid y={mid.y} beyond target y={target.y}"))
                if prev.y > target.y and mid.y < target.y - 0.1:
                    issues.append(Issue(level="ERROR", category="direction", line_no=i + 1,
                        message=f"Direction reversal: mid y={mid.y} beyond target y={target.y}"))
            if abs(mid.y - prev.y) < 0.05:
                if prev.x < target.x and mid.x > target.x + 0.1:
                    issues.append(Issue(level="ERROR", category="direction", line_no=i + 1,
                        message=f"Direction reversal: mid x={mid.x} beyond target x={target.x}"))
                if prev.x > target.x and mid.x < target.x - 0.1:
                    issues.append(Issue(level="ERROR", category="direction", line_no=i + 1,
                        message=f"Direction reversal: mid x={mid.x} beyond target x={target.x}"))
    return issues


# ─── Check 3: Container overflow ───

def check_container_overflow(nodes: list[Node], zones: list[Zone], diag: float = 30.0) -> list[Issue]:
    issues = []
    PAD = diag * 0.01  # 1% of diagonal
    for node in nodes:
        if not node.name:
            continue
        containing = None
        for zone in zones:
            if zone.x_min <= node.x <= zone.x_max and zone.y_min <= node.y <= zone.y_max:
                if containing is None or (zone.x_max - zone.x_min) < (containing.x_max - containing.x_min):
                    containing = zone
        if containing is None:
            continue
        hw, hh = node.width / 2, node.height / 2
        if node.x - hw < containing.x_min + PAD:
            issues.append(Issue(level="WARN", category="overflow", line_no=0,
                message=f"Overflow: '{node.name}' left {node.x-hw:.1f} beyond zone left {containing.x_min:.1f}"))
        if node.x + hw > containing.x_max - PAD:
            issues.append(Issue(level="WARN", category="overflow", line_no=0,
                message=f"Overflow: '{node.name}' right {node.x+hw:.1f} beyond zone right {containing.x_max:.1f}"))
        if node.y - hh < containing.y_min + PAD:
            issues.append(Issue(level="WARN", category="overflow", line_no=0,
                message=f"Overflow: '{node.name}' bottom {node.y-hh:.1f} beyond zone bottom {containing.y_min:.1f}"))
        if node.y + hh > containing.y_max - PAD:
            issues.append(Issue(level="WARN", category="overflow", line_no=0,
                message=f"Overflow: '{node.name}' top {node.y+hh:.1f} beyond zone top {containing.y_max:.1f}"))
    return issues


# ─── Check 4: Label collision ───

def check_label_collision(nodes: list[Node], diag: float = 30.0) -> list[Issue]:
    issues = []
    MIN_GAP = diag * 0.005  # 0.5% of diagonal
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1, n2 = nodes[i], nodes[j]
            if not n1.name or not n2.name:
                continue
            if abs(n1.x - n2.x) < 0.01 and abs(n1.y - n2.y) < 0.01:
                continue
            hw1, hh1 = n1.width / 2, n1.height / 2
            hw2, hh2 = n2.width / 2, n2.height / 2
            x_overlap = (n1.x - hw1 - MIN_GAP < n2.x + hw2 and n1.x + hw1 + MIN_GAP > n2.x - hw2)
            y_overlap = (n1.y - hh1 - MIN_GAP < n2.y + hh2 and n1.y + hh1 + MIN_GAP > n2.y - hh2)
            if x_overlap and y_overlap:
                dist_x = abs(n1.x - n2.x) - hw1 - hw2
                dist_y = abs(n1.y - n2.y) - hh1 - hh2
                issues.append(Issue(level="WARN", category="collision", line_no=0,
                    message=f"Collision: '{n1.name}' & '{n2.name}' gap x={dist_x:.2f} y={dist_y:.2f}cm"))
    return issues


# ─── Check 5: Arrow length ───

def check_short_arrows(lines: list[str], nodes: list[Node]) -> list[Issue]:
    issues = []
    MIN_GAP, MAX_GAP = 1.2, 4.0
    node_map = {n.name: n for n in nodes if n.name}
    scope_depth = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if '\\begin{scope}' in stripped:
            scope_depth += 1; continue
        if '\\end{scope}' in stripped:
            scope_depth = max(0, scope_depth - 1); continue
        if scope_depth > 0 or '\\draw' not in line:
            continue

        node_refs = re.findall(r'\(([a-zA-Z_][a-zA-Z0-9_]*?)(?:\.[a-zA-Z ]+)?\)', line)
        referenced = [name for name in node_refs if name in node_map]
        if len(referenced) < 2:
            continue
        src, dst = node_map[referenced[0]], node_map[referenced[-1]]
        gap_x = abs(src.x - dst.x) - src.width / 2 - dst.width / 2
        gap_y = abs(src.y - dst.y) - src.height / 2 - dst.height / 2
        min_gap = min(gap_x, gap_y) if gap_x > 0 and gap_y > 0 else max(gap_x, gap_y)

        if 0 < min_gap < MIN_GAP:
            issues.append(Issue(level="WARN", category="short-arrow", line_no=i + 1,
                message=f"Arrow too short: '{src.name}'->'{dst.name}' gap {min_gap:.2f}cm"))
        elif min_gap > MAX_GAP:
            issues.append(Issue(level="WARN", category="long-arrow", line_no=i + 1,
                message=f"Arrow too long: '{src.name}'->'{dst.name}' gap {min_gap:.2f}cm"))
    return issues


# ─── Check 6: Bezier collision ───

def bezier_max_depth(chord_cm, bend_angle):
    return (chord_cm / 2) * BEND_ANGLE_TABLE.get(bend_angle, 0.268)


def check_bezier_collisions(lines: list[str], nodes: list[Node]) -> list[Issue]:
    issues = []
    node_map = {n.name: n for n in nodes if n.name}
    bend_re = re.compile(r'bend\s+(left|right)\s*=\s*(\d+)')

    for i, line in enumerate(lines):
        if '\\draw' not in line:
            continue
        am = bend_re.search(line)
        if not am:
            continue
        direction, angle = am.group(1), int(am.group(2))

        refs = re.findall(r'\(([a-zA-Z_][a-zA-Z0-9_]*?)(?:\.[a-zA-Z ]+)?\)', line)
        endpoint_nodes = [name for name in refs if name in node_map]
        if len(endpoint_nodes) < 2:
            continue

        src, dst = node_map[endpoint_nodes[0]], node_map[endpoint_nodes[-1]]
        chord = ((src.x - dst.x)**2 + (src.y - dst.y)**2) ** 0.5
        safe_zone = bezier_max_depth(chord, angle) + MIN_CLEARANCES["label_to_arrow"]

        dx, dy = dst.x - src.x, dst.y - src.y
        nx, ny = (-dy, dx) if direction == "left" else (dy, -dx)
        nl = (nx**2 + ny**2) ** 0.5
        if nl < 0.01:
            continue
        nx, ny = nx / nl, ny / nl

        for node in nodes:
            if node in (src, dst):
                continue
            rx, ry = node.x - src.x, node.y - src.y
            proj_n = rx * nx + ry * ny
            proj_c = (rx * dx + ry * dy) / max(chord, 0.01)
            if 0 < proj_c < chord and abs(proj_n) < safe_zone:
                issues.append(Issue(level="WARN", category="bezier-collision", line_no=i + 1,
                    message=f"Bezier risk: '{node.name}' inside arc (dist {abs(proj_n):.2f}cm, need >={safe_zone:.2f}cm)"))
    return issues


# ─── Check 7: Label gaps ───

def estimate_label_width(text: str, font_size: str = "footnotesize") -> float:
    wpc = FONT_WIDTH_TABLE.get(font_size, 0.12)
    clean = re.sub(r'\\(?:text(?:bf|it|tt|sf)|textbf|textit|texttt|textsf|small|scriptsize|footnotesize|tiny|normalsize)\{', '', text)
    clean = re.sub(r'\\[a-zA-Z]+', '', clean)
    clean = re.sub(r'[{}$$]', '', clean)
    cc = max(len(clean.strip()), 1)
    mul = 1.0
    if 'bf' in text or 'textbf' in text:
        mul *= 1.10
    if 'tt' in text or 'texttt' in text:
        mul *= 1.15
    return cc * wpc * mul


def check_label_gaps(lines: list[str], nodes: list[Node]) -> list[Issue]:
    issues = []
    node_map = {n.name: n for n in nodes if n.name}
    for i, line in enumerate(lines):
        if '\\draw' not in line or 'node' not in line:
            continue
        refs = re.findall(r'\(([a-zA-Z_][a-zA-Z0-9_]*?)(?:\.[a-zA-Z ]+)?\)', line)
        referenced = [name for name in refs if name in node_map]
        if len(referenced) < 2:
            continue
        src, dst = node_map[referenced[0]], node_map[referenced[-1]]
        center_dist = ((src.x - dst.x)**2 + (src.y - dst.y)**2) ** 0.5
        usable = center_dist - src.width/2 - dst.width/2 - 0.6
        lm = re.search(r'node\s*\[[^\]]*\]\s*\{([^}]+)\}', line)
        if lm:
            ew = estimate_label_width(lm.group(1))
            if ew > usable > 0:
                issues.append(Issue(level="WARN", category="label-gap", line_no=i + 1,
                    message=f"Label too wide: \"{lm.group(1)[:20]}\" est {ew:.1f}cm > gap {usable:.1f}cm"))
    return issues


# ─── Check 8: Edge clipping ───

def check_edge_clipping(nodes: list[Node], zones: list[Zone], diag: float = 30.0) -> list[Issue]:
    issues = []
    M = diag * 0.02  # 2% of diagonal
    if zones:
        all_x = [z.x_min for z in zones] + [z.x_max for z in zones]
        all_y = [z.y_min for z in zones] + [z.y_max for z in zones]
        cx0, cx1 = min(all_x) - 1.0, max(all_x) + 1.0
        cy0, cy1 = min(all_y) - 1.0, max(all_y) + 1.0
    elif nodes:
        all_x = [n.x - n.width/2 for n in nodes] + [n.x + n.width/2 for n in nodes]
        all_y = [n.y - n.height/2 for n in nodes] + [n.y + n.height/2 for n in nodes]
        cx0, cx1 = min(all_x) - 1.0, max(all_x) + 1.0
        cy0, cy1 = min(all_y) - 1.0, max(all_y) + 1.0
    else:
        return issues

    for node in nodes:
        if not node.name:
            continue
        hw, hh = node.width / 2, node.height / 2
        l, r, b, t = node.x - hw, node.x + hw, node.y - hh, node.y + hh
        sides = [
            ("left", l - cx0, M), ("right", cx1 - r, M),
            ("bottom", b - cy0, M), ("top", cy1 - t, M),
        ]
        for side, gap, need in sides:
            if gap < need:
                issues.append(Issue(level="WARN", category="edge-clip", line_no=0,
                    message=f"Edge clip: '{node.name}' {side} gap {gap:.1f}cm < {need}cm"))
    return issues


# ─── Check 9: Boundary clearance ───

def check_boundary_clearance(nodes: list[Node], diag: float = 30.0) -> list[Issue]:
    issues = []
    C = diag * 0.01  # 1% of diagonal
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1, n2 = nodes[i], nodes[j]
            if not n1.name or not n2.name:
                continue
            gx = abs(n1.x - n2.x) - n1.width/2 - n2.width/2
            gy = abs(n1.y - n2.y) - n1.height/2 - n2.height/2
            if gx < C and gy < C and gx > -1 and gy > -1:
                if 0 < gx < C or 0 < gy < C:
                    issues.append(Issue(level="WARN", category="tight-clearance", line_no=0,
                        message=f"Tight: '{n1.name}' & '{n2.name}' gap x={gx:.2f} y={gy:.2f}cm"))
    return issues


# ─── Check 10: Line crossings ───

def segments_intersect(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
    def cross(ox, oy, ax, ay, bx, by):
        return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)
    d1 = cross(bx0, by0, bx1, by1, ax0, ay0)
    d2 = cross(bx0, by0, bx1, by1, ax1, ay1)
    d3 = cross(ax0, ay0, ax1, ay1, bx0, by0)
    d4 = cross(ax0, ay0, ax1, ay1, bx1, by1)
    return ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0))


def check_line_crossings(lines: list[str]) -> list[Issue]:
    """Detect line-line crossings that may need path routing."""
    issues = []
    segments = []
    scope_depth = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if '\\begin{scope}' in stripped:
            scope_depth += 1; continue
        if '\\end{scope}' in stripped:
            scope_depth = max(0, scope_depth - 1); continue
        if scope_depth > 0 or '\\draw' not in line:
            continue
        coords = parse_draw_coords(line)
        if len(coords) < 2:
            continue
        for j in range(len(coords) - 1):
            p1, p2 = coords[j], coords[j + 1]
            length = ((p2.x - p1.x)**2 + (p2.y - p1.y)**2) ** 0.5
            if length >= 0.5:  # skip very short segments (node borders)
                segments.append((i + 1, p1.x, p1.y, p2.x, p2.y))

    crossings = 0
    for a in range(len(segments)):
        for b in range(a + 1, len(segments)):
            s1, s2 = segments[a], segments[b]
            if segments_intersect(s1[1], s1[2], s1[3], s1[4], s2[1], s2[2], s2[3], s2[4]):
                crossings += 1

    if crossings > 0:
        issues.append(Issue(level="WARN", category="line-crossing", line_no=0,
            message=f"Line crossings: {crossings} detected — graphdrawing edge routing should handle these"))
    return issues


# ─── Check 11: Oversize nodes (box >> text content) ───

def check_oversize_nodes(nodes: list[Node]) -> list[Issue]:
    """Flag nodes where explicitly-set widths/heights are >1.8x estimated text size."""
    issues = []
    for node in nodes:
        if not node.name or len(node.name) < 2:
            continue
        # Skip anonymous text labels (long descriptive text)
        if len(node.name) > 30:
            continue
        # Skip default-dimension nodes (parser used 2.8/0.9 as fallback)
        if abs(node.width - 2.8) < 0.01 and abs(node.height - 0.9) < 0.01:
            continue

        text_chars = len(node.name)
        est_width = text_chars * 0.12 + 0.8   # chars * font + inner_sep
        est_height = 0.65                      # single line + padding

        if node.width > 1.5 and node.width > est_width * 3.0:  # 3x text width
            issues.append(Issue(level="WARN", category="oversize", line_no=0,
                message=f"Box too wide: '{node.name}' {node.width:.1f}cm for '{node.name}'"
                f" (est text ~{est_width:.1f}cm, ratio {node.width/est_width:.1f}x)"
                f" — drop minimum width or reduce to ~{est_width:.1f}cm"))
        if node.height > 1.0 and node.height > est_height * 3.0:  # 3x text height
            issues.append(Issue(level="WARN", category="oversize", line_no=0,
                message=f"Box too tall: '{node.name}' {node.height:.1f}cm"
                f" (est text ~{est_height:.1f}cm, ratio {node.height/est_height:.1f}x)"
                f" — drop minimum height"))
    return issues


# ─── Main ───

def compute_diag(nodes):
    """Calculate figure diagonal from node positions."""
    if not nodes: return 30.0  # default ~30cm diagonal
    xs = [n.x for n in nodes]
    ys = [n.y for n in nodes]
    w = max(xs) - min(xs) + 3 if xs else 20
    h = max(ys) - min(ys) + 3 if ys else 15
    return (w**2 + h**2) ** 0.5  # cm

def validate(filepath: str) -> list[Issue]:
    """Interference checks only — thresholds relative to figure diagonal."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")

    all_issues = []
    nodes = parse_nodes(lines)
    zones = parse_zones(lines)
    diag = compute_diag(nodes)  # cm
    # 1. Boxes touching/overlapping (relaxed: diag*0.5%)
    if len(nodes) >= 2:
        all_issues.extend(check_label_collision(nodes, diag))
    # 2. Node outside its zone background (padding: diag*1%)
    if zones:
        all_issues.extend(check_container_overflow(nodes, zones, diag))
    # 3. Node too close to canvas edge (margin: diag*2%)
    all_issues.extend(check_edge_clipping(nodes, zones, diag))
    # 4. Nodes too close (gap: diag*1%)
    all_issues.extend(check_boundary_clearance(nodes, diag))
    # 5. Box size >> text size (3x, already relative)
    all_issues.extend(check_oversize_nodes(nodes))
    return all_issues


def has_line_crossings(issues: list[Issue]) -> bool:
    """Check if any issues are line-crossing type (trigger path router)."""
    return any(i.category == "line-crossing" for i in issues)


def main():
    if len(sys.argv) < 2:
        print("Usage: python tikz-validator.py <file.tex>")
        sys.exit(1)

    filepath = sys.argv[1]
    issues = validate(filepath)

    if not issues:
        print("PASS — no issues found")
        sys.exit(0)

    errors = [i for i in issues if i.level == "ERROR"]
    warns = [i for i in issues if i.level == "WARN"]

    print(f"{'='*60}")
    print(f"TikZ Validator Report: {filepath}")
    print(f"{'='*60}")

    all_warns = errors + warns
    if all_warns:
        print(f"\nWARN ({len(all_warns)}) — model decides:")
        for i, issue in enumerate(all_warns, 1):
            loc = f"L{issue.line_no}" if issue.line_no else ""
            print(f"  {i}. [{issue.category}] {loc} {issue.message}")

    print(f"\nTotal: {len(all_warns)} warnings")

    sys.exit(1 if all_warns else 0)


if __name__ == "__main__":
    main()
