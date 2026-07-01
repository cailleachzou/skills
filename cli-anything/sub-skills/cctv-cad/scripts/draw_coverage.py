#!/usr/bin/env python3
"""CCTV 摄像机覆盖范围平面图生成工具"""

import argparse
import math
import sys

import ezdxf

from constants import SENSORS, DORI, PIXELS, DEFAULT_TILT, LAYER_COLORS, SCALE_INTERVAL


def parse_args():
    parser = argparse.ArgumentParser(
        description="生成摄像机覆盖范围 DXF 平面图",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--focal", type=float, default=4,
                        help="焦距 (mm): 2.8/4/6/8/12, 默认 4")
    parser.add_argument("--pixels", default="4mp", choices=["2mp", "4mp", "8mp"],
                        help="像素: 2mp/4mp/8mp, 默认 4mp")
    parser.add_argument("--sensor", default="1/2.8",
                        help="传感器尺寸, 默认 1/2.8")
    parser.add_argument("--height", type=float, default=3.0,
                        help="安装高度 (m), 默认 3.0")
    parser.add_argument("--tilt", default="auto",
                        help="俯角 (°), auto 按焦距推荐, 默认 auto")
    parser.add_argument("--direction", type=float, default=0,
                        help="摄像机朝向角度 (°), 0=右 90=上 180=左 270=下, 默认 0")
    parser.add_argument("--output", "-o",
                        help="输出 DXF 路径 (--dry-run 时可省略)")
    parser.add_argument("--dry-run", action="store_true",
                        help="显示计算参数但不生成文件")
    parser.add_argument("--no-dori", action="store_true",
                        help="去掉 DORI 分层")
    parser.add_argument("--no-blindspot", action="store_true",
                        help="去掉盲区标注")
    return parser.parse_args()


def validate_args(args):
    errors = []
    if args.focal not in [2.8, 4, 6, 8, 12]:
        errors.append(f"焦距不支持: {args.focal}, 支持: 2.8/4/6/8/12")
    if args.sensor not in SENSORS:
        errors.append(f"传感器不支持: {args.sensor}, 支持: {list(SENSORS.keys())}")
    if args.height <= 0:
        errors.append(f"安装高度必须为正数: {args.height}")
    if errors:
        print("参数错误:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    if args.tilt == "auto":
        args.tilt = DEFAULT_TILT.get(args.focal, 30)
    else:
        args.tilt = float(args.tilt)
    return args


def calculate(args):
    sensor = SENSORS[args.sensor]
    focal = args.focal
    h_pixels = PIXELS[args.pixels]
    height = args.height
    tilt = args.tilt
    h_fov = math.degrees(2 * math.atan(sensor["w"] / (2 * focal)))
    v_fov = math.degrees(2 * math.atan(sensor["h"] / (2 * focal)))
    dori_distances = {}
    for level, info in DORI.items():
        d = (h_pixels * focal) / (sensor["w"] * info["px_per_m"])
        dori_distances[level] = d
    blind_depth = height / math.tan(math.radians(tilt + v_fov / 2))
    return {
        "h_fov": h_fov,
        "v_fov": v_fov,
        "dori": dori_distances,
        "blind_depth": blind_depth,
    }


def print_dry_run(args, calc):
    print(f"焦距:     {args.focal} mm")
    print(f"像素:     {args.pixels} ({PIXELS[args.pixels]} px)")
    print(f"传感器:   {args.sensor} ({SENSORS[args.sensor]['w']}mm)")
    print(f"安装高度: {args.height} m")
    print(f"俯角:     {args.tilt}°")
    print(f"朝向:     {args.direction}°")
    print()
    print(f"水平 FOV: {calc['h_fov']:.1f}°")
    print(f"垂直 FOV: {calc['v_fov']:.1f}°")
    print(f"盲区深度: {calc['blind_depth']:.2f} m")
    print()
    print("DORI 距离:")
    for level, dist in calc["dori"].items():
        info = DORI[level]
        print(f"  {level} ({info['name']}): {dist:.1f} m")


def polar_to_cartesian(cx, cy, radius, angle_deg):
    angle_rad = math.radians(angle_deg)
    x = cx + radius * math.cos(angle_rad)
    y = cy + radius * math.sin(angle_rad)
    return x, y


def draw_dori_ring(msp, layer, cx, cy, inner_r, outer_r, start_angle, end_angle, segments=64):
    """绘制环形扇形区域（带填充）"""
    outer_points = []
    for i in range(segments + 1):
        angle = math.radians(start_angle + (end_angle - start_angle) * i / segments)
        x = cx + outer_r * math.cos(angle)
        y = cy + outer_r * math.sin(angle)
        outer_points.append((x, y))

    inner_points = []
    for i in range(segments, -1, -1):
        angle = math.radians(start_angle + (end_angle - start_angle) * i / segments)
        x = cx + inner_r * math.cos(angle)
        y = cy + inner_r * math.sin(angle)
        inner_points.append((x, y))

    all_points = outer_points + inner_points + [outer_points[0]]
    msp.add_lwpolyline(all_points, dxfattribs={"layer": layer})


def draw_sector(msp, layer, cx, cy, radius, start_angle, end_angle, segments=64):
    """绘制扇形区域（从圆心到半径）"""
    points = [(cx, cy)]
    for i in range(segments + 1):
        angle = math.radians(start_angle + (end_angle - start_angle) * i / segments)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))
    points.append((cx, cy))
    msp.add_lwpolyline(points, dxfattribs={"layer": layer})


