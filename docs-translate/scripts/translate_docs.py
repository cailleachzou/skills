#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs-translate: 离线文档翻译（Word / PPT / PDF），保留原格式。

原理:
  - docx/pptx: 本质是 zip，解包 -> 提取 XML 文本节点 -> llama-server 批量翻译
               -> 回填 -> 重新打包。样式/排版 100% 保留。
  - pdf: 用 pymupdf 提取每行文本(带坐标) -> 翻译 -> 在原文下方叠加译文，
         输出"原文+译文"双层 PDF（原文排版不动）。

引擎: 完全离线 —— 本机 llama.cpp Vulkan + Qwen2.5 GGUF（OpenAI 兼容 API）。
用法:
  py translate_docs.py <文件或目录> [-o 输出目录] [--model qwen7b|qwen14b|qwen7b-q6]
                      [--lang zh|en] [--port 8080] [--no-server] [--batch 10]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import zipfile
import shutil
from pathlib import Path

try:
    import requests
    from lxml import etree
    import fitz  # pymupdf
except ImportError as e:
    sys.exit(f"[错误] 缺少依赖: {e}\n请先: py -3 -m pip install requests lxml pymupdf")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

LLAMA_SERVER = r"C:\Users\caill\tools\llama-cpp\vulkan\llama-server.exe"
MODELS = {
    "qwen7b":   r"C:\Users\caill\.ollama\models\blobs\sha256-2bada8a7450677000f678be90653b85d364de7db25eb5ea54136ada5f3933730",
    "qwen14b":  r"C:\Users\caill\models\Qwen2.5-14B-Instruct-Q4_K_M.gguf",
    "qwen7b-q6": r"C:\Users\caill\models\Qwen2.5-7B-Instruct-Q6_K.gguf",
}
DEFAULT_MODEL = "qwen7b"
# 速度/质量档位 -> 模型映射
MODE_MODELS = {
    "fast":     "qwen7b",    # ~61 tok/s, 最快
    "balanced": "qwen7b-q6", # ~49 tok/s, 默认, Q6 精度更好
    "quality":  "qwen14b",   # ~28 tok/s, 质量最好
}
MODE_HINTS = {
    "fast":     "qwen7b   (~61 tok/s, 最快, 质量够用)",
    "balanced": "qwen7b-q6(~49 tok/s, 默认, 精度更好)",
    "quality":  "qwen14b  (~28 tok/s, 质量最好, PDF 推荐)",
}

SKIP_RE = re.compile(r"^[\s\d\W_]{0,3}$|^https?://|^www\.|^[\d\.\-\s]+$|^[·•●▪◦\-\u2022\s]+$", re.I)


# ---------- llama-server 管理 ----------

def server_healthy(port: int) -> bool:
    try:
        r = requests.get(f"http://127.0.0.1:{port}/health", timeout=2)
        return r.status_code == 200 and "ok" in r.text.lower()
    except Exception:
        return False


def ensure_server(port: int, model: str, no_server: bool):
    """确保 llama-server 运行。返回 (server_proc_or_None)。None 表示复用已有。"""
    if server_healthy(port):
        print(f"[引擎] 复用已有 llama-server @ {port}")
        return None
    if no_server:
        sys.exit(f"[错误] llama-server 未运行在 {port}，且指定了 --no-server。"
                 f"请先启动: llama-server.exe -m \"{MODELS[model]}\" -ngl 99 --port {port}")
    model_path = MODELS[model]
    print(f"[引擎] 启动 llama-server ({model}) ...")
    log = open(os.path.join(os.environ.get("TEMP", "/tmp"), f"llama-docs-{port}.log"), "w")
    proc = subprocess.Popen(
        [LLAMA_SERVER, "-m", model_path, "-ngl", "99", "--host", "127.0.0.1",
         "--port", str(port), "-c", "4096"],
        stdout=log, stderr=log)
    deadline = time.time() + 180
    while time.time() < deadline:
        if server_healthy(port):
            print(f"[引擎] 就绪（pid {proc.pid}）")
            return proc
        if proc.poll() is not None:
            sys.exit(f"[错误] llama-server 启动失败，日志: {log.name}")
        time.sleep(1)
    sys.exit(f"[错误] llama-server 启动超时，日志: {log.name}")


