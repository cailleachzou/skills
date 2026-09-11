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
    bash run.sh --image 图.png --out ./out/ --image-size 640   # 显存不够时降档
"""
import argparse
import contextlib
import os
import shutil
import sys
import tempfile
import time

# 见 _run_one：infer 会把识别正文写 stdout，推理期间一律重定向到这里
_DEVNULL = open(os.devnull, "w", encoding="utf-8")

MODEL_DIR = os.environ.get("UNLIMITED_OCR_DIR", "D:/models/unlimited-ocr")
VENV_DIR = os.environ.get("UNLIMITED_OCR_VENV", "D:/models/venvs/unlimited-ocr")

# 两种分辨率模式的出处（D:/models/unlimited-ocr/Unlimited-OCR.pdf §3.3）：
#   「DeepEncoder natively supports five resolution modes; we retain two of them:
#     the "Base" model (1024×1024 for multi-page), and the "Gundam" mode
#     (dynamic resolution for single-page).」
# 落到 infer() 的参数上是：
#   单页 Gundam = crop_mode=True  + image_size=640   （infer() 签名默认值；
#                 modeling_unlimitedocr.py:901 对 image_size==640 另有专门分支）
#   多页 Base   = crop_mode=False + image_size=1024
# ⚠️ ngram_window（单页 128 / 多页 1024）在建模代码与上游 PDF 里都找不到说明 ——
#    来源待核。数值沿用计划既定值，未经验证不擅自改。
NG_NGRAM_WINDOW_SINGLE = 128
NG_NGRAM_WINDOW_MULTI = 1024


def _positive_int(v: str) -> int:
    """--dpi/--image-size/--max-length 的正数校验。

    --dpi 0 会让 fitz.Matrix 退化成 0 倍缩放、整本白跑一趟，所以挡在参数层。
    """
    try:
        n = int(v)
    except ValueError:
        raise argparse.ArgumentTypeError(f"必须是整数，收到 {v!r}")
    if n <= 0:
        raise argparse.ArgumentTypeError(f"必须是正整数，收到 {v!r}")
    return n


def _model_label() -> str:
    """回执里报「真身」——MODEL_DIR 可被 UNLIMITED_OCR_DIR 覆盖，
    硬编码名字会让回执失真（同 llama_batch.py:_probe_model() 的教训）。"""
    return os.path.basename(MODEL_DIR.rstrip("/\\")) or MODEL_DIR


def _warn_if_exists(out_path: str) -> bool:
    """目标子目录已存在且非空 → 明确告警；返回「本次推理前该目录是否已存在」。

    一次调用只处理一张图，同一 --out 重跑本来是合法的重试路径，覆盖是预期行为，
    所以**只告警、不改命名**（加 -2 后缀反而会让人找不到自己的结果）。

    返回值供 _cleanup_failed_dir 判断「这目录是不是我们新建的」——
    用户自建的目录不能连内容一起删。判据**必须在这里取**（infer 之前）：
    失败之后再问「目录存在吗」必然为真，判不出是谁建的。
    """
    preexisting = os.path.isdir(out_path)
    if preexisting and os.listdir(out_path):
        print(f"[警告] {out_path} 已存在且非空 —— 其中的旧产物将被覆盖", file=sys.stderr)
    return preexisting


def _cleanup_failed_dir(out_path: str, preexisting: bool) -> bool:
    """清理失败页留下的空壳目录。返回是否**未清理**（即可能残留空壳）。

    只清本次运行新建的目录。用户完全可能事先在 <out>/ 下建了同名目录放了别的
    东西 —— 那种目录一律不动：_warn_if_exists 的告警说的是「旧产物会被覆盖」，
    用户读不出「我会把整个目录连内容删掉」这层意思，删了就是数据丢失。
    """
    if preexisting:
        return True
    # 目录是我们新建的，整个删掉不会有误伤
    if os.path.isdir(out_path):
        shutil.rmtree(out_path, ignore_errors=True)
    return False


def _report(out_dir: str, src: str, pages: int, results: list, elapsed: float,
            fatal: str = None) -> str:
    """同 llama_batch.py 的回执格式 —— 主模型只读这一份就够。

    fatal 是**文档级**失败（打不开 / 0 页），与「某页失败」不是一回事：
    它不该伪装成一页，否则回执会自相矛盾（「输入（0 页）」与「总 1 ｜ 失败 1」并排）。
    """
    path = os.path.join(out_dir, "ocr.report.md")
    ok = [r for r in results if r.get("error") is None]
    bad = [r for r in results if r.get("error") is not None]
    empt = [r for r in ok if r.get("empty")]
    leftover = [r for r in bad if r.get("leftover")]
    lines = [
        "# OCR 回执",
        "",
        f"- 生成：{time.strftime('%Y-%m-%d %H:%M')}",
        f"- 输入：{src}（{pages} 页）",
        f"- 输出目录：{out_dir}",
        f"- 模型：{_model_label()} (bf16, 本地 {MODEL_DIR})",
        f"- 耗时：{elapsed:.1f}s",
        "",
    ]
    if fatal:
        lines += [
            "## 文档级错误",
            "",
            fatal,
            "",
            "（文档未能打开 / 无页可处理，未执行任何页面推理）",
            "",
        ]
    lines += [
        "## 计数",
        "",
        f"总 **{len(results)}** ｜ 成功 {len(ok)} ｜ 失败 **{len(bad)}**"
        f" ｜ 空结果 {len(empt)}",
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
    if leftover:
        lines.append("")
        lines.append("注：" + "、".join(f"第 {r['page']} 页" for r in leftover)
                     + "的输出目录在本次运行前已存在，按「不删用户目录」原则未清理，"
                      "可能残留空壳目录。")
    lines += ["", "## 空结果清单", ""]
    if not empt:
        lines.append("无。")
    else:
        lines.append(f"共 **{len(empt)}** 页未识别出文字（空白页本就无字，不算失败）：")
        lines.append("")
        lines.append("　".join(f"第 {r['page']} 页" for r in empt))
    lines += ["", "## 输出文件", ""]
    for r in ok:
        lines.append(f"- 第 {r['page']} 页 → `{os.path.basename(r['output'])}/result.md`")
    lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def rasterize_pdf(pdf_path: str, dpi: int, tmp_dir: str) -> tuple:
    """逐页转图。返回 (总页数, {页号: png路径}, {页号: 错误}, 致命错误)。

    - 单页 get_pixmap 失败只记该页，**继续下一页** —— 转图与推理同属单页处理，
      容错范围必须一致，否则第 5 页损坏会让 1-4 页成果一起作废、连回执都拿不到。
    - fitz.open 本身失败（打不开 / 非 PDF）→ 致命错误交给调用方走回执，不裸 traceback。
    - doc.close() 走 finally，异常路径也不漏。
    """
    import fitz  # PyMuPDF
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return 0, {}, {}, f"{type(e).__name__}: {e}"

    paths, errors = {}, {}
    page_count = 0
    try:
        # page_count 必须在 close 之前读 —— close 之后再访问 doc.page_count 会
        # raise ValueError('document closed')
        page_count = doc.page_count
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        for i, page in enumerate(doc, 1):
            out = os.path.join(tmp_dir, f"page_{i:04d}.png")
            try:
                page.get_pixmap(matrix=mat).save(out)
                paths[i] = out
            except Exception as e:
                errors[i] = f"转图失败: {type(e).__name__}: {e}"
    finally:
        doc.close()
    return page_count, paths, errors, None


def _run_one(model, tokenizer, args, image_file: str, out_path: str, page,
             image_size: int, crop_mode: bool, ngram_window: int,
             preexisting: bool) -> dict:
    """跑一页，并把「infer 没抛错」升级成「产物确实存在」。

    infer() 返回不代表有产物：save_results=True 写的是 <out>/result.md。上游建模
    代码一旦改名，回执就会把**不存在的路径**指给主模型 —— 回执失真等于契约失效。

    preexisting 必须由调用方在 infer **之前**测好，再传进来（见 _warn_if_exists）。
    """
    try:
        # ⚠️ model.infer() 会把逐行识别结果（<|det|>… **含证件号、姓名等正文**）
        # 直接 print 到 stdout。识别结果已由 save_results=True 落到 result.md，
        # 所以这里吞掉不丢信息；不吞的代价是**任何读本进程 stdout 的调用方
        # 都会拿到证件正文** —— 主对话是外发的，实测踩过：批量驱动读 stdout
        # 只是想拿计数，把毕业证书正文一起读进了对话。
        with contextlib.redirect_stdout(_DEVNULL):
            model.infer(
                tokenizer,
                prompt="<image>document parsing.",
                image_file=image_file,
                output_path=out_path,
                base_size=1024,
                image_size=image_size,
                crop_mode=crop_mode,
                max_length=args.max_length,
                no_repeat_ngram_size=35, ngram_window=ngram_window,
                save_results=True,
            )
    except Exception as e:
        # 单页失败不中断整本 —— 与 llama_batch.py 的容错策略一致
        leftover = _cleanup_failed_dir(out_path, preexisting)
        return {"page": page, "output": None, "empty": False, "leftover": leftover,
                "error": f"{type(e).__name__}: {e}"}

    md = os.path.join(out_path, "result.md")
    if not os.path.exists(md):
        leftover = _cleanup_failed_dir(out_path, preexisting)
        return {"page": page, "output": None, "empty": False, "leftover": leftover,
                "error": f"产物缺失：未生成 {os.path.basename(out_path)}/result.md"}
    try:
        with open(md, encoding="utf-8") as f:
            empty = not f.read().strip()
    except Exception as e:
        return {"page": page, "output": None, "empty": False, "leftover": False,
                "error": f"产物不可读：{type(e).__name__}: {e}"}
    # 空白页本就无字 —— 归「空结果」一类，不算失败（照 llama_batch.py 的标签）
    return {"page": page, "output": out_path, "empty": empty, "leftover": False,
            "error": None}


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
    ap.add_argument("--dpi", type=_positive_int, default=300, help="PDF 转图 DPI（默认 300）")
    ap.add_argument("--max-length", type=_positive_int, default=32768, help="单次生成上限")
    ap.add_argument("--image-size", type=_positive_int, default=None,
                    help="显存不够时的降档旋钮：覆盖送入模型的图像边长（越小越省显存、"
                         "精度越低）。不传则 image 模式用 640、PDF 模式用 1024")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # PDF 模式先把 PyMuPDF 的可用性查掉：它的 import 原本在模型加载之后，
    # 缺包会先白加载 6.2GiB、吃满显存，再崩在一个 import 上。
    if args.pdf:
        try:
            import fitz  # noqa: F401
        except ImportError as e:
            sys.exit(f"[错误] PDF 模式需要 PyMuPDF，但导入失败：{type(e).__name__}: {e}\n"
                     f"       安装：{VENV_DIR}/Scripts/python.exe -m pip install pymupdf")

    # 延迟导入：让 --help 不必加载 torch（几秒起步）
    import torch
    from transformers import AutoModel, AutoTokenizer

    if not torch.cuda.is_available():
        sys.exit("[错误] CUDA 不可用 —— OCR 会在 CPU 上慢到不可用。"
                 "检查 torch 是否为 cu130 版："
                 f"{VENV_DIR}/Scripts/python.exe -c "
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
    tmp_dir = None
    try:
        if args.image:
            total_pages = 1
            out_path = os.path.join(args.out, os.path.splitext(os.path.basename(args.image))[0])
            # 必须在 infer 之前取 —— 失败后再问「目录存在吗」必然为真
            preexisting = _warn_if_exists(out_path)
            results.append(_run_one(
                model, tokenizer, args, args.image, out_path, page=1,
                # 单页 Gundam（见文件头出处注释）
                image_size=args.image_size if args.image_size is not None else 640,
                crop_mode=True, ngram_window=NG_NGRAM_WINDOW_SINGLE,
                preexisting=preexisting,
            ))
        else:
            tmp_dir = tempfile.mkdtemp(prefix="ocr_pdf_")
            page_count, page_paths, raster_errors, fatal = rasterize_pdf(
                args.pdf, args.dpi, tmp_dir)

            # 打不开 / 不是 PDF：给可读的中文错误，照常走回执路径，不裸 traceback。
            # 走 fatal= 而不是伪装成一页 —— 否则回执里「输入（0 页）」会和
            # 「总 1 ｜ 失败 1」并排，自相矛盾。
            if fatal is not None:
                report = _report(args.out, args.pdf, 0, [], time.time() - t0,
                                 fatal=f"无法打开 PDF：{fatal}")
                print(f"[错误] 无法打开 PDF：{fatal}", file=sys.stderr)
                print(f"[完成] 回执 → {report}（文档级错误，未处理任何页）", file=sys.stderr)
                sys.exit(1)

            # 0 页 PDF：别静默写出「总 0 ｜ 成功 0 ｜ 失败 0」再 exit 0
            # （照 llama_batch.py:107 的 `if not tasks: sys.exit(...)`）
            if page_count == 0:
                report = _report(args.out, args.pdf, 0, [], time.time() - t0,
                                 fatal="PDF 没有页：文件可能是空的或已损坏")
                print("[错误] PDF 没有页：文件可能是空的或已损坏", file=sys.stderr)
                print(f"[完成] 回执 → {report}（文档级错误，未处理任何页）", file=sys.stderr)
                sys.exit(1)

            total_pages = page_count
            print(f"[PDF] {page_count} 页（转图成功 {len(page_paths)}）", file=sys.stderr)
            # 逐页单独推理：整本 infer_multi 会一次性占满显存，8GB 上风险太高
            for idx in range(1, page_count + 1):
                if idx in raster_errors:
                    print(f"  [{idx}/{page_count}] {raster_errors[idx]}", file=sys.stderr)
                    results.append({"page": idx, "output": None, "empty": False,
                                    "leftover": False, "error": raster_errors[idx]})
                    continue
                page_png = page_paths.get(idx)
                if page_png is None:
                    # 既不在 paths 也不在 errors —— 只有 doc 迭代出的页数 !=
                    # doc.page_count 时才会走到这里。别用 page_paths[idx] 直接
                    # KeyError 崩在 _report() 之前（那又回到「连回执都拿不到」），
                    # 记一条 error 兜住，代价极小。
                    print(f"  [{idx}/{page_count}] 该页未参与转图（页数不一致）",
                          file=sys.stderr)
                    results.append({
                        "page": idx, "output": None, "empty": False, "leftover": False,
                        "error": "内部错误：该页未参与转图（doc 页数与 page_count 不一致）",
                    })
                    continue
                out_path = os.path.join(args.out, f"page_{idx:04d}")
                print(f"  [{idx}/{page_count}] {os.path.basename(page_png)}",
                      file=sys.stderr)
                # 必须在 infer 之前取 —— 失败后再问「目录存在吗」必然为真
                preexisting = _warn_if_exists(out_path)
                results.append(_run_one(
                    model, tokenizer, args, page_png, out_path, page=idx,
                    # 多页 Base（见文件头出处注释）
                    image_size=args.image_size if args.image_size is not None else 1024,
                    crop_mode=False, ngram_window=NG_NGRAM_WINDOW_MULTI,
                    preexisting=preexisting,
                ))

        report = _report(args.out, args.pdf or args.image, total_pages, results,
                         time.time() - t0)
        ok = [r for r in results if r.get("error") is None]
        bad = [r for r in results if r.get("error") is not None]
        print(f"[完成] 回执 → {report}（成功 {len(ok)} 失败 {len(bad)}）", file=sys.stderr)
        if bad and not ok:
            print("[提示] 全部失败：产物为空，原因见回执「异常清单」", file=sys.stderr)
            # 全部失败要交非零退出码 —— 别和「PDF 打不开」(:317)、「0 页」(:326)
            # 分裂成两种语义。回执已在上方落盘，这里只是补退出码。
            sys.exit(1)
        elif bad:
            print(f"[提示] {len(bad)} 页失败、{len(ok)} 页成功；"
                  f"原因见回执「异常清单」，修好后可只重跑这些页", file=sys.stderr)
    finally:
        # 转图临时目录：转完图、推理完，无论成败都清掉。
        # 不用 TemporaryDirectory 是因为它得包住整个推理过程，而那正是
        # 这里不想让它管的生命周期。
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
