#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
DWG 操作 CLI —— 转换 / 提取 / 回填（dwg skill 入口）

基于 ODA File Converter + ezdxf，无 AutoCAD、无 MIMO 依赖。

子命令：
  check                环境自检（ezdxf / ODA 可执行）
  convert <file>       转换 DWG<->DXF（按扩展名自动判断方向）
                       输出: 同目录下 <stem>.<另一格式>（ODA 要求输入/输出为独立目录）
  extract <dxf>        提取图纸文字 → JSON 清单（原文|类型|空间|图层|坐标|高度|旋转）
  apply <dxf> <json>   按 {原文:译文} 回填译文 → 输出 _ZH.dxf
  convert-back <dxf>   翻译后 DXF → DWG（_ZH.dwg）

用法示例：
  py dwg.py check
  py dwg.py convert in.dwg            # in.dwg -> in.dxf
  py dwg.py convert in.dxf            # in.dxf -> in.dwg
  py dwg.py extract in.dxf            # -> dwg_extract_<时间>/texts.json
  py dwg.py apply in.dxf texts_zh.json   # -> in_ZH.dxf
  py dwg.py convert-back in_ZH.dxf    # -> in_ZH.dwg

依赖：
  - Python 3 + ezdxf（py -3 -m pip install ezdxf）
  - ODA File Converter（默认 C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe）
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
ODA_CANDIDATES = [
    r"C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe",
    r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
    r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe",
]
ACAD_VERSION = "ACAD2018"  # 目标版本，ODA 支持 ACAD2018/2013/2010/2007/2004...

TEXT_TYPES = ("TEXT", "MTEXT", "ATTDEF", "ATTRIB")


def find_oda() -> Path | None:
    for c in ODA_CANDIDATES:
        p = Path(c)
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------------------
# ODA 转换
# ---------------------------------------------------------------------------

def oda_convert_one(src: Path, out_dir: Path, out_ext: str) -> Path:
    """用 ODA File Converter 转换单个文件。src 和 out_dir 必须不同目录。"""
    exe = find_oda()
    if exe is None:
        raise RuntimeError("未找到 ODA File Converter，请先安装或修改 ODA_CANDIDATES")

    in_dir = src.parent
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [str(exe), str(in_dir), str(out_dir), ACAD_VERSION,
           "DWG" if out_ext.lower() == "dwg" else "DXF", "0", "1"]
    print("运行:", " ".join(cmd), flush=True)
    # ODA 是 GUI 程序，无参数会挂起；带参数时会同步执行
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode not in (0, None):
        print("stderr:", proc.stderr[:500], file=sys.stderr)

    # 等待产物
    out_name = src.stem + "." + out_ext.lower()
    out_file = out_dir / out_name
    deadline = time.time() + 60
    while time.time() < deadline:
        if out_file.exists() and out_file.stat().st_size > 0:
            break
        time.sleep(1)

    if not out_file.exists() or out_file.stat().st_size == 0:
        err = out_dir / (out_name + ".err")
        detail = err.read_text(encoding="utf-8", errors="replace") if err.exists() else "无错误日志"
        raise RuntimeError(f"ODA 转换失败: {out_name}\n{detail}")

    # 有 .err 但仍有产物时给出警告
    err = out_dir / (out_name + ".err")
    if err.exists():
        print("⚠ ODA 警告:", err.read_text(encoding="utf-8", errors="replace").strip(), file=sys.stderr)
    return out_file


# ---------------------------------------------------------------------------
# 提取文字
# ---------------------------------------------------------------------------

def extract_texts(dxf_path: Path) -> list[dict]:
    import ezdxf
    doc = ezdxf.readfile(str(dxf_path))
    rows: list[dict] = []

    def add(entity, space: str):
        t = entity.dxftype()
        if t not in TEXT_TYPES:
            return
        try:
            if t == "MTEXT":
                text = entity.text
            else:
                text = entity.dxf.text
            if not text or not str(text).strip():
                return
            layer = entity.dxf.layer
            try:
                ins = entity.dxf.insert
                x, y, z = float(ins.x), float(ins.y), float(ins.z)
            except Exception:
                x = y = z = 0.0
            try:
                height = float(entity.dxf.height)
            except Exception:
                height = 0.0
            try:
                rot = float(entity.dxf.rotation)
            except Exception:
                rot = 0.0
            rows.append({
                "text": str(text),
                "type": t,
                "space": space,
                "layer": layer,
                "x": round(x, 4), "y": round(y, 4), "z": round(z, 4),
                "height": round(height, 4), "rotation": round(rot, 4),
            })
        except Exception:
            pass

    # 模型空间 + 所有布局
    for space_name, space in [("MODEL", doc.modelspace())] + \
                             [(ls.dxf.name, ls) for ls in doc.layouts if ls.dxf.name != "Model"]:
        for e in space:
            add(e, space_name)
            # INSERT 嵌套 ATTRIB
            if e.dxftype() == "INSERT":
                try:
                    for attrib in e.attribs:
                        add(attrib, space_name + "/ATTRIB")
                except Exception:
                    pass

    # 块定义
    for block in doc.blocks:
        if block.name.lower() in ("*model_space", "*paper_space"):
            continue
        for e in block:
            add(e, f"BLOCK:{block.name}")

    return rows


