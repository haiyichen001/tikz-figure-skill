#!/usr/bin/env python3
"""
TikZ Path Router — automatic obstacle-avoiding orthogonal path routing.
Accepts .tex files directly (no manual JSON needed).

Usage:
  python tikz-path-router.py <routing-spec.json>          # manual JSON mode
  python tikz-path-router.py --from-tex <file.tex>         # auto-parse .tex
  python tikz-path-router.py --from-tex <file.tex> --auto-fix  # in-place fix
"""

import json
import re
import sys
import math

try:
    from pathfinding.core.grid import Grid
    from pathfinding.finder.a_star import AStarFinder
except ImportError:
    print("ERROR: pathfinding not installed. Run: pip install pathfinding")
    sys.exit(1)

from tikz_parser import parse_nodes as parse_nodes_from_tex, parse_connections as parse_connections_from_tex


# ─── Data structures ───

class Node:
    def __init__(self, name, x, y, width, height):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def left(self):  return self.x - self.width / 2

    @property
    def right(self): return self.x + self.width / 2

    @property
    def top(self):   return self.y + self.height / 2

    @property
    def bottom(self): return self.y - self.height / 2

    def anchor_pos(self, anchor):
        anchors = {
            "north": (self.x, self.top), "south": (self.x, self.bottom),
            "east": (self.right, self.y), "west": (self.left, self.y),
            "north east": (self.right, self.top), "north west": (self.left, self.top),
            "south east": (self.right, self.bottom), "south west": (self.left, self.bottom),
            "center": (self.x, self.y),
        }
        return anchors.get(anchor, (self.x, self.y))


class Connection:
    def __init__(self, from_node, from_anchor, to_node, to_anchor, style="arrow", label=""):
        self.from_node = from_node
        self.from_anchor = from_anchor
        self.to_node = to_node
        self.to_anchor = to_anchor
        self.style = style
        self.label = label


# ─── Grid ───

def build_grid(nodes, resolution, padding=1.0):
    all_left = min(n.left for n in nodes) - padding
    all_right = max(n.right for n in nodes) + padding
    all_bottom = min(n.bottom for n in nodes) - padding
    all_top = max(n.top for n in nodes) + padding
    cols = int(math.ceil((all_right - all_left) / resolution)) + 1
    rows = int(math.ceil((all_top - all_bottom) / resolution)) + 1
    if cols * rows > 500000:
        area = (all_right - all_left) * (all_top - all_bottom)
        resolution = math.sqrt(area / 250000)
        cols = int(math.ceil((all_right - all_left) / resolution)) + 1
        rows = int(math.ceil((all_top - all_bottom) / resolution)) + 1
    matrix = [[1] * cols for _ in range(rows)]
    buffer = 0.8
    for node in nodes:
        c_min = max(0, int((node.left - buffer - all_left) / resolution))
        c_max = min(cols - 1, int((node.right + buffer - all_left) / resolution))
        r_min = max(0, int((node.bottom - buffer - all_bottom) / resolution))
        r_max = min(rows - 1, int((node.top + buffer - all_bottom) / resolution))
        for r in range(r_min, r_max + 1):
            for c in range(c_min, c_max + 1):
                gr = rows - 1 - r
                if 0 <= gr < rows:
                    matrix[gr][c] = 0
    return matrix, all_left, all_bottom, resolution, rows, cols


def tikz_to_grid(x, y, ox, oy, res, rows):
    return int(round((x - ox) / res)), rows - 1 - int(round((y - oy) / res))


def grid_to_tikz(col, row, ox, oy, res, rows):
    return ox + col * res, oy + (rows - 1 - row) * res


# ─── Path simplification ───

def simplify_path(points):
    if len(points) <= 2:
        return points
    simplified = [points[0]]
    for i in range(1, len(points) - 1):
        p, c, n = simplified[-1], points[i], points[i + 1]
        dx1, dy1 = c[0] - p[0], c[1] - p[1]
        dx2, dy2 = n[0] - c[0], n[1] - c[1]
        s1 = ((dx1 > 0) - (dx1 < 0), (dy1 > 0) - (dy1 < 0))
        s2 = ((dx2 > 0) - (dx2 < 0), (dy2 > 0) - (dy2 < 0))
        if s1 != s2:
            simplified.append(c)
    simplified.append(points[-1])
    return simplified


def snap_to_orthogonal(points):
    if len(points) <= 1:
        return points
    snapped = [points[0]]
    for i in range(1, len(points)):
        p, c = snapped[-1], points[i]
        if abs(c[0] - p[0]) < 0.05:
            snapped.append((p[0], c[1]))
        elif abs(c[1] - p[1]) < 0.05:
            snapped.append((c[0], p[1]))
        else:
            snapped.append((c[0], p[1]))
            snapped.append(c)
    return snapped


# ─── Routing ───

