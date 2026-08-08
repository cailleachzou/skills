#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DWG 图纸英译中 — 一键翻译脚本（dwg-translate 技能入口）

流程（全部实测通过）：
  1. DWG → DXF   （AutoCAD COM SaveAs 格式 25 = ac2004 DXF）
  2. 文字提取     （ezdxf → Excel：序号|原文|译文+坐标/图层）
  3. MIMO 批量翻译（并发 6 + 补译循环，175 条约 102 秒）
  4. 回填到 DXF   （ezdxf 按 {原文:译文} 替换 TEXT/MTEXT/ATTDEF/ATTRIB）
  5. DXF → DWG   （AutoCAD COM SaveAs 格式 24 = ac2004 DWG → *_ZH.dwg）

依赖：
  - 独立 venv：C:/Users/59620/cad-translate-cli/.venv/Scripts/python.exe
    （已装 ezdxf / pandas / pywin32 / openpyxl / pydantic-settings）
  - AutoDesk AutoCAD 2027（ProgID AutoCAD.Application.26；exe 位于 C:/Program Files/Autodesk/AutoCAD 2027/acad.exe）
    首次使用须【手动打开一次 AutoCAD】完成 COM 注册与许可证初始化
  - MIMO_API_KEY：已写入 ~/.config/cli-anything-cad/config.json（llm.primary.api_key）

用法：
  <venv python> translate_dwg.py "<输入.dwg>" [--output-dir DIR] [--target-language zh] [--keep] [--check]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# 路径常量（项目已从桌面迁移到用户目录）
# ---------------------------------------------------------------------------
REPO_ROOT = r"C:\Users\59620\cad-translate-cli"
ACAD_EXE = r"C:\Program Files\Autodesk\AutoCAD 2027\acad.exe"
PROG_ID = "AutoCAD.Application.26"
CONFIG_FILE = Path.home() / ".config" / "cli-anything-cad" / "config.json"

# AutoCAD COM SaveAs 格式码
#   DXF: ac2004=25, ac2007=37, ac2010=50, ac2013=60, ac2018=61
#   DWG: ac2004=24, ac2007=36, ac2010=48, ac2013=58, ac2018=64
DXF_FORMATS = (25, 37, 50, 60, 61)
DWG_FORMATS = (24, 36, 48, 58, 64)


def _bootstrap() -> None:
    """把项目根插入 sys.path，必须在 import pipeline 之前调用。"""
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")


_bootstrap()

from cli.core.pipeline import (  # noqa: E402
    run_apply,
    run_convert,
    run_extract,
    run_translate_excel,
)


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------

def _step(title: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"\n{'=' * 60}\n[{ts}] {title}\n{'=' * 60}", flush=True)


def _cfg_target_language() -> str:
    try:
        from lib.services.config_manager import ConfigManager
        return str(ConfigManager().get_effective_config().get("cad", {}).get("target_language") or "zh")
    except Exception:
        return "zh"


def _cfg_has_api_key() -> bool:
    try:
        if not CONFIG_FILE.exists():
            return False
        import json
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        primary = data.get("llm", {}).get("primary", {})
        return bool(primary.get("api_key") or primary.get("provider"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# AutoCAD COM 连接
# ---------------------------------------------------------------------------

def ensure_autocad(timeout: int = 120):
    """
    连接 AutoCAD 2027。优先复用运行中的实例（GetActiveObject），
    失败则用 powershell Start-Process 启动并轮询等待（不用 Dispatch，实测报 Server execution failed）。
    返回 AutoCAD Application COM 对象。
    """
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()

    # 1) 复用运行中的实例
    try:
        app = win32com.client.GetActiveObject(PROG_ID)
        print("✓ 已连接到运行中的 AutoCAD", flush=True)
        return app
    except Exception:
        pass

    # 2) 启动新实例
    if ACAD_EXE and Path(ACAD_EXE).exists():
        print("正在启动 AutoCAD …（冷启动约需 30-60 秒）", flush=True)
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"Start-Process -FilePath '{ACAD_EXE}'"],
                check=False, capture_output=True, timeout=30,
            )
        except Exception as exc:
            print(f"启动 AutoCAD 命令失败: {exc}", file=sys.stderr)

    # 3) 轮询等待就绪
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            app = win32com.client.GetActiveObject(PROG_ID)
            print("✓ AutoCAD 已就绪", flush=True)
            return app
        except Exception:
            time.sleep(2)

    raise RuntimeError(
        "AutoCAD 未在超时时间内启动。请手动打开一次 AutoCAD 2027，"
        "完成首次 COM 注册与许可证初始化后重试。"
    )


# ---------------------------------------------------------------------------
# DXF → DWG（AutoCAD COM 保存）
# ---------------------------------------------------------------------------

