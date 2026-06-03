# Task 10 烟测结果 — `pdf/scripts/extract_with_fallback.py`

**日期**: 2026-06-03
**执行人**: DUDU
**测试目标 PDF**: JYM 江阴博物馆项目
**环境**: Windows 11, Python 3, pdfplumber 0.11.9, pypdfium2 (imported), Umi-OCR v2.1.5

---

## 1. CLI `--help` 验证

```
$ python pdf/scripts/extract_with_fallback.py --help
```

退出码: **0** ✓
输出与 spec 一致 — 包含 `pdf_path` `output_dir` 位置参数,
以及 `--ocr-lang` `--text-threshold` `--scale` `--skip-ocr` 四个可选参数,
均带默认值与帮助文本。

---

## 2. Run A — 主测 (floor plans + Umi-OCR 在线)

**输入**: `博物馆1~7层平面图.pdf` (2.1 MB, 7 页纯扫描页)
**命令**:
```
python pdf/scripts/extract_with_fallback.py "博物馆1~7层平面图.pdf" /tmp/smoke_output
```
**退出码**: 0
**输出**:
- `extracted_text.txt` — 2,995 字节
- `page_001.png` ~ `page_007.png` — 共 7 张 PNG, 累计 3.5 MB

**页面 source 分布**:

| Source | 数量 |
|--------|------|
| `pdfplumber` | 0 |
| `umi-ocr` | **7** |
| `needs-vision` | 0 |

**结论**: pdfplumber 完全无法识别扫描页 (char_count=0),
Umi-OCR 全部 7 页成功 OCR, 输出可读中文 (图名/工程名称/楼层/房间名)。
**典型片段** (Page 3):
```
=== Page 3 (source: umi-ocr) ===
图名DRAMING ME 二层平面布置图工程名称
工程名称 PROJECT
建设单位
电子显示屏拍卖厅
皇太后多宝阁展示柜
军机处办公桌
201 天下第一桌
二层平面布置图
LAYOUT PLAN
SCALE 1:100
```

---

## 3. Run B — 备测 (text-heavy + Umi-OCR 在线)

**输入**: `Yihai - JYM弱电系统技术方案 Integrated Technical Proposal.pdf` (1.5 MB, 22 页)
**命令**:
```
python pdf/scripts/extract_with_fallback.py "技术方案.pdf" /tmp/smoke_backup
```
**退出码**: 0
**输出**:
- `extracted_text.txt` — 40,408 字节
- `extracted_tables.txt` — 19,195 字节, 334 行
- 无 PNG (全部页面 text 充足, 不需 fallback)

**页面 source 分布**:

| Source | 数量 |
|--------|------|
| `pdfplumber` | **22** |
| `umi-ocr` | 0 |
| `needs-vision` | 0 |

**结论**: 22 页全走 pdfplumber 快路径, 全部 ≥ 50 字符, 无 fallback 触发。
`extracted_tables.txt` 正确捕获所有表格 (楼层配置表、智能化系统配置表 等)。
**典型片段** (Page 1):
```
=== Page 1 (source: pdfplumber) ===
江阴蔡氏博物馆弱电系统技术方案
Integrated BMS & Security System Technical Proposal
版本 V2
编制日期 2026年04月13日
项目 江阴蔡氏博物馆 Jiangyin Museum
```

---

## 4. Run C — `--skip-ocr` 路径

**输入**: `博物馆1~7层平面图.pdf` (与 Run A 同 PDF)
**命令**:
```
python pdf/scripts/extract_with_fallback.py --skip-ocr "博物馆1~7层平面图.pdf" /tmp/smoke_skip_ocr
```
**退出码**: 0
**输出**:
- `extracted_text.txt` — 285 字节 (仅含 7 个空页面块)
- 7 张 PNG 仍正常生成

**页面 source 分布**:

