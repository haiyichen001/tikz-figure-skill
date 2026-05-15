#!/usr/bin/env python3
r"""
TikZ 坐标验证器 — 编译前自动检测常见布局错误
用法: python3 tikz-validator.py <file.tex>

检测项:
  1. 微斜线: \draw 路径中相邻坐标点既不共享 x 也不共享 y
  2. 容器溢出: node 坐标超出其所属 zone/region 的边界
  3. 标签碰撞: 两个 node 的估算 bounding box 重叠
  4. 箭头方向反转: 路径中间点超越目标点导致方向反转

输出: 逐条报告问题，无问题则输出 PASS
退出码: 0=全部通过, 1=有警告, 2=有错误

注意: scope 内的绘图（嵌入可视化的曲线/柱状图/热力图）不做微斜线检测，
因为数据可视化中的斜线是正常的。
"""

import re
import sys
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Point:
    x: float
    y: float


@dataclass
class Node:
    name: str
    x: float
    y: float
    width: float = 2.8  # default minimum width in cm
    height: float = 0.9  # default minimum height in cm
    text: str = ""


@dataclass
class Zone:
    name: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float


@dataclass
class Issue:
    level: str  # ERROR, WARN
    category: str  # micro-slope, overflow, collision, direction
    line_no: int
    message: str


# ─── 坐标提取 ───

COORD_PATTERN = re.compile(r'\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)')
NODE_PATTERN = re.compile(
    r'\\node\s*\[([^\]]*)\]\s*'           # options
    r'(?:\(([^)]*)\)\s*)?'                  # optional name
    r'at\s*\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)'  # position
)
NODE_ALT_PATTERN = re.compile(
    r'\\node\s*\(([^)]*)\)\s*'             # name first
    r'\[([^\]]*)\]\s*'                      # options
    r'at\s*\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)'
)
DRAW_PATTERN = re.compile(r'\\draw\s*\[([^\]]*)\]')
FILL_RECT_PATTERN = re.compile(
    r'\\fill\s*\[([^\]]*)\]\s*'
    r'\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)\s*'
    r'rectangle\s*'
    r'\((-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\)'
)
ZONE_FIT_PATTERN = re.compile(
    r'\\node\s*\[([^\]]*fit[^\]]*)\]\s*\(([^)]*)\)'
)


def parse_draw_coords(line: str) -> list[Point]:
    """Extract all explicit coordinate points from a \\draw line."""
    return [Point(float(m.group(1)), float(m.group(2)))
            for m in COORD_PATTERN.finditer(line)]


def parse_nodes(lines: list[str]) -> list[Node]:
    """Extract all named nodes with positions."""
    nodes = []
    for line in lines:
        # Try both node syntax patterns
        for pattern in [NODE_PATTERN, NODE_ALT_PATTERN]:
            for m in pattern.finditer(line):
                groups = m.groups()
                if pattern == NODE_PATTERN:
                    opts, name, x, y = groups
                    name = name or ""
                else:
                    name, opts, x, y = groups
                    name = name or ""

                width = 2.8
                height = 0.9
                # Extract minimum width/height from options
                w_match = re.search(r'minimum\s+width\s*=\s*(\d+\.?\d*)', opts)
                h_match = re.search(r'minimum\s+height\s*=\s*(\d+\.?\d*)', opts)
                tw_match = re.search(r'text\s+width\s*=\s*(\d+\.?\d*)', opts)
                if w_match:
                    width = float(w_match.group(1))
                if tw_match:
                    width = max(width, float(tw_match.group(1)) + 0.5)
                if h_match:
                    height = float(h_match.group(1))

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
        for m in FILL_RECT_PATTERN.finditer(line):
            opts = m.group(1)
            x1, y1 = float(m.group(2)), float(m.group(3))
            x2, y2 = float(m.group(4)), float(m.group(5))
            # Zone name from comment or opts
            name = opts[:30] if opts else "unnamed"
            zones.append(Zone(
                name=name,
                x_min=min(x1, x2), y_min=min(y1, y2),
                x_max=max(x1, x2), y_max=max(y1, y2)
            ))
    return zones


