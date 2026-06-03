# PDF Skill — OCR/MCP Fallback Chain Design

**Date:** 2026-06-03
**Status:** Draft (awaiting user review)
**Owner:** DUDU & Cailleach
**Affects:** `pdf/` skill

## 背景

当前 `pdf` skill 的 "AI 视觉审图" 流程是手动的三步（文字提取 → 导图 → MCP 视觉复核），且 UMI-OCR 完全是独立 skill，没接入 PDF 处理流。遇到扫描件、纯图 PDF、混排图纸时，Claude 不知道什么时候该停下来调 OCR、什么时候该直接调 MCP。

## 目标

把"抽文字失败时调 OCR、OCR 失败时调 MCP"做成自动 fallback 链，写成 SKILL 默认行为，调用方无感。

## 非目标

- 不重写 `pdf` skill 的所有功能（合并/拆分/旋转/水印/表单等不动）
- 不动 `umi-ocr` skill 本体（只调它的 HTTP API）
- 不引入新 Python 依赖（pdfplumber + pypdfium2 + stdlib 足够）
- 不在脚本里塞 Anthropic API key（vision 步骤交给 Claude 在主会话里调）

## 触发条件

**逐页判定。** 每页用 pdfplumber 抽文字，字符数 < 阈值（默认 50）即标记为"无文字页"，对该页触发 fallback。混合 PDF 不会浪费算力。

## Fallback 链

```
PDF → pdfplumber 逐页抽文
        ↓
   [text-pages] + [no-text-pages]
                    ↓
            no-text 页导出 PNG
                    ↓
            UMI-OCR HTTP API 逐页 OCR
                    ↓
            [ocr-success] + [ocr-fail]
                              ↓
                   ocr-fail 写入 "needs-vision" 占位
                              ↓
                  Claude 读到占位 → 调 mcp__MiniMax__understand_image
                              ↓
                  Claude 把 vision 结果回写到 extracted_text.txt
```

## 组件

### `scripts/extract_with_fallback.py`（替换现有 `extract_and_prompt.py`）

CLI：
```bash
python scripts/extract_with_fallback.py <input.pdf> <output_dir> \
    [--ocr-lang 简体中文] [--text-threshold 50] [--scale 2.0]
```

内部结构（4 个内聚类 + 1 个 main）：

| 类 | 职责 |
|---|---|
| `TextExtractor` | Phase 1：用 pdfplumber 逐页抽文，返回 `[(page_num, text, char_count), ...]` |
| `OCRFallback` | Phase 2：UMI-OCR HTTP 客户端（urllib + base64 stdlib），负责启动检测 + 调用 + 重试 |
| `VisionMarker` | Phase 3：对 OCR 也失败的页写 `=== Page N (source: needs-vision) ===` 占位 |
| `OutputMerger` | 装配 `extracted_text.txt`，按页顺序插入来源标签 |

`main()` 串起三步 Phase + 最终输出装配，任一步失败不阻断下一步（OCR 失败 → 进 `needs-vision`；vision 由 Claude 离线做）。

### `SKILL.md` 更新

修改 "AI 视觉审图" 章节：

1. **替换脚本名**：所有 `extract_and_prompt.py` 引用改为 `extract_with_fallback.py`
2. **加 fallback 决策树小节**：
   - 正常 PDF：脚本搞定，无需 MCP
   - 扫描件 PDF：脚本调 UMI-OCR，Claude 看到 `(source: umi-ocr)` 标签
   - 复杂图/拓扑图：脚本写 `needs-vision` 占位，Claude 调 MCP 处理
3. **加 MCP 调用模板**：直接用现有 `review_prompt.md` 模板，针对 `needs-vision` 标记的页生成语义理解 prompt
4. **加回写指引**：Claude 拿到 vision 结果后，正则匹配 `=== Page N (source: needs-vision) ===` 块，原地替换为 vision 输出

## 输出契约

`<output_dir>/` 下生成：

| 文件 | 内容 |
|---|---|
| `page_NNN.png` | 每页导出的 PNG（OCR 和 vision 共用，scale 默认 2.0） |
| `extracted_text.txt` | 合并结果，每页带来源标签 |
| `extracted_tables.txt` | 表格单独一份（沿用旧逻辑） |

`extracted_text.txt` 格式示例：
```
=== Page 1 (source: pdfplumber) ===
[正文文字内容...]

=== Page 2 (source: umi-ocr) ===
[OCR 抽出的文字...]

=== Page 3 (source: needs-vision) ===
[image: page_003.png — please run mcp__MiniMax__understand_image for semantic understanding]
```

## 错误处理

| 场景 | 行为 |
|---|---|
| Umi-OCR 未启动 | 脚本自动拉起 `Umi-OCR.exe &`，等 5s 重试一次 |
| Umi-OCR HTTP 仍不通 | 把无 OCR 页全部 mark `needs-vision`，stderr 警告 |
| Umi-OCR 返回空文本 | 同上，mark `needs-vision` |
| 单页 pdfplumber 抽不到 | 当 no-text 走 OCR |
| `--ocr-lang` 超出 Umi-OCR 支持 | 退回 `简体中文`，stderr 警告 |
| PDF 加密/损坏 | 启动时检测，stderr 报错退出，不留半成品 |

原则：**任何步骤失败都不阻断流程**，最多让 Claude 走 MCP 兜底。

## 测试

### evals（`pdf/evals/evals.json`）3 个 case：

1. **全文字 PDF** — 验证 pdfplumber 抽得到时，OCR/vision 不被调用（输出纯 `(source: pdfplumber)` 标签）
2. **扫描件 PDF** — 验证无文字页走 UMI-OCR，结果写入 `(source: umi-ocr)`
3. **混合 PDF**（部分有字部分扫描）— 验证逐页判定正确，混合格式对齐

### 手工 smoke test：

- 用 Tendo 真实项目 PDF 跑一遍（江阴博物馆 / Cooley 任一），看 `extracted_text.txt` 顺序、标签、占位符是否都对
- 故意关 Umi-OCR 再跑一次，确认 `needs-vision` 标记全部正确写入

## 兼容性

- `extract_with_fallback.py` 保留 `extract_and_prompt.py` 的 CLI 签名（`<input.pdf> <output_dir>`），其他引用无需改
- 旧脚本如果被外部代码直接引用，保留为兼容层（git history 里），不在新流程里

## 风险

| 风险 | 缓解 |
|---|---|
| Umi-OCR 启动慢（5-15s 冷启动模型加载） | 脚本启动时主动 ping + 自动拉起，给充分等待时间 |
| 大 PDF（100+ 页）逐页 OCR 慢 | Phase 2 只对 no-text 页触发；Tendo 场景典型 no-text 页 < 20%，可接受；可后续加并发（本期不做） |
| MCP vision 结果回写格式不一致 | SKILL.md 给出明确的正则替换规则和示例 |
| 旧 `extract_and_prompt.py` 用户路径中断 | 保留 git history，必要时回退 |