def shutdown_server(proc) -> None:
    """关闭本次自启动的 llama-server（不影响用户已有的）。"""
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=10)
        print("[引擎] 已关闭本次启动的 llama-server")
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


# ---------- 翻译 ----------

def translate_batch(texts, port: int, lang: str, model: str) -> list:
    """一次请求翻译一批，返回与输入等长的译文列表（失败返回 None）。"""
    if not texts:
        return []
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    sys_msg = ("You are a professional translator. Translate every line in the user's "
               "message into " + ("Chinese (简体中文)" if lang == "zh" else "English") +
               ". Output ONLY the translations, one per line, in the SAME ORDER and "
               "SAME NUMBER of lines as the input. Do NOT add numbering, quotes, "
               "explanations, or blank lines.")
    payload = {
        "model": "local",
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": numbered},
        ],
        "temperature": 0.1,
        "max_tokens": min(4096, max(512, len(numbered) * 2 + 256)),
    }
    try:
        r = requests.post(f"http://127.0.0.1:{port}/v1/chat/completions",
                          json=payload, timeout=300)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"    ! 请求失败: {e}")
        return None
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    # 去掉模型可能加的行号前缀
    cleaned = [re.sub(r"^\d+[\.\、\)]\s*", "", ln) for ln in lines]
    if len(cleaned) != len(texts):
        print(f"    ! 数量不符({len(cleaned)}/{len(texts)})，降级逐条翻译")
        return None
    return cleaned


def translate_all(texts, port: int, lang: str, model: str, batch_size: int) -> list:
    """分块翻译全部文本，顺序与输入一致。"""
    results = [None] * len(texts)
    done = 0
    for start in range(0, len(texts), batch_size):
        chunk = texts[start:start + batch_size]
        idxs = [start + i for i in range(len(chunk))]
        out = translate_batch(chunk, port, lang, model)
        if out is None:
            # 逐条兜底
            for j, k in enumerate(idxs):
                one = translate_batch([chunk[j]], port, lang, model)
                results[k] = one[0] if one else None
        else:
            for k, v in zip(idxs, out):
                results[k] = v
        done += len(chunk)
        print(f"    [{done}/{len(texts)}] 条已翻译")
    return results


def translate_single(text: str, port: int, lang: str, model: str, code_mode: bool = False):
    """单条无编号翻译（用于多行块 / 代码块）。"""
    if code_mode:
        sys_msg = ("You are a professional translator. This is a code/example block. "
                   "Translate ONLY the human-language text inside it (comments, "
                   "annotations, sample dialogue, natural-language descriptions) into " +
                   ("Chinese (简体中文)" if lang == "zh" else "English") +
                   ". Keep ALL code syntax, identifiers, commands, paths, file names, "
                   "and structural markers (tree glyphs, arrows, pipes, yaml keys) "
                   "EXACTLY as-is. Output ONLY the translated block.")
    else:
        sys_msg = ("You are a professional translator. Translate the user's text into " +
                   ("Chinese (简体中文)" if lang == "zh" else "English") +
                   ". Output ONLY the translation. If the input has multiple lines, "
                   "keep the same number of lines and preserve any markdown formatting "
                   "(headings, list markers, table pipes) in the translation.")
    payload = {
        "model": "local",
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": text},
        ],
        "temperature": 0.1,
        "max_tokens": min(4096, max(512, len(text) * 2 + 256)),
    }
    try:
        r = requests.post(f"http://127.0.0.1:{port}/v1/chat/completions",
                          json=payload, timeout=300)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"    ! 单条翻译失败: {e}")
        return None


def should_skip(text: str) -> bool:
    t = text.strip()
    if not t or len(t) < 2:
        return True
    return bool(SKIP_RE.match(t))