# ---------------------------------------------------------------------------
# 回填译文
# ---------------------------------------------------------------------------

def apply_translations(dxf_path: Path, json_path: Path) -> tuple[int, int]:
    """按 {原文:译文} 内容匹配替换文本。返回 (替换实体数, 译文条数)。"""
    import ezdxf

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    # 支持两种结构: [{original, translation}] 或 {original: translation}
    mapping: dict[str, str] = {}
    if isinstance(data, dict):
        mapping = {str(k): str(v) for k, v in data.items() if str(k) != str(v)}
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "original" in item and "translation" in item:
                o, t = str(item["original"]), str(item["translation"])
                if o and o != t:
                    mapping[o] = t
    if not mapping:
        raise RuntimeError(f"译文清单为空或格式不对: {json_path}")

    doc = ezdxf.readfile(str(dxf_path))
    count = 0
    for entity in doc.entitydb:
        e = doc.entitydb[entity]
        if e is None or not hasattr(e, "dxf"):
            continue
        try:
            if e.dxftype() == "MTEXT":
                cur = e.text
                if cur in mapping:
                    e.text = mapping[cur]
                    count += 1
            elif e.dxftype() in ("TEXT", "ATTDEF", "ATTRIB"):
                cur = e.dxf.text
                if cur in mapping:
                    e.dxf.text = mapping[cur]
                    count += 1
        except Exception:
            pass

    out = dxf_path.with_name(dxf_path.stem + "_ZH.dxf")
    doc.saveas(str(out))
    return count, len(mapping)


# ---------------------------------------------------------------------------
# 子命令
# ---------------------------------------------------------------------------

def cmd_check(_args) -> int:
    print("=" * 50)
    print("dwg skill 环境自检")
    print("=" * 50)
    ok = True

    try:
        import ezdxf
        print(f"✓ ezdxf {ezdxf.__version__} @ {sys.executable}")
    except ImportError:
        ok = False
        print("✗ ezdxf 未安装: py -3 -m pip install ezdxf")

    oda = find_oda()
    if oda:
        print(f"✓ ODA: {oda}")
    else:
        ok = False
        print("✗ ODA File Converter 未找到，请安装或修改 ODA_CANDIDATES")

    print("=" * 50)
    print("自检通过" if ok else "自检未通过")
    return 0 if ok else 1


def cmd_convert(args) -> int:
    src = Path(args.file)
    if not src.exists():
        print(f"文件不存在: {src}", file=sys.stderr)
        return 2
    ext = src.suffix.lower()
    if ext == ".dwg":
        out_ext = "dxf"
    elif ext == ".dxf":
        out_ext = "dwg"
    else:
        print(f"不支持的扩展名: {ext}（仅支持 .dwg / .dxf）", file=sys.stderr)
        return 2

    work = Path(tempfile.mkdtemp(prefix="dwg_convert_"))
    try:
        out = oda_convert_one(src, work, out_ext)
        final = src.parent / out.name
        shutil.move(str(out), str(final))
        print(f"✓ {src.name} → {final} ({final.stat().st_size / 1024 / 1024:.1f} MB)")
        return 0
    except RuntimeError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


def cmd_extract(args) -> int:
    src = Path(args.file)
    if not src.exists():
        print(f"文件不存在: {src}", file=sys.stderr)
        return 2
    try:
        rows = extract_texts(src)
    except Exception as exc:
        print(f"[错误] 提取失败: {exc}", file=sys.stderr)
        return 1

    if not rows:
        print("未提取到任何文本（纯图形图纸？）", file=sys.stderr)
        return 1

    out_dir = Path(tempfile.mkdtemp(prefix="dwg_extract_", dir=str(src.parent)))
    out_json = out_dir / "texts.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

    # 去重后的待译原文（回填按原文匹配，需唯一）
    seen = {}
    for r in rows:
        seen.setdefault(r["text"], r)
    uniq = list(seen.values())

    out_txt = out_dir / "unique_texts.txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        for i, r in enumerate(uniq, 1):
            f.write(f"{i}\t{r['text']}\n")

    print(f"✓ 提取 {len(rows)} 条文本（去重 {len(uniq)} 条）")
    print(f"  清单: {out_json}")
    print(f"  待译原文(每行一条): {out_txt}")
    return 0


def cmd_apply(args) -> int:
    dxf = Path(args.dxf)
    js = Path(args.json)
    if not dxf.exists() or not js.exists():
        print("文件不存在", file=sys.stderr)
        return 2
    try:
        count, total = apply_translations(dxf, js)
    except Exception as exc:
        print(f"[错误] 回填失败: {exc}", file=sys.stderr)
        return 1
    out = dxf.with_name(dxf.stem + "_ZH.dxf")
    print(f"✓ 回填 {count}/{total} 条 → {out.name}")
    return 0


