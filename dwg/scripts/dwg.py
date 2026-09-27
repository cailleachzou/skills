#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
DWG 操作 CLI —— 转换 / 提取 / 回填 / 外参（dwg skill 入口）

基于 ODA File Converter + ezdxf，无 AutoCAD、无 MIMO 依赖。

子命令：
  check                环境自检（ezdxf / ODA 可执行）
  convert <file>       转换 DWG<->DXF（按扩展名自动判断方向）
                       输出: 同目录下 <stem>.<另一格式>（ODA 要求输入/输出为独立目录）
  extract <dxf>        提取图纸文字 → JSON 清单（原文|类型|空间|图层|坐标|高度|旋转）
  apply <dxf> <json>   按 {原文:译文} 回填译文 → 输出 _ZH.dxf
  convert-back <dxf>   翻译后 DXF → DWG（_ZH.dwg）
  translate <dwg>      前半程一步到位：DWG → <stem>_待译.txt（中间 DXF 自动清理）
  apply-back <dwg> <json>  后半程一步到位：DWG + 译文 JSON → _ZH.dwg
  xref <dwg>...        查看 / 修改图纸的**外部参照路径**（不改块名、不动图面）

用法示例：
  py dwg.py check
  py dwg.py convert in.dwg            # in.dwg -> in.dxf
  py dwg.py convert in.dxf            # in.dxf -> in.dwg
  py dwg.py extract in.dxf            # -> in_提取/texts.json + unique_texts.txt
  py dwg.py apply in.dxf texts_zh.json   # -> in_ZH.dxf
  py dwg.py convert-back in_ZH.dxf    # -> in_ZH.dwg
  py dwg.py translate in.dwg          # -> in_待译.txt
  py dwg.py apply-back in.dwg zh.json # -> in_ZH.dwg
  py dwg.py xref in.dwg               # 列出外参（块名 / 路径 / 目标是否存在）
  py dwg.py xref in.dwg --set '[R]Building D=..\[R]_ZH\[R]Building D_ZH.dwg' --apply

依赖：
  - Python 3 + ezdxf（py -3 -m pip install ezdxf）
  - ODA File Converter（默认 C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe）
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Windows 控制台代码页不一定是 UTF-8（本机为 cp1252），中文提示会抛
# UnicodeEncodeError 把整条命令崩掉。强制 stdout/stderr 走 UTF-8 并降级替换。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# ezdxf 首次导入时 fontTools 会扫描系统字体目录，本机的 mstmc.ttf 不是标准
# TrueType，会往 stderr 喷两行警告污染命令输出。只静音这一次导入。
with contextlib.redirect_stderr(io.StringIO()):
    try:
        import ezdxf  # noqa: F401
    except ImportError:
        ezdxf = None  # 真缺依赖时由各命令自行报错，那里的提示更完整

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

# MTEXT 内联控制码：\P 硬换行、\~ 不换行空格、\{ \} 字面花括号
_MTEXT_CTRL = re.compile(r"\\P", re.IGNORECASE)


def _norm_key(text: str) -> str:
    """归一化匹配键：把 MTEXT 控制码折算成等价普通字符，并压缩空白。

    翻译环节很容易把 \\P 当普通字符吞掉、或改写成真实换行，回填时精确匹配就会
    失配——而且失配不报错，只是那段文字静默地没被翻译。归一键让"只差控制码"
    的译文仍然能命中。
    """
    s = _MTEXT_CTRL.sub("\n", str(text))
    s = s.replace("\\~", " ").replace("\\{", "{").replace("\\}", "}")
    return " ".join(s.split())


def _to_mtext(text: str) -> str:
    """回填 MTEXT 前，把译文里的真实换行折算回 \\P。

    MTEXT 内容中的换行必须写成 \\P；带真实 \\n 的字符串直接写回会产出坏 DXF。
    译文自己已经带 \\P 的就原样保留，不重复折算。
    """
    if _MTEXT_CTRL.search(text):
        return text
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\P")


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

    # 精确匹配 + 归一化兜底：MTEXT 的 \P/\~ 等控制码常被翻译环节改写，
    # 归一化后仍能对上，避免"看着翻译了、其实没生效"的静默失配。
    norm_index: dict[str, str] = {}
    for k, v in mapping.items():
        norm_index.setdefault(_norm_key(k), v)

    def lookup(cur: str) -> str | None:
        if cur in mapping:
            return mapping[cur]
        return norm_index.get(_norm_key(cur))

    doc = ezdxf.readfile(str(dxf_path))
    count = 0
    for entity in doc.entitydb:
        e = doc.entitydb[entity]
        if e is None or not hasattr(e, "dxf"):
            continue
        try:
            if e.dxftype() == "MTEXT":
                new = lookup(e.text)
                if new is not None:
                    e.text = _to_mtext(new)
                    count += 1
            elif e.dxftype() in ("TEXT", "ATTDEF", "ATTRIB"):
                new = lookup(e.dxf.text)
                if new is not None:
                    e.dxf.text = new
                    count += 1
        except Exception:
            pass

    out = dxf_path.with_name(dxf_path.stem + "_ZH.dxf")
    doc.saveas(str(out))
    return count, len(mapping)