# ─── 检测器 ───

def check_micro_slopes(lines: list[str]) -> list[Issue]:
    """Check for micro-slopes in \\draw paths.

    Skips lines inside \\begin{scope} blocks (embedded visualizations)
    and lines containing 'plot' (data curves).
    """
    issues = []
    TOLERANCE = 0.05  # 0.05cm tolerance for floating point
    scope_depth = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track scope nesting
        if '\\begin{scope}' in stripped or stripped.startswith('\\begin{scope'):
            scope_depth += 1
            continue
        if '\\end{scope}' in stripped:
            scope_depth = max(0, scope_depth - 1)
            continue

        # Skip lines inside scope (embedded visualizations use scope)
        if scope_depth > 0:
            continue

        if '\\draw' not in line:
            continue
        # Skip non-path draws (fills, nodes)
        if 'node' in line and '--' not in line:
            continue
        # Skip plot commands (intentional curves)
        if 'plot' in line:
            continue

        coords = parse_draw_coords(line)
        if len(coords) < 2:
            continue

        for j in range(len(coords) - 1):
            p1, p2 = coords[j], coords[j + 1]
            dx = abs(p1.x - p2.x)
            dy = abs(p1.y - p2.y)

            # Both x and y change = diagonal line
            if dx > TOLERANCE and dy > TOLERANCE:
                # Skip if it's likely intentional (large diagonal for contour/curve)
                if dx > 2.0 and dy > 2.0:
                    continue
                issues.append(Issue(
                    level="ERROR",
                    category="micro-slope",
                    line_no=i + 1,
                    message=f"微斜线: ({p1.x},{p1.y})→({p2.x},{p2.y}) "
                            f"dx={dx:.2f} dy={dy:.2f} 都变了，应共享 x 或 y"
                ))
    return issues


def check_direction_reversal(lines: list[str]) -> list[Issue]:
    """Check for arrow direction reversal due to midpoint overshooting target."""
    issues = []

    for i, line in enumerate(lines):
        if '\\draw' not in line or 'arrow' not in line.lower() and 'Stealth' not in line:
            continue

        coords = parse_draw_coords(line)
        if len(coords) < 3:
            continue

        # Check if any midpoint overshoots the final target
        target = coords[-1]
        for j in range(1, len(coords) - 1):
            mid = coords[j]
            prev = coords[j - 1]

            # Check y-direction reversal
            if abs(mid.x - prev.x) < 0.05:  # vertical segment
                # If going up (prev.y < target.y) but mid.y > target.y
                if prev.y < target.y and mid.y > target.y + 0.1:
                    issues.append(Issue(
                        level="ERROR",
                        category="direction",
                        line_no=i + 1,
                        message=f"方向反转: 中间点 y={mid.y} 超过目标 y={target.y}，"
                                f"箭头最后一段会朝下"
                    ))
                # If going down but mid.y < target.y
                if prev.y > target.y and mid.y < target.y - 0.1:
                    issues.append(Issue(
                        level="ERROR",
                        category="direction",
                        line_no=i + 1,
                        message=f"方向反转: 中间点 y={mid.y} 超过目标 y={target.y}，"
                                f"箭头最后一段会朝上"
                    ))

            # Check x-direction reversal
            if abs(mid.y - prev.y) < 0.05:  # horizontal segment
                if prev.x < target.x and mid.x > target.x + 0.1:
                    issues.append(Issue(
                        level="ERROR",
                        category="direction",
                        line_no=i + 1,
                        message=f"方向反转: 中间点 x={mid.x} 超过目标 x={target.x}，"
                                f"箭头最后一段会朝左"
                    ))
                if prev.x > target.x and mid.x < target.x - 0.1:
                    issues.append(Issue(
                        level="ERROR",
                        category="direction",
                        line_no=i + 1,
                        message=f"方向反转: 中间点 x={mid.x} 超过目标 x={target.x}，"
                                f"箭头最后一段会朝右"
                    ))
    return issues