# ---------- docx / pptx ----------

W_TEXT = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"
A_TEXT = "{http://schemas.openxmlformats.org/drawingml/2006/main}t"

# 需要翻译的 XML 路径模式（按文件类型）
DOCX_TARGETS = ["word/document.xml", "word/header", "word/footer"]
PPTX_TARGETS = ["ppt/slides/slide", "ppt/notesSlides/notesSlide"]


def _is_target(name: str, targets: list) -> bool:
    return any(name.startswith(t) for t in targets)


def _collect_units(root, text_tag):
    """收集翻译单元: 返回 [(element, parent_p), texts...] 结构。

    策略: 按段落(p)合并其下所有文本节点为一条，翻译后回填第一个节点，
    其余节点清空(保留 run 结构)。
    """
    units = []  # (paragraph_element, [text_elements])
    if text_tag == W_TEXT:
        p_tag = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
    else:
        p_tag = "{http://schemas.openxmlformats.org/drawingml/2006/main}p"
    for p in root.iter(p_tag):
        texts = p.findall(f".//{text_tag}")
        if texts:
            units.append((p, texts))
    return units


def process_office(path: Path, out_dir: Path, port: int, lang: str,
                   model: str, batch_size: int) -> Path:
    """解包 docx/pptx -> 翻译 -> 回填 -> 重新打包。"""
    is_docx = path.suffix.lower() == ".docx"
    targets = DOCX_TARGETS if is_docx else PPTX_TARGETS
    text_tag = W_TEXT if is_docx else A_TEXT
    out_path = out_dir / f"{path.stem}_zh{path.suffix}"

    # 全部读入内存: name -> (bytes 或 lxml root)
    entries = {}
    order = []
    with zipfile.ZipFile(path) as zin:
        for n in zin.namelist():
            order.append(n)
            if _is_target(n, targets) and n.endswith(".xml"):
                entries[n] = etree.fromstring(zin.read(n))
            else:
                entries[n] = zin.read(n)

    # 收集全部翻译单元（保持文档顺序）
    all_units = []  # (xml_name, p, [text_elems])
    for n, data in entries.items():
        if not isinstance(data, etree._Element):
            continue
        for p, texts in _collect_units(data, text_tag):
            all_units.append((n, p, texts))

    # 汇总文本（跳过无意义片段）
    units_text = []
    for n, p, texts in all_units:
        joined = "".join(t.text or "" for t in texts).strip()
        if should_skip(joined):
            continue
        units_text.append((n, p, texts, joined))

    print(f"[{path.name}] 提取 {len(units_text)} 个翻译单元")
    if not units_text:
        print(f"[{path.name}] 无可翻译文本，跳过")
        return out_path

    raw_texts = [u[3] for u in units_text]
    translated = translate_all(raw_texts, port, lang, model, batch_size)

    # 回填
    filled = 0
    for (n, p, texts, _orig), tr in zip(units_text, translated):
        if tr is None:
            continue
        texts[0].text = tr
        for extra in texts[1:]:
            extra.text = None  # 保留标签结构，清空文本
        filled += 1

    # 重新打包（保持条目顺序）
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in order:
            data = entries[n]
            if isinstance(data, etree._Element):
                data = etree.tostring(data, xml_declaration=True,
                                      encoding="UTF-8", standalone=True)
            zout.writestr(n, data)
    print(f"[{path.name}] 完成 -> {out_path}（回填 {filled} 条）")
    return out_path


# ---------- PDF ----------