# ---------------------------------------------------------------------------
# 外部参照（xref）
# ---------------------------------------------------------------------------
# 参照路径在 DXF 里就是 BLOCK 表项上的 group code 1（明文，形如 `..\[R]_ZH\x.dwg`），
# 块名本身不含路径信息——改路径不影响图面显示，图面仍显示原块名。
#
# ⚠ 必须用 flags & 4 筛「真外参」。直接按「group code 1 有值」去找会误伤普通块：
#   实测图纸里 CA-BG / CA-CR / AUDIT_I_xxx 这类普通块（flags=0）的 group 1 写着
#   `Acad:XRef` 占位串，照改就把它们改坏了。
XREF_FLAG = 4


def _iso_convert(src: Path, work: Path, tag: str, out_ext: str) -> Path:
    """把 src 复制到 work/<tag>/in 后再交给 ODA，产物落在 work/<tag>/out。

    ODA 会把「输入目录里的所有文件」一起转换，直接传 src.parent（oda_convert_one
    的默认行为）会在一个有 20 张图的目录里老老实实转 20 遍。隔离后每次只转 1 个，
    顺带绕开中文/特殊字符文件名在命令行上的坑。
    """
    in_dir = work / tag / "in"
    in_dir.mkdir(parents=True, exist_ok=True)
    staged = in_dir / (tag + src.suffix.lower())
    shutil.copy2(src, staged)
    return oda_convert_one(staged, work / tag / "out", out_ext)


def list_xrefs(dxf_path: Path) -> list[dict]:
    """列出图纸里真正的外部参照。返回 [{name, path, flags}]。"""
    import ezdxf

    doc = ezdxf.readfile(str(dxf_path))
    out: list[dict] = []
    for blk in doc.blocks:
        flags = blk.block.dxf.get("flags", 0)
        if not (flags & XREF_FLAG):
            continue
        out.append({
            "name": blk.name,
            "path": str(blk.block.dxf.get("xref_path", "") or ""),
            "flags": flags,
        })
    return out


def resolve_xref(dwg_dir: Path, path: str) -> Path | None:
    """按图纸所在目录把参照路径解析成绝对路径；空路径返回 None。

    相对路径是相对**图纸（DWG）所在目录**、不是相对 CWD——判断"参照断没断"时
    这一点最常搞错。
    """
    if not path:
        return None
    p = Path(path.replace("\\", "/"))
    return p if p.is_absolute() else (dwg_dir / p)


def set_xrefs(dxf_path: Path, mapping: dict[str, str]) -> tuple[list[tuple[str, str, str]], set[str]]:
    """按 {块名: 新路径} 改外参。返回 (改动清单, 没命中的块名)。

    只动 flags & 4 的块；块名不在 mapping 里的一律原样保留（不猜、不编路径）。
    """
    import ezdxf

    doc = ezdxf.readfile(str(dxf_path))
    changes: list[tuple[str, str, str]] = []
    hit: set[str] = set()
    for blk in doc.blocks:
        if not (blk.block.dxf.get("flags", 0) & XREF_FLAG):
            continue
        if blk.name not in mapping:
            continue
        hit.add(blk.name)
        old = str(blk.block.dxf.get("xref_path", "") or "")
        new = mapping[blk.name]
        if old == new:
            continue
        blk.block.dxf.xref_path = new
        changes.append((blk.name, old, new))
    if changes:
        doc.saveas(str(dxf_path))
    return changes, set(mapping) - hit


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

    # 固定目录名：可重复运行覆盖，不在用户图纸目录里留下随机命名的垃圾目录
    out_dir = src.parent / (src.stem + "_提取")
    out_dir.mkdir(parents=True, exist_ok=True)
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