def route_connection(conn, nodes, matrix, ox, oy, res, rows, cols):
    sx, sy = conn.from_node.anchor_pos(conn.from_anchor)
    ex, ey = conn.to_node.anchor_pos(conn.to_anchor)
    sc, sr = tikz_to_grid(sx, sy, ox, oy, res, rows)
    ec, er = tikz_to_grid(ex, ey, ox, oy, res, rows)
    sc = max(0, min(cols - 1, sc)); sr = max(0, min(rows - 1, sr))
    ec = max(0, min(cols - 1, ec)); er = max(0, min(rows - 1, er))
    grid = Grid(matrix=matrix)
    sn = grid.node(sc, sr); en = grid.node(ec, er)
    sn.walkable = True; en.walkable = True
    finder = AStarFinder()
    path, _ = finder.find_path(sn, en, grid)
    if not path:
        return [(sx, sy), (ex, sy), (ex, ey)]
    tikz_path = [(round(ox + c * res, 2), round(oy + (rows - 1 - r) * res, 2)) for c, r in path]
    tikz_path = snap_to_orthogonal(simplify_path(tikz_path))
    if tikz_path:
        tikz_path[0] = (round(sx, 2), round(sy, 2))
        tikz_path[-1] = (round(ex, 2), round(ey, 2))
    return tikz_path


def path_to_tikz(conn, path_points):
    if not path_points:
        return f"% ERROR: no path for {conn.from_node.name} -> {conn.to_node.name}"
    coords = " -- ".join(f"({x:.2f},{y:.2f})" for x, y in path_points)
    lbl = f" node[midway, above, font=\\scriptsize] {{{conn.label}}}" if conn.label else ""
    return f"\\draw[{conn.style}, rounded corners=6pt] {coords}{lbl};"


# ─── Core ───

def route_spec(nodes_dicts, connections_dicts, resolution=0.15):
    node_map = {}
    nodes = []
    for n in nodes_dicts:
        # Supports both dict and tikz_parser.Node objects
        if isinstance(n, dict):
            node = Node(n.name, n["x"], n["y"], n["width"], n["height"])
        else:
            node = Node(n.name, n.x, n.y, n.width, n.height)
        node_map[node.name] = node
        nodes.append(node)
    connections = []
    for c in connections_dicts:
        connections.append(Connection(
            from_node=node_map[c["from"]],
            from_anchor=c.get("from_anchor", "south"),
            to_node=node_map[c["to"]],
            to_anchor=c.get("to_anchor", "north"),
            style=c.get("style", "arrow"),
            label=c.get("label", ""),
        ))
    matrix, ox, oy, res, rows, cols = build_grid(nodes, resolution)
    results = []
    for conn in connections:
        path = route_connection(conn, nodes, matrix, ox, oy, res, rows, cols)
        results.append((conn, path_to_tikz(conn, path)))
    return results, (cols, rows, res)


def route_from_tex(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")
    nodes = parse_nodes_from_tex(lines)
    node_names = {n.name for n in nodes}
    connections = parse_connections_from_tex(lines, node_names)
    if not nodes:
        return "% No named nodes found"
    if not connections:
        return "% No node-to-node connections found"
    results, (cols, rows, res) = route_spec(nodes, connections)
    out = [f"% Auto-routed: {len(nodes)} nodes, {len(connections)} edges, grid {cols}x{rows}@{res:.2f}cm", ""]
    for conn, tikz_code in results:
        out.append(f"% {conn.from_node.name}.{conn.from_anchor} -> {conn.to_node.name}.{conn.to_anchor}")
        out.append(tikz_code)
        out.append("")
    return "\n".join(out)


# ─── Main ───

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python tikz-path-router.py <routing-spec.json>")
        print("  python tikz-path-router.py --from-tex <file.tex>")
        print("  python tikz-path-router.py --from-tex <file.tex> --auto-fix")
        sys.exit(1)

    if sys.argv[1] == "--from-tex":
        if len(sys.argv) < 3:
            print("ERROR: --from-tex requires a .tex file path")
            sys.exit(1)
        output = route_from_tex(sys.argv[2])
        print(output)
        if "--auto-fix" in sys.argv:
            with open(sys.argv[2], "r", encoding="utf-8") as f:
                original = f.read()
            lines = original.split("\n")
            nodes = parse_nodes_from_tex(lines)
            node_names = {n.name for n in nodes}
            new_lines = []
            for line in lines:
                if '\\draw' in line:
                    refs = re.findall(r'\(([a-zA-Z_][a-zA-Z0-9_]*?)(?:\.([a-zA-Z ]+))?\)', line)
                    node_refs = [name for name, _ in refs if name in node_names]
                    if len(node_refs) >= 2:
                        new_lines.append(f"% [auto-fix] original: {line.strip()}")
                        continue
                new_lines.append(line)
            new_lines.append("")
            new_lines.append("% === Auto-routed connections ===")
            for line in output.split("\n"):
                if line.strip() and not line.startswith("%"):
                    new_lines.append(line)
            with open(sys.argv[2], "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))
            print(f"% Wrote auto-fix to: {sys.argv[2]}")

    elif sys.argv[1] == "-":
        spec = json.load(sys.stdin)
        results, _ = route_spec(spec["nodes"], spec["connections"],
                                spec.get("grid_resolution", 0.15))
        for conn, tikz_code in results:
            print(f"% {conn.from_node.name} -> {conn.to_node.name}")
            print(tikz_code)
            print()
    else:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            spec = json.load(f)
        results, _ = route_spec(spec["nodes"], spec["connections"],
                                spec.get("grid_resolution", 0.15))
        for conn, tikz_code in results:
            print(f"% {conn.from_node.name} -> {conn.to_node.name}")
            print(tikz_code)
            print()


if __name__ == "__main__":
    main()
