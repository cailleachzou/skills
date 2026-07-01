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
    parser.add_argument("--focal", type=float, default=4)
    parser.add_argument("--pixels", default="4mp", choices=["2mp", "4mp", "8mp"])
    parser.add_argument("--sensor", default="1/2.8")
    parser.add_argument("--height", type=float, default=3.0)
    parser.add_argument("--tilt", default="auto")
    parser.add_argument("--direction", type=float, default=0)
    parser.add_argument("--output", "-o")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-dori", action="store_true")
    parser.add_argument("--no-blindspot", action="store_true")
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
    return cx + radius * math.cos(angle_rad), cy + radius * math.sin(angle_deg if False else angle_rad)


def get_arc_endpoints(cx, cy, radius, center_angle, half_fov):
    """获取弧的两个端点坐标"""
    a1 = math.radians(center_angle + half_fov)
    a2 = math.radians(center_angle - half_fov)
    return (cx + radius * math.cos(a1), cy + radius * math.sin(a1)), \
           (cx + radius * math.cos(a2), cy + radius * math.sin(a2))


def draw_trapezoid(msp, layer, cx, cy, inner_r, outer_r, center_angle, half_fov):
    """绘制梯形区域：内弧两端点 → 外弧两端点"""
    (ix1, iy1), (ix2, iy2) = get_arc_endpoints(cx, cy, inner_r, center_angle, half_fov)
    (ox1, oy1), (ox2, oy2) = get_arc_endpoints(cx, cy, outer_r, center_angle, half_fov)
    msp.add_lwpolyline(
        [(ox1, oy1), (ix1, iy1), (ix2, iy2), (ox2, oy2), (ox1, oy1)],
        dxfattribs={"layer": layer}
    )


def draw_triangle(msp, layer, cx, cy, radius, center_angle, half_fov):
    """绘制三角形：原点 → 内弧两端点"""
    (x1, y1), (x2, y2) = get_arc_endpoints(cx, cy, radius, center_angle, half_fov)
    msp.add_lwpolyline(
        [(cx, cy), (x1, y1), (x2, y2), (cx, cy)],
        dxfattribs={"layer": layer}
    )


def draw_dori_layers(msp, args, calc):
    """绘制覆盖扇形：原点 → 盲区M → D → O → R → I"""
    cx, cy = 0, 0
    center_angle = args.direction
    half_fov = calc["h_fov"] / 2

    # 盲区 M：三角形
    if not args.no_blindspot:
        draw_triangle(msp, "BLINDSPOT", cx, cy, calc["blind_depth"], center_angle, half_fov)

    # DORI 层：从近到远 D → O → R → I
    prev_r = calc["blind_depth"]
    for level in ["D", "O", "R", "I"]:
        r = calc["dori"][level]
        draw_trapezoid(msp, f"DORI-{level}", cx, cy, prev_r, r, center_angle, half_fov)
        prev_r = r


def draw_fov_lines_segmented(msp, args, calc):
    """绘制 FOV 边界线，从盲区边界开始按 DORI 分段"""
    cx, cy = 0, 0
    center_angle = args.direction
    half_fov = calc["h_fov"] / 2

    a1 = math.radians(center_angle + half_fov)
    a2 = math.radians(center_angle - half_fov)

    prev_r = calc["blind_depth"]
    for level in ["D", "O", "R", "I"]:
        r = calc["dori"][level]
        layer = f"DORI-{level}"
        msp.add_line(
            (cx + prev_r * math.cos(a1), cy + prev_r * math.sin(a1)),
            (cx + r * math.cos(a1), cy + r * math.sin(a1)),
            dxfattribs={"layer": layer}
        )
        msp.add_line(
            (cx + prev_r * math.cos(a2), cy + prev_r * math.sin(a2)),
            (cx + r * math.cos(a2), cy + r * math.sin(a2)),
            dxfattribs={"layer": layer}
        )
        prev_r = r


def draw_scale_marks(msp, args, calc):
    """绘制距离刻度"""
    cx, cy = 0, 0
    center_angle = args.direction
    max_dist = calc["dori"]["D"]
    for dist in range(SCALE_INTERVAL, int(max_dist) + 1, SCALE_INTERVAL):
        x, y = polar_to_cartesian(cx, cy, dist, center_angle)
        perp = center_angle + 90
        t = 0.15
        x1, y1 = polar_to_cartesian(x, y, t, perp)
        x2, y2 = polar_to_cartesian(x, y, t, perp + 180)
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "ANNOTATION"})
        tx, ty = polar_to_cartesian(x, y, 0.3, perp)
        msp.add_text(
            f"{dist}m",
            dxfattribs={"layer": "ANNOTATION", "height": 0.25}
        ).set_placement((tx, ty))


def draw_camera_icon(msp, args):
    """绘制摄像机位置点和方向箭头"""
    cx, cy = 0, 0
    msp.add_circle((cx, cy), radius=0.15, dxfattribs={"layer": "CAMERA"})
    x, y = polar_to_cartesian(cx, cy, 0.4, args.direction)
    msp.add_line((cx, cy), (x, y), dxfattribs={"layer": "CAMERA"})


def create_dxf(args, calc):
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.M
    msp = doc.modelspace()
    for name, color in LAYER_COLORS.items():
        doc.layers.add(name, color=color)

    # 先画到模型空间
    if not args.no_dori:
        draw_dori_layers(msp, args, calc)
    draw_fov_lines_segmented(msp, args, calc)
    draw_scale_marks(msp, args, calc)
    draw_camera_icon(msp, args)

    # 打包为块
    block_name = "CAMERA_COVERAGE"
    block = doc.blocks.new(name=block_name)
    for entity in list(msp):
        msp.delete_entity(entity)

    if not args.no_dori:
        draw_dori_layers(block, args, calc)
    draw_fov_lines_segmented(block, args, calc)
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
