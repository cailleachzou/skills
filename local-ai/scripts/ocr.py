#!/usr/bin/env python3
"""OCR 文字提取 —— Intel NPU（docling + rapidocr PP-OCR）。

包装 Desktop 上的 docling_npu.py（NPU 编译与 rapidocr 补丁固化在 venv-docling 里），
统一入口，参数原样转发。不依赖 Ollama 服务。

用法:
    py -3 ocr.py <图片或PDF路径> [-o 输出.md] [--cpu]

参数:
    图片/PDF路径     必填；图片(jpg/png)或 PDF（含扫描件）
    -o 输出.md       可选，结果写入文件；默认打印到终端
    --cpu            可选，用 OpenVINO CPU 而非 NPU（对比精度用）

实测: 中文文字图 6.6s（NPU）；小模型对长数字末尾偶有丢失（如 12345→1234）。
"""
import subprocess
import sys

VENV_PY = r"C:\Users\caill\.venv-docling\Scripts\python.exe"
DOCLING_NPU = r"C:\Users\caill\Desktop\docling_npu.py"


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(subprocess.call([VENV_PY, DOCLING_NPU] + sys.argv[1:]))


if __name__ == "__main__":
    main()