def cmd_xref(args) -> int:
    """查看 / 修改外部参照路径。

    无 --set 时只列出（只读）；给了 --set 但没给 --apply 时是预演；
    加 --apply 才原地写回，写回前把原文件备份到 <图纸目录>/_work/backup-before-xref/。
    """
    paths = [Path(p) for p in args.dwg]
    for p in paths:
        if not p.exists():
            print(f"文件不存在: {p}", file=sys.stderr)
    paths = [p for p in paths if p.exists()]
    if not paths:
        return 2

    mapping: dict[str, str] = {}
    for item in (args.set or []):
        name, sep, path = item.partition("=")
        if not sep or not name.strip():
            print(f"--set 格式应为 '块名=新路径'，收到: {item}", file=sys.stderr)
            return 2
        mapping[name.strip()] = path.strip()
    if mapping and not args.apply:
        print("（预演模式：只报差异，不写回；确认无误后加 --apply）\n")

    rc = 0
    for dwg in paths:
        work = Path(tempfile.mkdtemp(prefix="dwg_xref_"))
        try:
            print(f"### {dwg.name}")
            dxf = _iso_convert(dwg, work, "src", "dxf")
            found = list_xrefs(dxf)
            if not found:
                print("    （无外部参照）")
            for x in found:
                tgt = resolve_xref(dwg.parent, x["path"])
                if not x["path"]:
                    mark = "  ✗空路径"
                elif tgt is None:
                    mark = ""
                else:
                    mark = "  ✓ 目标存在" if tgt.exists() else "  ✗ 目标缺失"
                print(f"    {x['name']}  →  {x['path']}{mark}")

            if not mapping:
                continue

            changes, unhit = set_xrefs(dxf, mapping)
            if unhit:
                print(f"    ⚠ 未改动（不在图中或不是外参）: {', '.join(sorted(unhit))}")
            if not changes:
                print("    无改动")
                continue
            for name, old, new in changes:
                print(f"    改 {name}: {old}  →  {new}")
            if not args.apply:
                continue

            out = _iso_convert(dxf, work, "out", "dwg")
            backup_dir = (Path(args.backup_dir) if args.backup_dir
                          else dwg.parent / "_work" / "backup-before-xref")
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dwg, backup_dir / dwg.name)
            shutil.move(str(out), str(dwg))
            print(f"    ✓ 已写回 {dwg.name}（改 {len(changes)} 处）")

            if args.verify:
                vdxf = _iso_convert(dwg, work, "chk", "dxf")
                print("    复核（从写回后的 DWG 重新读出）:")
                for x in list_xrefs(vdxf):
                    tgt = resolve_xref(dwg.parent, x["path"])
                    mark = "✓ 存在" if (tgt and tgt.exists()) else "✗ 缺失"
                    print(f"      {x['name']} → {x['path']}  [{mark}]")
        except Exception as exc:
            print(f"    [错误] {type(exc).__name__}: {exc}", file=sys.stderr)
            rc = 1
        finally:
            shutil.rmtree(work, ignore_errors=True)
    return rc


def cmd_translate(args) -> int:
    """DWG→(临时DXF)→提取→输出待译清单。中间 DXF 在临时目录，结束后自动清理。

    只负责前半程：翻译必须由 Agent 在对话中完成，之后用 apply-back 收尾。
    用户最终拿到的是输入 DWG、<stem>_待译.txt 和 <stem>_ZH.dwg。
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

    p = sub.add_parser("xref", help="查看/修改外部参照路径（默认只列只演，--apply 才写回）")
    p.add_argument("dwg", nargs="+", help="一张或多张 DWG")
    p.add_argument("--set", action="append", metavar="块名=路径",
                   help="要改的参照，形如 '[R]Building D=..\\[R]_ZH\\[R]Building D_ZH.dwg'，可重复")
    p.add_argument("--apply", action="store_true", help="真正写回（不加则只预演）")
    p.add_argument("--backup-dir", metavar="DIR",
                   help="原文件备份目录（默认 <图纸目录>/_work/backup-before-xref）")
    p.add_argument("--verify", action="store_true", help="写回后从 DWG 重新读出复核")

    args = parser.parse_args(argv)
    handlers = {
        "check": cmd_check,
        "convert": cmd_convert,
        "extract": cmd_extract,
        "apply": cmd_apply,
        "convert-back": cmd_convert_back,
        "translate": cmd_translate,
        "apply-back": cmd_apply_back,
        "xref": cmd_xref,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