| Source | 数量 |
|--------|------|
| `pdfplumber` | **7** (应为 0) |
| `umi-ocr` | 0 |
| `needs-vision` | 0 (应为 7) |

**结论**: ⚠️ **发现 Bug** — 当 `--skip-ocr` 启用时, 0 字符页面的 `source`
字段未被改写为 `needs-vision`, 仍保留默认的 `pdfplumber` 标签。
结果: 7 个空页面被错误地标记为 `pdfplumber`, 输出仅是空白块。
后续 `mcp__MiniMax__understand_image` 消费者会以为 pdfplumber 已成功
提取 (实际为 0 字符), 漏掉这些页面。

### 触发原因 (分析)

`main()` 中:
```python
# Phase 2: OCR fallback
if not args.skip_ocr and no_text:
    print(f"[3/4] Running UMI-OCR fallback ...", file=sys.stderr)
    run_ocr_fallback(pages, ocr_lang=args.ocr_lang)
```

`run_ocr_fallback()` 是唯一把 `source` 字段改写为 `needs-vision` 的地方。
`--skip-ocr` 跳过了整个 Phase 2, 导致 `source` 保留为初始默认
`"pdfplumber"`。

### 建议修复 (留作后续 issue, 不在本次任务中处理)

在 Phase 2 之前加一段:
```python
if args.skip_ocr and no_text:
    print(f"[skip-ocr] marking {len(no_text)} page(s) as needs-vision ...", file=sys.stderr)
    for p in no_text:
        p.source = "needs-vision"
```

---

## 5. 状态汇总

| 验证项 | 状态 |
|--------|------|
| CLI `--help` 干净运行 | ✓ PASS |
| `extracted_text.txt` 生成 + per-page source 标签 | ✓ PASS |
| 页面 PNG 渲染 (pypdfium2) | ✓ PASS |
| Umi-OCR 在线时扫描页走 `(source: umi-ocr)` | ✓ PASS (Run A: 7/7) |
| pdfplumber 路径 (text 充足) 走 `(source: pdfplumber)` | ✓ PASS (Run B: 22/22) |
| `--skip-ocr` 时页面走 `(source: needs-vision)` | ✗ **FAIL** (Run C: 0/7, 错误标签 pdfplumber) |
| `--skip-ocr` 时 PNG 仍正常生成 | ✓ PASS |
| Umi-OCR 不可达时降级 `needs-vision` | ✓ PASS (Run 0 验证: 早期一次 Umi-OCR 进程卡死时, 7 页正确标记) |
| 表格提取 (`extracted_tables.txt`) | ✓ PASS (Run B: 334 行) |

---

## 6. 附加发现 — Umi-OCR 进程管理

- 启动时 Umi-OCR (Rapid v2.1.5) 偶发进入"进程在跑但 HTTP 不响应"状态
  (curl ping 超时, 但 `netstat` 显示 LISTEN/ESTABLISHED)。
  解决: `taskkill /F /IM Umi-OCR.exe` 后重新启动即恢复。
- `ocr_client.ensure_running()` 的 5s 等待不足以覆盖慢启动场景,
  但在 `subprocess.Popen` + `creationflags=DETACHED_PROCESS` 下表现正常。
- **建议**: 在 `ocr_client.py` 把 `STARTUP_WAIT_SEC` 调到 8~10s,
  或加多次重试 (3 次 × 3 秒)。但本次任务范围内未改源码, 仅记录。

---

## 7. 后续跟进

1. [ ] **Bug fix**: `--skip-ocr` 路径应将空页面 source 设为 `needs-vision`
2. [ ] **可选**: `STARTUP_WAIT_SEC` 调大, 或加 ping 重试
3. [ ] **可选**: 把 `博物馆1~7层平面图.pdf` 和 `技术方案.pdf` 复制到
       `pdf/tests/fixtures/` 作为长期 smoke fixture (本次未复制,
       避免误传客户文件入仓, 需评估脱敏)