def check_container_overflow(nodes: list[Node], zones: list[Zone]) -> list[Issue]:
    """Check if nodes are outside their containing zone."""
    issues = []
    PADDING = 0.3  # minimum padding in cm

    for node in nodes:
        if not node.name:
            continue
        # Find the smallest zone that should contain this node
        containing = None
        for zone in zones:
            if (zone.x_min <= node.x <= zone.x_max and
                    zone.y_min <= node.y <= zone.y_max):
                if containing is None or (
                    (zone.x_max - zone.x_min) < (containing.x_max - containing.x_min)
                ):
                    containing = zone

        if containing is None:
            continue

        # Check if node's bounding box exceeds zone with padding
        half_w = node.width / 2
        half_h = node.height / 2
        node_left = node.x - half_w
        node_right = node.x + half_w
        node_bottom = node.y - half_h
        node_top = node.y + half_h

        if node_left < containing.x_min + PADDING:
            issues.append(Issue(
                level="WARN",
                category="overflow",
                line_no=0,
                message=f"溢出: 节点 '{node.name}' 左边界 {node_left:.1f} "
                        f"超出 zone 左边界 {containing.x_min:.1f}"
            ))
        if node_right > containing.x_max - PADDING:
            issues.append(Issue(
                level="WARN",
                category="overflow",
                line_no=0,
                message=f"溢出: 节点 '{node.name}' 右边界 {node_right:.1f} "
                        f"超出 zone 右边界 {containing.x_max:.1f}"
            ))
        if node_bottom < containing.y_min + PADDING:
            issues.append(Issue(
                level="WARN",
                category="overflow",
                line_no=0,
                message=f"溢出: 节点 '{node.name}' 下边界 {node_bottom:.1f} "
                        f"超出 zone 下边界 {containing.y_min:.1f}"
            ))
        if node_top > containing.y_max - PADDING:
            issues.append(Issue(
                level="WARN",
                category="overflow",
                line_no=0,
                message=f"溢出: 节点 '{node.name}' 上边界 {node_top:.1f} "
                        f"超出 zone 上边界 {containing.y_max:.1f}"
            ))
    return issues


def check_short_arrows(lines: list[str], nodes: list[Node]) -> list[Issue]:
    """Check for arrows between nodes that are too close (arrow shaft invisible)."""
    issues = []
    MIN_EDGE_GAP = 1.2  # minimum gap between node edges in cm
    MAX_EDGE_GAP = 4.0  # maximum gap — longer means too much whitespace
    scope_depth = 0

    # Build node lookup by name
    node_map = {n.name: n for n in nodes if n.name}

    for i, line in enumerate(lines):
        stripped = line.strip()
        if '\\begin{scope}' in stripped:
            scope_depth += 1
            continue
        if '\\end{scope}' in stripped:
            scope_depth = max(0, scope_depth - 1)
            continue
        if scope_depth > 0:
            continue

        if '\\draw' not in line or 'arrow' not in line.lower() and 'Stealth' not in line:
            continue

        # Find node references like (nodename.east) or (nodename)
        node_refs = re.findall(r'\(([a-zA-Z_][a-zA-Z0-9_]*?)(?:\.[a-z ]+)?\)', line)
        # Filter to known nodes
        referenced = [name for name in node_refs if name in node_map]

        if len(referenced) >= 2:
            src = node_map[referenced[0]]
            dst = node_map[referenced[-1]]

            # Calculate edge-to-edge gap
            gap_x = abs(src.x - dst.x) - src.width / 2 - dst.width / 2
            gap_y = abs(src.y - dst.y) - src.height / 2 - dst.height / 2
            min_gap = min(gap_x, gap_y) if gap_x > 0 and gap_y > 0 else max(gap_x, gap_y)

            if 0 < min_gap < MIN_EDGE_GAP:
                issues.append(Issue(
                    level="WARN",
                    category="short-arrow",
                    line_no=i + 1,
                    message=f"箭头过短: '{src.name}'→'{dst.name}' "
                            f"边距仅 {min_gap:.2f}cm (建议 ≥{MIN_EDGE_GAP}cm)"
                ))
            elif min_gap > MAX_EDGE_GAP:
                issues.append(Issue(
                    level="WARN",
                    category="long-arrow",
                    line_no=i + 1,
                    message=f"箭头过长: '{src.name}'→'{dst.name}' "
                            f"边距 {min_gap:.2f}cm (建议 ≤{MAX_EDGE_GAP}cm，缩小间距)"
                ))
    return issues


