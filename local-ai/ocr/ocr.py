#!/usr/bin/env python3
"""Unlimited-OCR 本地推理 —— 扫描件 / 复杂版面 / 公式表格 / 长文档。

为什么单独一个栈（不走 llama-server）:
    Unlimited-OCR 是 DeepseekV2-style MoE + 自定义建模代码（trust_remote_code），
    llama.cpp 不认这个架构，只能走 transformers。

显存: 权重是 bf16 单文件约 6.7GB，本机可用约 6.9GB —— **贴边**。
      所以 run.sh 会先 stop.sh 腾显存。跑完不常驻，不占着卡。

用法:
    bash run.sh --pdf 合同.pdf --out ./out/
    bash run.sh --image 扫描件.png --out ./out/
    bash run.sh --pdf 长文档.pdf --out ./out/ --dpi 200
"""
import argparse
import json
import os
import sys
import tempfile
import time

MODEL_DIR = os.environ.get("UNLIMITED_OCR_DIR", "D:/models/unlimited-ocr")


def _report(out_dir: str, src: str, pages: int, results: list, elapsed: float) -> str:
    """同 llama_batch.py 的回执格式 —— 主模型只读这一份就够。"""
    path = os.path.join(out_dir, "ocr.report.md")
    ok = [r for r in results if r.get("error") is None]
    bad = [r for r in results if r.get("error") is not None]
    lines = [
        "# OCR 回执",
        "",
        f"- 生成：{time.strftime('%Y-%m-%d %H:%M')}",
        f"- 输入：{src}（{pages} 页）",
        f"- 输出目录：{out_dir}",
        f"- 模型：baidu/Unlimited-OCR (bf16, 本地 {MODEL_DIR})",
        f"- 耗时：{elapsed:.1f}s",
        "",
        "## 计数",
        "",
        f"总 **{len(results)}** ｜ 成功 {len(ok)} ｜ 失败 **{len(bad)}**",
        "",
        "## 异常清单",
        "",
    ]
    if not bad:
        lines.append("无。")
    else:
        lines += ["| 页 | 错误 |", "| --- | --- |"]
        for r in bad:
            lines.append(f"| {r['page']} | {r['error']} |")
    lines += ["", "## 输出文件", ""]
    for r in ok:
        lines.append(f"- 第 {r['page']} 页 → `{os.path.basename(r['output'])}`")
    lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def pdf_to_images(pdf_path: str, dpi: int) -> list:
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    tmp_dir = tempfile.mkdtemp(prefix="ocr_pdf_")
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    paths = []
    for i, page in enumerate(doc):
        out = os.path.join(tmp_dir, f"page_{i + 1:04d}.png")
        page.get_pixmap(matrix=mat).save(out)
        paths.append(out)
    doc.close()
    return paths


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="Unlimited-OCR 本地推理（transformers / CUDA）")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--pdf", help="PDF 路径（逐页转图后解析）")
    src.add_argument("--image", help="单张图片路径")
    ap.add_argument("--out", required=True, help="输出目录（markdown 与回执写在这里）")
    ap.add_argument("--dpi", type=int, default=300, help="PDF 转图 DPI（默认 300）")
    ap.add_argument("--max-length", type=int, default=32768, help="单次生成上限")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # 延迟导入：让 --help 不必加载 torch（几秒起步）
    import torch
    from transformers import AutoModel, AutoTokenizer

    if not torch.cuda.is_available():
        sys.exit("[错误] CUDA 不可用 —— OCR 会在 CPU 上慢到不可用。"
                 "检查 torch 是否为 cu129 版："
                 "D:/models/venvs/unlimited-ocr/Scripts/python.exe -c "
                 "\"import torch; print(torch.__version__, torch.cuda.is_available())\"")

    print(f"[加载] {MODEL_DIR} …", file=sys.stderr)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        MODEL_DIR,
        trust_remote_code=True,
        use_safetensors=True,
        torch_dtype=torch.bfloat16,
    )
    model = model.eval().cuda()
    print("[加载] 完成", file=sys.stderr)

    t0 = time.time()
    results = []

    if args.image:
        out_path = os.path.join(args.out, os.path.splitext(os.path.basename(args.image))[0])
        try:
            model.infer(
                tokenizer,
                prompt="<image>document parsing.",
                image_file=args.image,
                output_path=out_path,
                base_size=1024, image_size=640, crop_mode=True,
                max_length=args.max_length,
                no_repeat_ngram_size=35, ngram_window=128,
                save_results=True,
            )
            results.append({"page": 1, "output": out_path, "error": None})
        except Exception as e:
            results.append({"page": 1, "output": None, "error": f"{type(e).__name__}: {e}"})
        total_pages = 1
    else:
        pages = pdf_to_images(args.pdf, args.dpi)
        total_pages = len(pages)
        print(f"[PDF] {total_pages} 页已转图", file=sys.stderr)
        # 逐页单独推理：整本 infer_multi 会一次性占满显存，8GB 上风险太高
        for idx, page_png in enumerate(pages, 1):
            out_path = os.path.join(args.out, f"page_{idx:04d}")
            print(f"  [{idx}/{total_pages}] {os.path.basename(page_png)}", file=sys.stderr)
            try:
                model.infer(
                    tokenizer,
                    prompt="<image>document parsing.",
                    image_file=page_png,
                    output_path=out_path,
                    base_size=1024, image_size=1024, crop_mode=False,
                    max_length=args.max_length,
                    no_repeat_ngram_size=35, ngram_window=1024,
                    save_results=True,
                )
                results.append({"page": idx, "output": out_path, "error": None})
            except Exception as e:
                # 单页失败不中断整本 —— 与 llama_batch.py 的容错策略一致
                results.append({"page": idx, "output": None,
                                "error": f"{type(e).__name__}: {e}"})

    report = _report(args.out, args.pdf or args.image, total_pages, results, time.time() - t0)
    print(f"[完成] 回执 → {report}", file=sys.stderr)


if __name__ == "__main__":
    main()
