#!/usr/bin/env python3
"""CCTV 摄像机覆盖范围平面图生成工具"""

import argparse
import math
import sys

import ezdxf

from constants import SENSORS, DORI, PIXELS, DEFAULT_TILT, LAYER_COLORS

TRANSPARENCY = {
    "BLINDSPOT": 0x2000000 + 178,
    "DORI-I":    0x2000000 + 153,
    "DORI-R":    0x2000000 + 102,
    "DORI-O":    0x2000000 + 51,
    "DORI-D":    0x2000000 + 25,
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
    if args.focal not in [2.8, 4, 6, 8, 12]:
        print(f"焦距不支持: {args.focal}", file=sys.stderr); sys.exit(1)
    if args.sensor not in SENSORS:
        print(f"传感器不支持: {args.sensor}", file=sys.stderr); sys.exit(1)
    if args.height <= 0:
        print("安装高度必须为正数", file=sys.stderr); sys.exit(1)
    if args.tilt == "auto":
        args.tilt = DEFAULT_TILT.get(args.focal, 30)
    else:
        args.tilt = float(args.tilt)
    return args


def calculate(args):
    sensor = SENSORS[args.sensor]
    focal = args.focal
    h_pixels = PIXELS[args.pixels]
    h_fov = math.degrees(2 * math.atan(sensor["w"] / (2 * focal)))
    v_fov = math.degrees(2 * math.atan(sensor["h"] / (2 * focal)))
    dori = {}
    for level, info in DORI.items():
        dori[level] = (h_pixels * focal) / (sensor["w"] * info["px_per_m"])
    blind = args.height / math.tan(math.radians(args.tilt + v_fov / 2))
    return {"h_fov": h_fov, "v_fov": v_fov, "dori": dori, "blind": blind}


def print_dry_run(args, calc):
    print(f"焦距:{args.focal}mm 像素:{args.pixels} 传感器:{args.sensor}")
    print(f"高度:{args.height}m 俯角:{args.tilt}° 朝向:{args.direction}°")
    print(f"FOV:{calc['h_fov']:.1f}° 盲区:{calc['blind']:.2f}m")
    for l, d in calc["dori"].items():
        print(f"  {l}: {d:.1f}m")


def polar_xy(cx, cy, r, angle_deg):
    rad = math.radians(angle_deg)
    return (cx + r * math.cos(rad), cy + r * math.sin(rad))


def create_dxf(args, calc):
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.M
    msp = doc.modelspace()

    for name, color in LAYER_COLORS.items():
        doc.layers.add(name, color=color)

    cx, cy = 0, 0
    ca = args.direction + calc["h_fov"] / 2  # 整体旋转 FOV/2

    # 5 段线段沿中心线：原点 → I → R → O → D
    segments = [
        ("BLINDSPOT", 0, calc["blind"]),
        ("DORI-I",    calc["blind"], calc["dori"]["I"]),
        ("DORI-R",    calc["dori"]["I"], calc["dori"]["R"]),
        ("DORI-O",    calc["dori"]["R"], calc["dori"]["O"]),
        ("DORI-D",    calc["dori"]["O"], calc["dori"]["D"]),
    ]

    for layer, r_start, r_end in segments:
        p1 = polar_xy(cx, cy, r_start, ca)
        p2 = polar_xy(cx, cy, r_end, ca)
        msp.add_line(
            p1, p2,
            dxfattribs={"layer": layer, "transparency": TRANSPARENCY[layer]}
        )
        # 镜像线段（沿 X 轴翻转）
        msp.add_line(
            (p1[0], -p1[1]), (p2[0], -p2[1]),
            dxfattribs={"layer": layer, "transparency": TRANSPARENCY[layer]}
        )

    # 5 个同心圆：盲区 / I / R / O / D
    circle_radii = [
        ("BLINDSPOT", calc["blind"]),
        ("DORI-I",    calc["dori"]["I"]),
        ("DORI-R",    calc["dori"]["R"]),
        ("DORI-O",    calc["dori"]["O"]),
        ("DORI-D",    calc["dori"]["D"]),
    ]
    for layer, radius in circle_radii:
        msp.add_circle(
            (cx, cy), radius,
            dxfattribs={"layer": layer, "transparency": TRANSPARENCY[layer]}
        )

    return doc


def main():
    args = parse_args()
    args = validate_args(args)
    calc = calculate(args)
    if args.dry_run:
        print_dry_run(args, calc)
        return
    if not args.output:
        print("错误: 需要 --output", file=sys.stderr); sys.exit(1)
    doc = create_dxf(args, calc)
    doc.saveas(args.output)
    print(f"已生成: {args.output}")


if __name__ == "__main__":
    main()