# ─── 新增: Bezier 曲线碰撞检测 ───

BEND_ANGLE_TABLE = {
    20: 0.176, 25: 0.222, 30: 0.268, 35: 0.315,
    40: 0.364, 45: 0.414, 50: 0.466, 55: 0.521, 60: 0.577,
}


def bezier_max_depth(chord_length_cm: float, bend_angle: int) -> float:
    """Calculate max depth of a Bezier curve arc from its chord."""
    tan_half = BEND_ANGLE_TABLE.get(bend_angle, 0.268)
    return (chord_length_cm / 2) * tan_half


FONT_WIDTH_TABLE = {
    "tiny": 0.08, "scriptsize": 0.10, "footnotesize": 0.12,
    "small": 0.15, "normalsize": 0.18, "large": 0.22,
}

MIN_CLEARANCES = {
    "label_to_label": 0.3,
    "label_to_shape": 0.4,
    "label_to_arrow": 0.3,
    "node_edge_to_node_edge": 0.8,
    "any_to_canvas_edge": 0.5,
}


def estimate_label_width(text: str, font_size: str = "footnotesize") -> float:
    """Estimate rendered width of a label in cm."""
    w_per_char = FONT_WIDTH_TABLE.get(font_size, 0.12)
    # Strip LaTeX commands, count visible chars
    clean = re.sub(r'\\(?:text(?:bf|it|tt|sf)|textbf|textit|texttt|textsf|small|scriptsize|footnotesize|tiny|normalsize)\{', '', text)
    clean = re.sub(r'\\[a-zA-Z]+', '', clean)
    clean = re.sub(r'[{}$$]', '', clean)
    char_count = len(clean.strip())
    # Bold: +10%, monospace: +15%
    multiplier = 1.0
    if 'bf' in text or 'textbf' in text:
        multiplier *= 1.10
    if 'tt' in text or 'texttt' in text:
        multiplier *= 1.15
    return max(char_count * w_per_char * multiplier, 1.0)


def parse_bend_arrows(lines: list[str]) -> list[dict]:
    """Extract all bent arrows with endpoints and bend angle."""
    arrows = []
    # Pattern: \draw[... bend left=N ...] (A.anchor) ... (B.anchor)
    bend_pattern = re.compile(
        r'\\draw\s*\[([^\]]*)\]\s*'
        r'\(([^)]+)\)\s*'
        r'(?:--|to\[[^\]]*\])'
        r'\s*\(([^)]+)\)'
    )
    bend_angle_re = re.compile(r'bend\s+(left|right)\s*=\s*(\d+)')

    for i, line in enumerate(lines):
        if '\\draw' not in line:
            continue
        angle_match = bend_angle_re.search(line)
        if not angle_match:
            continue
        direction = angle_match.group(1)
        angle = int(angle_match.group(2))

        # Extract coordinates
        coords = parse_draw_coords(line)
        if len(coords) < 2:
            continue

        # Also try to match node references like (node.east)
        node_refs = re.findall(r'\(([a-zA-Z_][a-zA-Z0-9_]*?)(?:\.[a-zA-Z ]+)?\)', line)

        arrows.append({
            "line_no": i + 1,
            "direction": direction,
            "angle": angle,
            "start": coords[0],
            "end": coords[-1],
            "depth": None,  # filled later if coords are explicit
        })
    return arrows


