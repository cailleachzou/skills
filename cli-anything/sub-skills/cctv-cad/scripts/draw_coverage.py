#!/usr/bin/env python3
"""CCTV 摄像机覆盖范围平面图生成工具"""

import argparse
import math
import sys

import ezdxf

from constants import SENSORS, DORI, PIXELS, DEFAULT_TILT, LAYER_COLORS

# 透明度：DXF 编码 = 0x2000000 + alpha
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


def arc_point(cx, cy, r, angle_deg):
    rad = math.radians(angle_deg)
    return (cx + r * math.cos(rad), cy + r * math.sin(rad))


def bulge_for_arc(start_angle, end_angle):
    """计算 LWPOLYLINE bulge 值（弧段）"""
    delta = end_angle - start_angle
    return math.tan(math.radians(delta) / 4)


def create_dxf(args, calc):
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.M
    msp = doc.modelspace()

    for name, color in LAYER_COLORS.items():
        doc.layers.add(name, color=color)

    cx, cy = 0, 0
    ca = args.direction  # 中心角
    hf = calc["h_fov"] / 2  # 半 FOV
    blind_r = calc["blind"]

    # 角度边界
    a_top = ca + hf
    a_bot = ca - hf

    # 盲区 M：三角形（原点 → 弧两端）
    p_origin = (cx, cy)
    p_top = arc_point(cx, cy, blind_r, a_top)
    p_bot = arc_point(cx, cy, blind_r, a_bot)
    msp.add_lwpolyline(
        [p_origin, p_top, p_bot],
        dxfattribs={"layer": "BLINDSPOT", "transparency": TRANSPARENCY["BLINDSPOT"]}
    )

    # DORI 梯形：每层是 4 个点 + 弧形边
    prev_r = blind_r
    for level in ["D", "O", "R", "I"]:
        r = calc["dori"][level]
        layer = f"DORI-{level}"

        # 4 个顶点：外弧两端 + 内弧两端
        outer_top = arc_point(cx, cy, r, a_top)
        outer_bot = arc_point(cx, cy, r, a_bot)
        inner_top = arc_point(cx, cy, prev_r, a_top)
        inner_bot = arc_point(cx, cy, prev_r, a_bot)

        # 用 bulge 画弧形边
        # 顺序：外弧上 → 内弧上 → 内弧下 → 外弧下
        # 外弧边（上到下）：bulge > 0 逆时针
        # 内弧边（下到上）：bulge > 0 逆时针
        # 侧边（直线）：bulge = 0

        half_arc = hf  # 弧的半角
        bulge_val = bulge_for_arc(0, calc["h_fov"])  # 弧段 bulge

        points = [
            (outer_top[0], outer_top[1], 0),      # 外弧上端
            (outer_bot[0], outer_bot[1], -bulge_val),  # 外弧下端（顺时针弧）
            (inner_bot[0], inner_bot[1], 0),       # 内弧下端
            (inner_top[0], inner_top[1], bulge_val),   # 内弧上端（逆时针弧）
        ]

        msp.add_lwpolyline(
            points,
            dxfattribs={"layer": layer, "transparency": TRANSPARENCY[layer]}
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
        print("错误: 需要 --output", file=sys.stderr); sys.exit(1)
    doc = create_dxf(args, calc)
    doc.saveas(args.output)
    print(f"已生成: {args.output}")


if __name__ == "__main__":
    main()
