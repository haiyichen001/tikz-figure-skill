#!/usr/bin/env python3
"""
Shared .tex parser for tikz-figure-skill tools.
Extracts nodes, zones, connections, and coordinates from TikZ source.

Used by: tikz-validator.py, tikz-path-router.py, pdf-overlap-checker.py
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Node:
    name: str
    x: float
    y: float
    width: float = 2.8
    height: float = 0.9
    text: str = ""

    @property
    def left(self):   return self.x - self.width / 2

    @property
    def right(self):  return self.x + self.width / 2

    @property
    def top(self):    return self.y + self.height / 2

    @property
    def bottom(self): return self.y - self.height / 2


@dataclass
class Coord:
    x: float
    y: float


@dataclass
class Zone:
    name: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float


# ─── Regex patterns ───

COORD_RE = re.compile(r'\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)')
NODE_RE = re.compile(
    r'\\node\s*\[([^\]]*)\]\s*'
    r'(?:\(([^)]*)\)\s*)?'
    r'at\s*\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)'
)
NODE_ALT_RE = re.compile(
    r'\\node\s*\(([^)]*)\)\s*'
    r'\[([^\]]*)\]\s*'
    r'at\s*\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)'
)
FILL_RECT_RE = re.compile(
    r'\\fill\s*\[([^\]]*)\]\s*'
    r'\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)\s*'
    r'rectangle\s*'
    r'\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)'
)
NODE_REF_RE = re.compile(r'\(([a-zA-Z_][a-zA-Z0-9_]*?)(?:\.([a-zA-Z ]+))?\)')


# ─── Parse functions ───

def parse_coords(line: str) -> list[Coord]:
    """Extract all explicit coordinate pairs from a line."""
    return [Coord(float(m.group(1)), float(m.group(2)))
            for m in COORD_RE.finditer(line)]


def parse_nodes(lines: list[str]) -> list[Node]:
    """Extract all named nodes with positions and dimensions."""
    nodes = []
    for line in lines:
        for pattern in [NODE_RE, NODE_ALT_RE]:
            for m in pattern.finditer(line):
                groups = m.groups()
                if pattern == NODE_RE:
                    opts, name, x, y = groups
                    name = name or ""
                else:
                    name, opts, x, y = groups
                if not name.strip():
                    continue

                width, height = 2.8, 0.9
                wm = re.search(r'minimum\s+width\s*=\s*(\d+\.?\d*)', opts)
                hm = re.search(r'minimum\s+height\s*=\s*(\d+\.?\d*)', opts)
                tw = re.search(r'text\s+width\s*=\s*(\d+\.?\d*)', opts)
                if wm:
                    width = float(wm.group(1))
                if tw:
                    width = max(width, float(tw.group(1)) + 0.5)
                if hm:
                    height = float(hm.group(1))

                nodes.append(Node(
                    name=name.strip(),
                    x=float(x), y=float(y),
                    width=width, height=height
                ))
    return nodes


def parse_zones(lines: list[str]) -> list[Zone]:
    """Extract zone/region rectangles from \\fill commands."""
    zones = []
    for line in lines:
        for m in FILL_RECT_RE.finditer(line):
            x1, y1 = float(m.group(2)), float(m.group(3))
            x2, y2 = float(m.group(4)), float(m.group(5))
            name = m.group(1)[:30] if m.group(1) else "unnamed"
            zones.append(Zone(
                name=name,
                x_min=min(x1, x2), y_min=min(y1, y2),
                x_max=max(x1, x2), y_max=max(y1, y2)
            ))
    return zones


def parse_connections(lines: list[str], node_names: set[str]) -> list[dict]:
    """Extract directed edges between known nodes."""
    connections = []
    for line in lines:
        if '\\draw' not in line:
            continue
        refs = NODE_REF_RE.findall(line)
        node_list = [(name, anchor if anchor else "center")
                     for name, anchor in refs if name in node_names]
        if len(node_list) < 2:
            continue

        from_name, from_anchor = node_list[0]
        to_name, to_anchor = node_list[-1]

        style = "arrow"
        if 'dashed' in line:
            style = "dashed"
        elif 'thick' in line:
            style = "thick"
        if 'rounded corners' in line:
            rc = re.search(r'rounded corners=(\d+\.?\d*)pt', line)
            if rc:
                style += f", rounded corners={rc.group(1)}pt"

        connections.append({
            "from": from_name, "from_anchor": from_anchor,
            "to": to_name, "to_anchor": to_anchor,
            "style": style, "label": ""
        })
    return connections


def parse_file(filepath: str) -> tuple[list[str], list[Node], list[Zone], list[dict]]:
    """Parse a .tex file — returns (lines, nodes, zones, connections)."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")
    nodes = parse_nodes(lines)
    zones = parse_zones(lines)
    connections = parse_connections(lines, {n.name for n in nodes})
    return lines, nodes, zones, connections