def check_bezier_collisions(lines: list[str], nodes: list[Node]) -> list[Issue]:
    """Check if any labels sit within the arc of a Bezier curve arrow."""
    issues = []
    node_map = {n.name: n for n in nodes if n.name}
    bend_angle_re = re.compile(r'bend\s+(left|right)\s*=\s*(\d+)')

    for i, line in enumerate(lines):
        if '\\draw' not in line:
            continue
        angle_match = bend_angle_re.search(line)
        if not angle_match:
            continue

        direction = angle_match.group(1)
        angle = int(angle_match.group(2))

        # Find node references for endpoints
        node_refs = re.findall(r'\(([a-zA-Z_][a-zA-Z0-9_]*?)(?:\.[a-zA-Z ]+)?\)', line)
        endpoint_nodes = [name for name in node_refs if name in node_map]
        if len(endpoint_nodes) < 2:
            continue

        src = node_map[endpoint_nodes[0]]
        dst = node_map[endpoint_nodes[-1]]
        chord = ((src.x - dst.x)**2 + (src.y - dst.y)**2) ** 0.5
        max_depth = bezier_max_depth(chord, angle)
        safe_zone = max_depth + MIN_CLEARANCES["label_to_arrow"]

        # Check labels near this curve (within chord midpoint region)
        mid_x = (src.x + dst.x) / 2
        mid_y = (src.y + dst.y) / 2
        # Direction of bend relative to chord
        chord_dx = dst.x - src.x
        chord_dy = dst.y - src.y
        # Normal vector (perpendicular to chord, pointing to bend side)
        if direction == "left":
            normal_x = -chord_dy
            normal_y = chord_dx
        else:
            normal_x = chord_dy
            normal_y = -chord_dx
        norm_len = (normal_x**2 + normal_y**2) ** 0.5
        if norm_len < 0.01:
            continue
        normal_x /= norm_len
        normal_y /= norm_len

        # Check each node against the curve's safe zone
        for node in nodes:
            if node in (src, dst):
                continue
            # Project node onto chord direction
            node_rel_x = node.x - src.x
            node_rel_y = node.y - src.y
            # Project onto normal
            proj_normal = node_rel_x * normal_x + node_rel_y * normal_y
            # Project onto chord axis (how far along the chord)
            chord_axis_x = chord_dx / max(chord, 0.01)
            chord_axis_y = chord_dy / max(chord, 0.01)
            proj_chord = node_rel_x * chord_axis_x + node_rel_y * chord_axis_y

            if 0 < proj_chord < chord:
                if abs(proj_normal) < safe_zone:
                    issues.append(Issue(
                        level="WARN",
                        category="bezier-collision",
                        line_no=i + 1,
                        message=f"Bezier碰撞风险: 节点 '{node.name}' 在弯曲箭头弧线内 "
                                f"(距离弧线基线 {abs(proj_normal):.2f}cm, "
                                f"需要 ≥{safe_zone:.2f}cm, bend {direction}={angle}deg)"
                    ))

    return issues


def check_label_gaps(lines: list[str], nodes: list[Node]) -> list[Issue]:
    """Check if label text fits in the gap between connected nodes."""
    issues = []
    node_map = {n.name: n for n in nodes if n.name}

    for i, line in enumerate(lines):
        if '\\draw' not in line or 'arrow' not in line.lower() and 'Stealth' not in line:
            continue
        if 'node' not in line:
            continue

        # Find node references
        node_refs = re.findall(r'\(([a-zA-Z_][a-zA-Z0-9_]*?)(?:\.[a-zA-Z ]+)?\)', line)
        referenced = [name for name in node_refs if name in node_map]
        if len(referenced) < 2:
            continue

        src = node_map[referenced[0]]
        dst = node_map[referenced[-1]]

        # Calculate available gap
        center_dist = ((src.x - dst.x)**2 + (src.y - dst.y)**2) ** 0.5
        available_gap = center_dist - src.width/2 - dst.width/2
        usable_space = available_gap - 0.6  # 0.3cm padding each side

        # Extract label text
        label_match = re.search(r'node\s*\[[^\]]*\]\s*\{([^}]+)\}', line)
        if label_match:
            label_text = label_match.group(1)
            est_width = estimate_label_width(label_text)
            if est_width > usable_space and usable_space > 0:
                issues.append(Issue(
                    level="WARN",
                    category="label-gap",
                    line_no=i + 1,
                    message=f"标签超宽: \"{label_text[:20]}\" 估计 {est_width:.1f}cm > "
                            f"可用间隙 {usable_space:.1f}cm "
                            f"(建议移到上方/下方或缩短文字)"
                ))

    return issues