def cmd_translate(args) -> int:
    """一步到位：DWG→(临时DXF)→提取→输出待译清单→(Agent翻译)→回填→转回DWG。
    中间 DXF 全在临时目录，结束后自动清理，用户只看到输入 DWG 和输出 _ZH.dwg。
    """
    src = Path(args.dwg)
    if not src.exists():
        print(f"文件不存在: {src}", file=sys.stderr)
        return 2

    work = Path(tempfile.mkdtemp(prefix="dwg_translate_"))
    try:
        # ① DWG → DXF（临时目录）
        print("① DWG → DXF ...", flush=True)
        dxf = oda_convert_one(src, work, "dxf")

        # ② 提取文字（临时目录）
        print("② 提取文字 ...", flush=True)
        rows = extract_texts(dxf)
        if not rows:
            raise RuntimeError("未提取到任何文本（纯图形图纸？）")
        seen = {}
        for r in rows:
            seen.setdefault(r["text"], r)
        uniq = list(seen.values())

        # 待译清单输出到输入文件同目录，供 Agent 翻译
        out_dir = src.parent
        out_txt = out_dir / (src.stem + "_待译.txt")
        with open(out_txt, "w", encoding="utf-8") as f:
            for i, r in enumerate(uniq, 1):
                f.write(f"{i}\t{r['text']}\n")
        print(f"✓ 提取 {len(rows)} 条文本（去重 {len(uniq)} 条）")
        print(f"  待译清单: {out_txt}")

        # ③ Agent 翻译阶段（外部：翻译后调用 apply/convert-back）
        print(f"\n下一步: 翻译 {out_txt} 为 JSON 后执行:")
        print(f"  py -3 ...dwg.py apply-back \"{src}\" \"<译文.json>\"")
        return 0
    except Exception as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


def cmd_apply_back(args) -> int:
    """翻译完成后一步到位：DWG→临时DXF→回填→转回DWG（输出 _ZH.dwg）。"""
    src = Path(args.dwg)
    js = Path(args.json)
    if not src.exists() or not js.exists():
        print("文件不存在", file=sys.stderr)
        return 2

    work = Path(tempfile.mkdtemp(prefix="dwg_back_"))
    try:
        print("① DWG → DXF（临时）...", flush=True)
        dxf = oda_convert_one(src, work, "dxf")

        print("② 回填译文 ...", flush=True)
        count, total = apply_translations(dxf, js)
        zh_dxf = dxf.with_name(dxf.stem + "_ZH.dxf")

        print("③ DXF → DWG（临时）...", flush=True)
        out = oda_convert_one(zh_dxf, work / "out", "dwg")
        final = src.parent / (src.stem + "_ZH.dwg")
        shutil.move(str(out), str(final))
        print(f"✓ 回填 {count}/{total} 条 → {final} ({final.stat().st_size / 1024 / 1024:.1f} MB)")
        return 0
    except Exception as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


def cmd_convert_back(args) -> int:
    src = Path(args.dxf)
    if not src.exists():
        print(f"文件不存在: {src}", file=sys.stderr)
        return 2
    work = Path(tempfile.mkdtemp(prefix="dwg_back_"))
    try:
        out = oda_convert_one(src, work, "dwg")
        final = src.parent / (src.stem + ".dwg")
        shutil.move(str(out), str(final))
        print(f"✓ {src.name} → {final} ({final.stat().st_size / 1024 / 1024:.1f} MB)")
        return 0
    except RuntimeError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DWG 操作 CLI（转换/提取/回填）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="环境自检")

    p = sub.add_parser("convert", help="DWG<->DXF 转换（按扩展名判断方向）")
    p.add_argument("file")

    p = sub.add_parser("extract", help="提取 DXF 文字 → JSON 清单")
    p.add_argument("file")

    p = sub.add_parser("apply", help="按译文 JSON 回填 → _ZH.dxf")
    p.add_argument("dxf")
    p.add_argument("json")

    p = sub.add_parser("convert-back", help="翻译后 DXF → DWG")
    p.add_argument("dxf")

    p = sub.add_parser("translate", help="一步到位：DWG→待译清单（中间 DXF 自动清理）")
    p.add_argument("dwg")

    p = sub.add_parser("apply-back", help="翻译后一步到位：DWG+译文JSON→_ZH.dwg（中间 DXF 自动清理）")
    p.add_argument("dwg")
    p.add_argument("json")

    args = parser.parse_args(argv)
    handlers = {
        "check": cmd_check,
        "convert": cmd_convert,
        "extract": cmd_extract,
        "apply": cmd_apply,
        "convert-back": cmd_convert_back,
        "translate": cmd_translate,
        "apply-back": cmd_apply_back,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