def dxf_to_dwg(dxf_path: Path, dwg_path: Path) -> str:
    """打开翻译后 DXF，用 AutoCAD SaveAs 转回 DWG（格式 24 ac2004，兜底更高版本）。"""
    import win32com.client

    dwg_path = Path(dwg_path)
    dwg_path.unlink(missing_ok=True)  # 避免 SaveAs 因目标存在报错

    app = ensure_autocad()
    try:
        app.Visible = False
    except Exception:
        pass

    doc = None
    try:
        doc = app.Documents.Open(str(dxf_path))
        last_err: Exception | None = None
        saved = False
        for ver in DWG_FORMATS:
            try:
                doc.SaveAs(str(dwg_path), ver)
                saved = True
                break
            except Exception as exc:
                last_err = exc
                continue
        if not saved:
            raise last_err or RuntimeError("SaveAs 失败")
        print(f"✓ 已输出 DWG: {dwg_path}", flush=True)
        return str(dwg_path)
    finally:
        if doc is not None:
            try:
                doc.Close(False)  # 不保存，保持 AutoCAD 进程存活供下次复用
            except Exception:
                pass


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run_pipeline(dwg: Path, output_dir: Path, target_lang: str, keep: bool) -> dict:
    stem = dwg.stem
    work = Path(tempfile.mkdtemp(prefix="dwg_translate_", dir=str(output_dir)))

    try:
        # 1) DWG → DXF
        _step("① DWG → DXF（AutoCAD COM）")
        conv = run_convert(str(dwg), str(work), backend_override="autocad_com")
        dxf = Path(conv["output_file"])
        print(f"✓ DXF: {dxf.name} ({dxf.stat().st_size / 1024 / 1024:.1f} MB)", flush=True)

        # 2) DXF → Excel
        _step("② 提取文字 → Excel")
        ext = run_extract(str(dxf), str(work))
        excel = Path(ext["excel_file"])
        text_count = int(ext.get("text_count", 0))
        print(f"✓ 提取 {text_count} 条文本 → {excel.name}", flush=True)
        if text_count == 0:
            raise RuntimeError("未提取到任何文本，可能是纯图形图纸")

        # 3) 翻译 Excel
        _step(f"③ MIMO 批量翻译 → {target_lang}（并发 6，约 1-3 分钟）")
        t0 = time.time()
        tr = run_translate_excel(str(excel), str(work), target_language=target_lang)
        xl_done = Path(tr["output_file"])
        translated = int(tr.get("translated_cells", 0))
        print(f"✓ 翻译 {translated} 条（耗时 {time.time() - t0:.0f} 秒）→ {xl_done.name}", flush=True)

        # 4) 回填到 DXF
        _step("④ 回填翻译到 DXF")
        ap = run_apply(str(dxf), excel_file=str(xl_done), output_dir=str(work))
        translated_dxf = Path(ap["output_file"])
        entities = int(ap.get("translated_entities", 0))
        print(f"✓ 回填 {entities} 个文本实体 → {translated_dxf.name}", flush=True)

        # 5) DXF → DWG
        _step("⑤ DXF → DWG（AutoCAD COM）")
        final_dwg = output_dir / f"{stem}_ZH.dwg"
        dxf_to_dwg(translated_dxf, final_dwg)

        _step("✅ 完成")
        print(f"最终输出: {final_dwg}", flush=True)
        print(f"翻译文件: {xl_done}", flush=True)
        return {"ok": True, "dwg": str(final_dwg), "work": str(work), "excel": str(xl_done)}

    except Exception:
        print(f"\n[错误] 流程失败，中间文件保留在: {work}", file=sys.stderr)
        raise
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------------------
# 环境自检
# ---------------------------------------------------------------------------

def preflight() -> int:
    print("=" * 60)
    print("dwg-translate 环境自检")
    print("=" * 60)
    ok = True

    # ① venv 导入
    try:
        import ezdxf  # noqa: F401
        import pandas  # noqa: F401
        import win32com.client  # noqa: F401
        print(f"✓ venv 可用: {sys.executable}")
    except ImportError as exc:
        ok = False
        print(f"✗ venv 缺少依赖: {exc}")
        print("  修复: 运行 .venv 重建或 pip install ezdxf pandas pywin32 openpyxl")

    # ② 运行时配置 / API key
    if _cfg_has_api_key():
        print(f"✓ 运行时配置: {CONFIG_FILE}（含 LLM API key）")
    else:
        ok = False
        print(f"✗ 运行时配置缺失或未含 API key: {CONFIG_FILE}")
        print("  修复: 运行项目 onboard 或编辑 config.json 的 llm.primary")

    # ③ AutoCAD 可连（快速探测 20 秒）
    try:
        app = ensure_autocad(timeout=20)
        try:
            print(f"✓ AutoCAD 已连接: {app.Name} v{app.Version}")
        except Exception:
            print("✓ AutoCAD 已连接")
        ok = True
    except RuntimeError as exc:
        ok = False
        print(f"✗ {exc}")

    # ④ 输出目录可写
    test_dir = Path(tempfile.gettempdir()) / "dwg_translate_write_test"
    try:
        test_dir.mkdir(parents=True, exist_ok=True)
        probe = test_dir / ".probe"
        probe.write_text("ok")
        probe.unlink()
        print(f"✓ 输出目录可写: {tempfile.gettempdir()}")
    except Exception as exc:
        ok = False
        print(f"✗ 输出目录不可写: {exc}")

    print("=" * 60)
    print("自检通过" if ok else "自检未通过，请按上述指引修复")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DWG 图纸英译中（dwg-translate）")
    parser.add_argument("dwg", nargs="?", help="输入 DWG 文件路径")
    parser.add_argument("--output-dir", default=None, help="输出目录（默认：与输入同目录）")
    parser.add_argument("--target-language", default=None, help="目标语言（默认：读配置，zh）")
    parser.add_argument("--keep", action="store_true", help="保留中间文件（DXF/Excel/翻译文件）")
    parser.add_argument("--check", action="store_true", help="环境自检（不执行翻译）")
    args = parser.parse_args(argv)

    if args.check or not args.dwg:
        return preflight()

    dwg = Path(args.dwg)
    if not dwg.exists():
        print(f"文件不存在: {dwg}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir) if args.output_dir else dwg.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    target_lang = args.target_language or _cfg_target_language()

    try:
        run_pipeline(dwg, output_dir, target_lang, args.keep)
    except Exception as exc:
        print(f"\n[错误] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
