#!/usr/bin/env python3
"""DXF 视觉复查工具 — 渲染、验证、多模态对比"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加父目录到路径以导入 mimo
sys.path.insert(0, str(Path(__file__).parent.parent / "mimo.disabled"))

try:
    import ezdxf
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf import bbox
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False
    print("Warning: ezdxf/matplotlib not installed. Install with: pip install ezdxf matplotlib")


def render_dxf(dxf_path, output_path=None, dpi=150, size=10):
    """渲染 DXF 为 PNG"""
    if not HAS_EZDXF:
        print("Error: ezdxf not installed")
        return None
    
    dxf_path = Path(dxf_path)
    if output_path is None:
        output_path = dxf_path.parent / f"{dxf_path.stem}_review.png"
    
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    
    fig, ax = plt.subplots(figsize=(size, size))
    ax.set_aspect('equal')
    ax.set_facecolor('white')
    
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(msp)
    
    ax.autoscale()
    ax.margins(0.1)
    plt.savefig(str(output_path), dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Rendered: {output_path}")
    return output_path


def validate_dxf(dxf_path, spec_path=None):
    """验证 DXF 文件"""
    if not HAS_EZDXF:
        print("Error: ezdxf not installed")
        return None
    
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    
    # 实体统计
    entities = list(msp)
    circles = list(msp.query('CIRCLE'))
    lines = list(msp.query('LINE'))
    arcs = list(msp.query('ARC'))
    polylines = list(msp.query('LWPOLYLINE'))
    
    # 图层统计
    layers = [l.dxf.name for l in doc.layers if not l.is_frozen()]
    
    # 边界框
    cache = bbox.Cache()
    extents = bbox.extents(msp, cache=cache)
    
    report = {
        "file": str(dxf_path),
        "timestamp": datetime.now().isoformat(),
        "entities": {
            "total": len(entities),
            "circles": len(circles),
            "lines": len(lines),
            "arcs": len(arcs),
            "polylines": len(polylines)
        },
        "layers": layers,
        "extents": {
            "min": list(extents.extmin) if extents.has_data else None,
            "max": list(extents.extmax) if extents.has_data else None,
            "size": [extents.size.x, extents.size.y] if extents.has_data else None
        }
    }
    
    # 加载规格文件
    if spec_path and Path(spec_path).exists():
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec = json.load(f)
        report["spec"] = spec
        
        # 验证实体数量
        if "expected_entities" in spec:
            expected = spec["expected_entities"]
            actual = report["entities"]["total"]
            report["validation"] = {
                "entity_count": {
                    "expected": expected,
                    "actual": actual,
                    "pass": abs(expected - actual) <= 5  # 允许5个误差
                }
            }
    
    print(f"Validation: {json.dumps(report, indent=2, ensure_ascii=False)}")
    return report


def compare_with_reference(dxf_path, reference_path, prompt=None):
    """多模态对比 DXF 与参考图"""
    # 先渲染 DXF
    rendered_path = render_dxf(dxf_path)
    if not rendered_path:
        return None
    
    # 尝试调用 mimo 进行多模态分析
    try:
        from mimo_multimodal import MimoMultimodal
        
        mimo = MimoMultimodal()
        if prompt is None:
            prompt = "对比这两个图，找出差异：左边是原始参考图，右边是生成的CAD图。列出所有不同之处。"
        
        result = mimo.compare_images(str(reference_path), str(rendered_path), prompt)
        print(f"Comparison: {result}")
        return result
    except ImportError:
        print("Warning: mimo not available. Manual comparison required.")
        print(f"  - Reference: {reference_path}")
        print(f"  - Rendered: {rendered_path}")
        return {"reference": str(reference_path), "rendered": str(rendered_path)}


def read_image(image_path, prompt="请描述这张图片的内容"):
    """多模态读取图片"""
    try:
        from mimo_multimodal import MimoMultimodal
        
        mimo = MimoMultimodal()
        result = mimo.analyze_image(str(image_path), prompt)
        print(f"Analysis: {result}")
        return result
    except ImportError:
        print("Error: mimo not available. Install mimo skill.")
        return None


def full_review(dxf_path, reference_path=None, spec_path=None):
    """完整复查流程"""
    print("=" * 60)
    print("DXF 视觉复查报告")
    print("=" * 60)
    
    # 1. 渲染
    print("\n1. 渲染预览...")
    rendered = render_dxf(dxf_path)
    
    # 2. 验证
    print("\n2. 自动验证...")
    validation = validate_dxf(dxf_path, spec_path)
    
    # 3. 多模态对比
    comparison = None
    if reference_path:
        print("\n3. 多模态对比...")
        comparison = compare_with_reference(dxf_path, reference_path)
    
    # 4. 生成报告
    report = {
        "file": str(dxf_path),
        "rendered": str(rendered) if rendered else None,
        "validation": validation,
        "comparison": comparison,
        "timestamp": datetime.now().isoformat()
    }
    
    # 保存报告
    report_path = Path(dxf_path).parent / f"{Path(dxf_path).stem}_review.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nReport saved: {report_path}")
    print("=" * 60)
    
    return report


def main():
    parser = argparse.ArgumentParser(description="DXF 视觉复查工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # render 命令
    render_parser = subparsers.add_parser("render", help="渲染 DXF 为 PNG")
    render_parser.add_argument("input", help="输入 DXF 文件")
    render_parser.add_argument("--output", "-o", help="输出 PNG 路径")
    render_parser.add_argument("--dpi", type=int, default=150, help="分辨率")
    render_parser.add_argument("--size", type=float, default=10, help="图形尺寸（英寸）")
    
    # validate 命令
    validate_parser = subparsers.add_parser("validate", help="验证 DXF 文件")
    validate_parser.add_argument("input", help="输入 DXF 文件")
    validate_parser.add_argument("--spec", help="规格文件（JSON）")
    
    # compare 命令
    compare_parser = subparsers.add_parser("compare", help="多模态对比")
    compare_parser.add_argument("input", help="输入 DXF 文件")
    compare_parser.add_argument("reference", help="参考图片")
    compare_parser.add_argument("--prompt", help="对比提示词")
    
    # read-image 命令
    read_parser = subparsers.add_parser("read-image", help="多模态读取图片")
    read_parser.add_argument("input", help="图片文件")
    read_parser.add_argument("--prompt", default="请描述这张图片的内容", help="提示词")
    
    # full 命令
    full_parser = subparsers.add_parser("full", help="完整复查流程")
    full_parser.add_argument("input", help="输入 DXF 文件")
    full_parser.add_argument("--reference", help="参考图片")
    full_parser.add_argument("--spec", help="规格文件（JSON）")
    
    args = parser.parse_args()
    
    if args.command == "render":
        render_dxf(args.input, args.output, args.dpi, args.size)
    elif args.command == "validate":
        validate_dxf(args.input, args.spec)
    elif args.command == "compare":
        compare_with_reference(args.input, args.reference, args.prompt)
    elif args.command == "read-image":
        read_image(args.input, args.prompt)
    elif args.command == "full":
        full_review(args.input, args.reference, args.spec)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