def process_pdf(path: Path, out_dir: Path, port: int, lang: str,
                model: str, batch_size: int) -> Path:
    out_path = out_dir / f"{path.stem}_zh.pdf"
    doc = fitz.open(path)
    units = []  # (page_index, bbox, text)
    for pno in range(doc.page_count):
        page = doc[pno]
        d = page.get_text("dict")
        for block in d.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                text = "".join(s.get("text", "") for s in line.get("spans", [])).strip()
                if should_skip(text):
                    continue
                units.append((pno, fitz.Rect(line["bbox"]), text))
    print(f"[{path.name}] 提取 {len(units)} 行文本")
    if not units:
        sys.exit(f"[错误] {path.name} 无可提取文本（可能是扫描件/图片 PDF，不支持）")

    raw_texts = [u[2] for u in units]
    translated = translate_all(raw_texts, port, lang, model, batch_size)

    # 叠加译文
    for (pno, bbox, _orig), tr in zip(units, translated):
        if tr is None:
            continue
        page = doc[pno]
        fs = max(6.0, bbox.height * 0.8)
        color = (0.0, 0.35, 0.7)
        y = bbox.y1 + fs * 0.9
        if y > page.rect.height - 10:
            y = page.rect.height - 10
        page.insert_text((bbox.x0, y), tr, fontsize=fs, color=color,
                         fontname="china-s")
    doc.save(out_path)
    doc.close()
    print(f"[{path.name}] 完成 -> {out_path}")
    return out_path


# ---------- 纯文本 / Markdown ----------

def process_text(path: Path, out_dir: Path, port: int, lang: str,
                 model: str, batch_size: int) -> Path:
    """md/txt: 代码块原样保留，正文段落分块翻译，写回原文结构。"""
    suffix = "_en" if lang == "en" else "_zh"
    out_path = out_dir / f"{path.stem}{suffix}{path.suffix}"
    lines = path.read_text(encoding="utf-8").splitlines()

    units = []  # ("code", [lines]) | ("text", [lines]) | ("code_text", [lines])
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            block = lines[i:j + 1]  # 含结束围栏
            # 代码块内含人类语言（非 ASCII）则也翻译，保留代码结构
            has_human = any(ord(c) > 127 for ln in block for c in ln)
            units.append(("code_text" if has_human else "code", block))
            i = j + 1
            continue
        if not line.strip():
            i += 1
            continue
        j = i
        while j < len(lines) and lines[j].strip():
            j += 1
        units.append(("text", lines[i:j]))
        i = j

    text_units = [u for u in units if u[0] in ("text", "code_text")]
    print(f"[{path.name}] {len(units)} 块（正文 {len(text_units)}，代码 {len(units)-len(text_units)}）")
    if not text_units:
        print(f"[{path.name}] 无可翻译内容，跳过")
        return out_path

    # 段落块作为翻译单元（块内多行用 \n 连接）
    # 单行单元走批量协议（快、可校验）；多行单元逐条发送（避免编号破坏内部换行）
    def block_text(u):
        return "\n".join(u[1])

    translated = [None] * len(text_units)
    single_idxs = [i for i, u in enumerate(text_units) if "\n" not in block_text(u)]
    multi_idxs = [i for i, u in enumerate(text_units) if "\n" in block_text(u)]

    for start in range(0, len(single_idxs), batch_size):
        chunk = single_idxs[start:start + batch_size]
        texts = [block_text(text_units[i]) for i in chunk]
        out = translate_batch(texts, port, lang, model)
        if out is None:
            for j, k in enumerate(chunk):
                one = translate_batch([texts[j]], port, lang, model)
                translated[k] = one[0] if one else None
        else:
            for j, k in enumerate(chunk):
                translated[k] = out[j]
        print(f"    [单行 {len(single_idxs)}/{len(single_idxs)}]")

    for i in multi_idxs:
        is_code = text_units[i][0] == "code_text"
        tr = translate_single(block_text(text_units[i]), port, lang, model,
                              code_mode=is_code)
        translated[i] = tr
        print(f"    [多行块 {multi_idxs.index(i)+1}/{len(multi_idxs)}]{' (代码)' if is_code else ''}")

    # 回填
    ti = 0
    out_lines = []
    for kind, content in units:
        if kind == "code":
            out_lines.extend(content)
        else:
            tr = translated[ti]
            ti += 1
            if tr is None:
                out_lines.extend(content)
            else:
                out_lines.extend(tr.splitlines() if tr else content)
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"[{path.name}] 完成 -> {out_path}")
    return out_path