def check_edge_clipping(nodes: list[Node], zones: list[Zone]) -> list[Issue]:
    """Check if any element is within 0.5cm of the canvas edge."""
    issues = []
    MARGIN = MIN_CLEARANCES["any_to_canvas_edge"]

    # Determine canvas bounds from zones or node extremes
    if zones:
        all_x = [z.x_min for z in zones] + [z.x_max for z in zones]
        all_y = [z.y_min for z in zones] + [z.y_max for z in zones]
        canvas_x0 = min(all_x) - 1.0
        canvas_x1 = max(all_x) + 1.0
        canvas_y0 = min(all_y) - 1.0
        canvas_y1 = max(all_y) + 1.0
    elif nodes:
        all_x = [n.x - n.width/2 for n in nodes] + [n.x + n.width/2 for n in nodes]
        all_y = [n.y - n.height/2 for n in nodes] + [n.y + n.height/2 for n in nodes]
        canvas_x0 = min(all_x) - 1.0
        canvas_x1 = max(all_x) + 1.0
        canvas_y0 = min(all_y) - 1.0
        canvas_y1 = max(all_y) + 1.0
    else:
        return issues

    for node in nodes:
        if not node.name:
            continue
        half_w, half_h = node.width / 2, node.height / 2
        left = node.x - half_w
        right = node.x + half_w
        bottom = node.y - half_h
        top = node.y + half_h

        if left < canvas_x0 + MARGIN:
            issues.append(Issue(
                level="WARN", category="edge-clip",
                line_no=0,
                message=f"贴边风险: 节点 '{node.name}' 距左边界仅 {left - canvas_x0:.1f}cm (需 ≥{MARGIN}cm)"
            ))
        if right > canvas_x1 - MARGIN:
            issues.append(Issue(
                level="WARN", category="edge-clip",
                line_no=0,
                message=f"贴边风险: 节点 '{node.name}' 距右边界仅 {canvas_x1 - right:.1f}cm (需 ≥{MARGIN}cm)"
            ))
        if bottom < canvas_y0 + MARGIN:
            issues.append(Issue(
                level="WARN", category="edge-clip",
                line_no=0,
                message=f"贴边风险: 节点 '{node.name}' 距下边界仅 {bottom - canvas_y0:.1f}cm (需 ≥{MARGIN}cm)"
            ))
        if top > canvas_y1 - MARGIN:
            issues.append(Issue(
                level="WARN", category="edge-clip",
                line_no=0,
                message=f"贴边风险: 节点 '{node.name}' 距上边界仅 {canvas_y1 - top:.1f}cm (需 ≥{MARGIN}cm)"
            ))

    return issues


def check_boundary_clearance(nodes: list[Node]) -> list[Issue]:
    """Check 0.4cm clearance between labels and other nodes' boundaries."""
    issues = []
    CLEARANCE = MIN_CLEARANCES["label_to_shape"]

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1, n2 = nodes[i], nodes[j]
            if not n1.name or not n2.name:
                continue

            # Edge-to-edge gap
            gap_x = abs(n1.x - n2.x) - n1.width/2 - n2.width/2
            gap_y = abs(n1.y - n2.y) - n1.height/2 - n2.height/2

            if gap_x < CLEARANCE and gap_y < CLEARANCE and gap_x > -1 and gap_y > -1:
                if 0 < gap_x < CLEARANCE or 0 < gap_y < CLEARANCE:
                    issues.append(Issue(
                        level="WARN", category="tight-clearance",
                        line_no=0,
                        message=f"间距不足: '{n1.name}' 与 '{n2.name}' "
                                f"间距 x={gap_x:.2f}cm y={gap_y:.2f}cm (需 ≥{CLEARANCE}cm)"
                    ))

    return issues