def draw_dori_layers(msp, args, calc):
    """绘制 DORI 分层扇形"""
    cx, cy = 0, 0
    direction = args.direction
    h_fov = calc["h_fov"]
    start_angle = direction - h_fov / 2
    end_angle = direction + h_fov / 2

    levels = ["D", "O", "R", "I"]
    prev_radius = 0

    for level in levels:
        radius = calc["dori"][level]
        layer_name = f"DORI-{level}"

        if prev_radius > 0:
            draw_dori_ring(msp, layer_name, cx, cy, prev_radius, radius, start_angle, end_angle)
        else:
            draw_sector(msp, layer_name, cx, cy, radius, start_angle, end_angle)

        prev_radius = radius


def draw_fov_lines_segmented(msp, args, calc):
    """绘制 FOV 边界线，按 DORI 距离分段分图层"""
    cx, cy = 0, 0
    direction = args.direction
    h_fov = calc["h_fov"]
    start_angle = direction - h_fov / 2
    end_angle = direction + h_fov / 2

    levels = ["I", "R", "O", "D"]
    radii = [calc["dori"][l] for l in levels]

    prev_r = 0
    for level, r in zip(levels, radii):
        layer_name = f"DORI-{level}"
        x1, y1 = polar_to_cartesian(cx, cy, prev_r, start_angle)
        x2, y2 = polar_to_cartesian(cx, cy, r, start_angle)
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer_name})

        x3, y3 = polar_to_cartesian(cx, cy, prev_r, end_angle)
        x4, y4 = polar_to_cartesian(cx, cy, r, end_angle)
        msp.add_line((x3, y3), (x4, y4), dxfattribs={"layer": layer_name})

        prev_r = r


def draw_blindspot(msp, args, calc):
    """绘制盲区（三角形 + 弧线）"""
    if args.no_blindspot:
        return
    cx, cy = 0, 0
    direction = args.direction
    blind_depth = calc["blind_depth"]
    back_angle = direction + 180

    p1 = (cx, cy)
    p2 = polar_to_cartesian(cx, cy, blind_depth, back_angle - 15)
    p3 = polar_to_cartesian(cx, cy, blind_depth, back_angle + 15)
    msp.add_lwpolyline([p1, p2, p3, p1], dxfattribs={"layer": "BLINDSPOT"})

    arc_points = []
    segments = 32
    for i in range(segments + 1):
        angle = math.radians(back_angle - 15 + 30 * i / segments)
        x = cx + blind_depth * math.cos(angle)
        y = cy + blind_depth * math.sin(angle)
        arc_points.append((x, y))
    msp.add_lwpolyline(arc_points, dxfattribs={"layer": "BLINDSPOT"})


def draw_scale_marks(msp, args, calc):
    """绘制距离刻度"""
    cx, cy = 0, 0
    direction = args.direction
    max_dist = calc["dori"]["D"]
    for dist in range(SCALE_INTERVAL, int(max_dist) + 1, SCALE_INTERVAL):
        x, y = polar_to_cartesian(cx, cy, dist, direction)
        perp_angle = direction + 90
        tick_len = 0.15
        x1, y1 = polar_to_cartesian(x, y, tick_len, perp_angle)
        x2, y2 = polar_to_cartesian(x, y, tick_len, perp_angle + 180)
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "ANNOTATION"})
        text_x, text_y = polar_to_cartesian(x, y, 0.3, perp_angle)
        msp.add_text(
            f"{dist}m",
            dxfattribs={"layer": "ANNOTATION", "height": 0.25}
        ).set_placement((text_x, text_y))


def draw_camera_icon(msp, args):
    """绘制摄像机位置点和方向箭头"""
    cx, cy = 0, 0
    direction = args.direction
    msp.add_circle((cx, cy), radius=0.15, dxfattribs={"layer": "CAMERA"})
    arrow_len = 0.4
    x, y = polar_to_cartesian(cx, cy, arrow_len, direction)
    msp.add_line((cx, cy), (x, y), dxfattribs={"layer": "CAMERA"})


def create_dxf(args, calc):
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.M
    msp = doc.modelspace()
    for name, color in LAYER_COLORS.items():
        doc.layers.add(name, color=color)

    if not args.no_dori:
        draw_dori_layers(msp, args, calc)
    draw_fov_lines_segmented(msp, args, calc)
    draw_blindspot(msp, args, calc)
    draw_scale_marks(msp, args, calc)
    draw_camera_icon(msp, args)

    # 打包为块
    block_name = "CAMERA_COVERAGE"
    block = doc.blocks.new(name=block_name)

    # 先清空模型空间，收集实体引用
    entities_to_move = list(msp)
    for entity in entities_to_move:
        msp.delete_entity(entity)

    # 重新绘制到块中
    if not args.no_dori:
        draw_dori_layers(block, args, calc)
    draw_fov_lines_segmented(block, args, calc)
    draw_blindspot(block, args, calc)
    draw_scale_marks(block, args, calc)
    draw_camera_icon(block, args)

    msp.add_blockref(block_name, (0, 0))
    return doc


def main():
    args = parse_args()
    args = validate_args(args)
    calc = calculate(args)
    if args.dry_run:
        print_dry_run(args, calc)
        return
    if not args.output:
        print("错误: 生成文件需要指定 --output", file=sys.stderr)
        sys.exit(1)
    doc = create_dxf(args, calc)
    doc.saveas(args.output)
    print(f"已生成: {args.output}")


if __name__ == "__main__":
    main()
