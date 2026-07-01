#!/usr/bin/env python3
"""CCTV 摄像机覆盖范围平面图生成工具"""

import argparse
import math
import sys

import ezdxf

from constants import SENSORS, DORI, PIXELS, DEFAULT_TILT, LAYER_COLORS


# 透明度：DXF 编码 = 0x2000000 + alpha (alpha 0=透明 255=不透明)
TRANSPARENCY = {
    "BLINDSPOT": 0x2000000 + 178,  # ~30% 透明
    "DORI-I":    0x2000000 + 153,  # ~40% 透明
    "DORI-R":    0x2000000 + 102,  # ~60% 透明
    "DORI-O":    0x2000000 + 51,   # ~80% 透明
    "DORI-D":    0x2000000 + 25,   # ~90% 透明
}


def parse_args():
    parser = argparse.ArgumentParser(description="生成摄像机覆盖范围 DXF 平面图")
    parser.add_argument("--focal", type=float, default=4)
    parser.add_argument("--pixels", default="4mp", choices=["2mp", "4mp", "8mp"])
    parser.add_argument("--sensor", default="1/2.8")
    parser.add_argument("--height", type=float, default=3.0)
    parser.add_argument("--tilt", default="auto")
    parser.add_argument("--direction", type=float, default=0)
    parser.add_argument("--output", "-o")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def validate_args(args):
    errors = []
    if args.focal not in [2.8, 4, 6, 8, 12]:
        errors.append(f"焦距不支持: {args.focal}")
    if args.sensor not in SENSORS:
        errors.append(f"传感器不支持: {args.sensor}")
    if args.height <= 0:
        errors.append(f"安装高度必须为正数")
    if errors:
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
    return {"h_fov": h_fov, "v_fov": v_fov, "dori": dori_distances, "blind_depth": blind_depth}


def print_dry_run(args, calc):
    print(f"焦距: {args.focal} mm | 像素: {args.pixels} | 传感器: {args.sensor}")
    print(f"高度: {args.height} m | 俯角: {args.tilt}° | 朝向: {args.direction}°")
    print(f"FOV: {calc['h_fov']:.1f}° | 盲区: {calc['blind_depth']:.2f} m")
    for level, dist in calc["dori"].items():
        print(f"  {level}: {dist:.1f} m")


def get_arc_endpoints(cx, cy, radius, center_angle, half_fov):
    a1 = math.radians(center_angle + half_fov)
    a2 = math.radians(center_angle - half_fov)
    return (cx + radius * math.cos(a1), cy + radius * math.sin(a1)), \
           (cx + radius * math.cos(a2), cy + radius * math.sin(a2))


def create_dxf(args, calc):
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.M
    msp = doc.modelspace()

    for name, color in LAYER_COLORS.items():
        doc.layers.add(name, color=color)

    cx, cy = 0, 0
    center_angle = args.direction
    half_fov = calc["h_fov"] / 2
    blind_r = calc["blind_depth"]

    # 盲区 M 三角形
    (x1, y1), (x2, y2) = get_arc_endpoints(cx, cy, blind_r, center_angle, half_fov)
    msp.add_lwpolyline(
        [(cx, cy), (x1, y1), (x2, y2)],
        dxfattribs={"layer": "BLINDSPOT", "transparency": TRANSPARENCY["BLINDSPOT"]}
    )

    # DORI 梯形：D → O → R → I
    prev_r = blind_r
    for level in ["D", "O", "R", "I"]:
        r = calc["dori"][level]
        (ix1, iy1), (ix2, iy2) = get_arc_endpoints(cx, cy, prev_r, center_angle, half_fov)
        (ox1, oy1), (ox2, oy2) = get_arc_endpoints(cx, cy, r, center_angle, half_fov)
        msp.add_lwpolyline(
            [(ox1, oy1), (ix1, iy1), (ix2, iy2), (ox2, oy2)],
            dxfattribs={"layer": f"DORI-{level}", "transparency": TRANSPARENCY[f"DORI-{level}"]}
        )
        prev_r = r

    return doc


def main():
    args = parse_args()
    args = validate_args(args)
    calc = calculate(args)
    if args.dry_run:
        print_dry_run(args, calc)
        return
    if not args.output:
        print("错误: 需要 --output", file=sys.stderr)
        sys.exit(1)
    doc = create_dxf(args, calc)
    doc.saveas(args.output)
    print(f"已生成: {args.output}")


if __name__ == "__main__":
    main()