def check_label_collision(nodes: list[Node]) -> list[Issue]:
    """Check for overlapping node bounding boxes."""
    issues = []
    MIN_GAP = 0.15  # minimum gap between nodes in cm

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1, n2 = nodes[i], nodes[j]
            # Skip unnamed nodes
            if not n1.name or not n2.name:
                continue
            # Skip if same position (likely overlaid intentionally)
            if abs(n1.x - n2.x) < 0.01 and abs(n1.y - n2.y) < 0.01:
                continue

            # Calculate bounding boxes
            hw1, hh1 = n1.width / 2, n1.height / 2
            hw2, hh2 = n2.width / 2, n2.height / 2

            # Check overlap
            x_overlap = (n1.x - hw1 - MIN_GAP < n2.x + hw2 and
                         n1.x + hw1 + MIN_GAP > n2.x - hw2)
            y_overlap = (n1.y - hh1 - MIN_GAP < n2.y + hh2 and
                         n1.y + hh1 + MIN_GAP > n2.y - hh2)

            if x_overlap and y_overlap:
                dist_x = abs(n1.x - n2.x) - hw1 - hw2
                dist_y = abs(n1.y - n2.y) - hh1 - hh2
                issues.append(Issue(
                    level="WARN",
                    category="collision",
                    line_no=0,
                    message=f"碰撞: '{n1.name}' 和 '{n2.name}' "
                            f"间距 x={dist_x:.2f}cm y={dist_y:.2f}cm "
                            f"(需要 ≥{MIN_GAP}cm)"
                ))
    return issues


# ─── 主逻辑 ───

def validate(filepath: str) -> list[Issue]:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')

    all_issues: list[Issue] = []

    # 1. Micro-slope detection
    all_issues.extend(check_micro_slopes(lines))

    # 2. Direction reversal detection
    all_issues.extend(check_direction_reversal(lines))

    # 3. Parse structures for overflow and collision checks
    nodes = parse_nodes(lines)
    zones = parse_zones(lines)

    # 4. Container overflow
    if zones:
        all_issues.extend(check_container_overflow(nodes, zones))

    # 5. Label collision
    if len(nodes) >= 2:
        all_issues.extend(check_label_collision(nodes))

    # 6. Short arrows (nodes too close for visible arrow shaft)
    all_issues.extend(check_short_arrows(lines, nodes))

    # 7. Bezier curve collision (labels in arc of bent arrows)
    all_issues.extend(check_bezier_collisions(lines, nodes))

    # 8. Label gap calculation (text width vs available space between nodes)
    all_issues.extend(check_label_gaps(lines, nodes))

    # 9. Edge clipping (elements within 0.5cm of canvas edge)
    all_issues.extend(check_edge_clipping(nodes, zones))

    # 10. Boundary clearance (0.4cm between label and shape boundary)
    all_issues.extend(check_boundary_clearance(nodes))

    return all_issues


def main():
    if len(sys.argv) < 2:
        print("用法: python3 tikz-validator.py <file.tex>")
        sys.exit(1)

    filepath = sys.argv[1]
    issues = validate(filepath)

    if not issues:
        print("✅ PASS — 未发现坐标问题")
        sys.exit(0)

    errors = [i for i in issues if i.level == "ERROR"]
    warns = [i for i in issues if i.level == "WARN"]

    print(f"{'='*60}")
    print(f"TikZ 坐标验证报告: {filepath}")
    print(f"{'='*60}")

    if errors:
        print(f"\n🔴 错误 ({len(errors)} 个) — 必须修复:")
        for i, issue in enumerate(errors, 1):
            loc = f"L{issue.line_no}" if issue.line_no else ""
            print(f"  {i}. [{issue.category}] {loc} {issue.message}")

    if warns:
        print(f"\n🟡 警告 ({len(warns)} 个) — 建议修复:")
        for i, issue in enumerate(warns, 1):
            loc = f"L{issue.line_no}" if issue.line_no else ""
            print(f"  {i}. [{issue.category}] {loc} {issue.message}")

    print(f"\n{'='*60}")
    print(f"总计: {len(errors)} 错误, {len(warns)} 警告")

    sys.exit(2 if errors else 1)


if __name__ == "__main__":
    main()