# ---------- 主流程 ----------

def main():
    ap = argparse.ArgumentParser(description="离线文档翻译 (docx/pptx/pdf)")
    ap.add_argument("input", nargs="?", help="文件(.docx/.pptx/.pdf)或目录（--text 模式下可省略）")
    ap.add_argument("--text", default=None, help="直接翻译命令行文本（而非文件），输出到 stdout")
    ap.add_argument("-o", "--out", default=None, help="输出目录（默认同输入目录）")
    ap.add_argument("--model", choices=MODELS.keys(), default=None,
                    help="指定模型（与 --mode 二选一）")
    ap.add_argument("--mode", choices=MODE_MODELS.keys(), default=None,
                    help="速度/质量档位: fast / balanced / quality")
    ap.add_argument("--lang", choices=["zh", "en"], default="zh",
                    help="目标语言（默认 zh）")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--no-server", action="store_true", help="不自动启动 llama-server")
    ap.add_argument("--batch", type=int, default=10, help="每批翻译条数")
    args = ap.parse_args()

    # 模型选择: --mode > 交互式 > 默认
    if args.model and args.mode:
        sys.exit("[错误] --model 和 --mode 不能同时指定")
    if not args.model:
        if args.mode:
            args.model = MODE_MODELS[args.mode]
            print(f"[模式] {args.mode} -> {MODE_MODELS[args.mode]}")
        elif sys.stdin.isatty():
            print("选择翻译模式:")
            for k, v in MODE_HINTS.items():
                print(f"  {k:<9} {v}")
            choice = input("输入档位 (fast/balanced/quality，回车默认 balanced): ").strip().lower()
            args.model = MODE_MODELS.get(choice, MODE_MODELS["balanced"])
        else:
            args.model = MODE_MODELS["balanced"]

    # 纯文本直翻（--text）：翻译单段文本到 stdout，复用 translate_single
    if args.text is not None:
        server_proc = ensure_server(args.port, args.model, args.no_server)
        try:
            tr = translate_single(args.text, args.port, args.lang, args.model)
            print(tr if tr else "[错误] 翻译失败")
        finally:
            shutdown_server(server_proc)
        return

    if args.input is None:
        sys.exit("[错误] 需要指定 input 文件/目录，或用 --text 直接翻译文本")

    inp = Path(args.input)
    if not inp.exists():
        sys.exit(f"[错误] 输入不存在: {inp}")

    out_dir = Path(args.out) if args.out else (inp.parent if inp.is_file() else inp / "_zh_out")
    out_dir.mkdir(parents=True, exist_ok=True)

    server_proc = ensure_server(args.port, args.model, args.no_server)
    try:
        files = [inp] if inp.is_file() else sorted(
            p for p in inp.iterdir()
            if p.suffix.lower() in (".docx", ".pptx", ".pdf", ".md", ".txt"))
        if not files:
            sys.exit("[错误] 没有找到 docx/pptx/pdf/md/txt 文件")

        print(f"[任务] {len(files)} 个文件，目标语言 {'中文' if args.lang=='zh' else '英文'}"
              f"，模型 {args.model}，输出 {out_dir}")
        for f in files:
            try:
                if f.suffix.lower() in (".docx", ".pptx"):
                    process_office(f, out_dir, args.port, args.lang, args.model, args.batch)
                elif f.suffix.lower() == ".pdf":
                    process_pdf(f, out_dir, args.port, args.lang, args.model, args.batch)
                elif f.suffix.lower() in (".md", ".txt"):
                    process_text(f, out_dir, args.port, args.lang, args.model, args.batch)
            except Exception as e:
                print(f"[错误] {f.name}: {e}")
        print(f"[完成] 输出目录: {out_dir}")
    finally:
        shutdown_server(server_proc)


if __name__ == "__main__":
    main()
