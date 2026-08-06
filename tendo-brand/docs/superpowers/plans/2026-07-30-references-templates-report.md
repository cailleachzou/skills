# references/ 模板参考文档实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 根据 spec `2026-07-30-references-templates-design.md`，生成一份完整的 `references/` 模板参考文档，覆盖 7 个模板的结构化说明。

**Architecture:** 文档型任务，非代码任务。输出单一 Markdown 文件。两个二进制模板（Service Report.xlsx、Test Procedure.docx）需先解析结构，再填充到文档对应章节，最后替换所有"待解析/待确认"占位符。

**Tech Stack:** Markdown、openpyxl/xlsx 读取（或解包 docx 读 XML）、Tendo skill 仓库结构。

**Spec:** `docs/superpowers/specs/2026-07-30-references-templates-design.md`

---

### Task 1: 解析 Service Report.xlsx 结构

**Files:**
- Read: `references/Service Report.xlsx`
- Temp output: 解析结果记录到内存/草稿

- [ ] **Step 1: 用 openpyxl 读取 Service Report.xlsx 结构**

Run:
```bash
py -3 -c "import openpyxl; wb=openpyxl.load_workbook(r'references/Service Report.xlsx'); [print(f'Sheet: {s.title}, dims: {s.dimensions}, max_row={s.max_row}, max_col={s.max_column}') for s in wb.worksheets]"
```
Expected: 输出每个 sheet 的名称、维度、行列数。

- [ ] **Step 2: dump 每个 sheet 的非空单元格内容**

Run:
```bash
py -3 -c "
import openpyxl
wb=openpyxl.load_workbook(r'references/Service Report.xlsx')
for s in wb.worksheets:
    print(f'=== Sheet: {s.title} ===')
    for row in s.iter_rows():
        for c in row:
            if c.value is not None:
                print(f'{c.coordinate}: {repr(c.value)}')
"
```
Expected: 输出所有非空单元格的坐标和值，用于识别表头、字段区、合并单元格模式。

- [ ] **Step 3: 记录结构摘要**

整理出：
- sheet 数量和名称
- 每个 sheet 的区域划分（标题/表头/数据区/签字区）行范围
- 关键字段名清单
- 合并单元格范围
- 是否有公式

记录到草稿，供 Task 3 填充文档使用。

---

### Task 2: 解析 TendoCN - Test Procedure.docx 结构

**Files:**
- Read: `references/TendoCN - Test Procedure.docx`

- [ ] **Step 1: 用 python-docx 读取文档结构**

Run:
```bash
py -3 -c "import docx; print('ok')" 2>nul || py -3 -m pip install python-docx
```
Expected: 确认 python-docx 可用；若未安装则安装。

- [ ] **Step 2: dump 段落和表格结构**

Run:
```bash
py -3 -c "
import docx
d=docx.Document(r'references/TendoCN - Test Procedure.docx')
print('=== Paragraphs ===')
for i,p in enumerate(d.paragraphs):
    if p.text.strip():
        print(f'{i}: [{p.style.name}] {p.text}')
print('=== Tables ===')
for ti,t in enumerate(d.tables):
    print(f'--- Table {ti} ({len(t.rows)}x{len(t.columns)}) ---')
    for ri,row in enumerate(t.rows):
        cells=[c.text for c in row.cells]
        print(f'  row{ri}: {cells}')
"
```
Expected: 输出所有非空段落（含样式名）和所有表格的行列内容。

- [ ] **Step 3: 记录结构摘要**

整理出：
- 章节结构（标题层级）
- 表格清单（每个表的列头、行数、用途）
- 是否含签字区、测试项矩阵
- 页眉图标位置（确认 image2.jpg / image3.jpg 来源，与 SKILL.md 一致）

记录到草稿，供 Task 3 填充文档使用。

---

### Task 3: 填充 Service Report 和 Test Procedure 章节

**Files:**
- Modify: `docs/superpowers/specs/2026-07-30-references-templates-design.md` 的 4.6 和 4.7 节

- [ ] **Step 1: 用 Task 1 结果替换 4.6 节的占位符**

将 `### 4.6 Service Report.xlsx` 节中的：
- "用途"段的"待确认"
- "内部结构"段的"待解析"
- "关键字段"段的"待解析"

替换为 Task 1 解析得到的实际内容。保持 6 段结构（用途/文件信息/内部结构/对应 agent/关键字段/注意事项）。

- [ ] **Step 2: 用 Task 2 结果替换 4.7 节的占位符**

将 `### 4.7 Test Procedure.docx` 节中的：
- "用途"段的"待确认"
- "内部结构"段的"待解析"
- "关键字段"段的"待解析"

替换为 Task 2 解析得到的实际内容。保留"附加价值：页眉图标来源"说明。

- [ ] **Step 3: 检查文档无残留占位符**

Run: 在文档中搜索 "待解析"、"待确认"、"TBD"、"TODO"。
Expected: 无匹配（或仅在合理上下文中）。

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-07-30-references-templates-design.md
git commit -m "docs: 填充 Service Report 和 Test Procedure 模板结构"
```

---

### Task 4: 生成最终参考文档（从 spec 派生）

**Files:**
- Create: `docs/references-templates-guide.md`（skill 根目录 docs 下，作为长期参考文档）

**说明：** spec 文件是设计文档（Draft 状态），最终交付物应是一份独立的参考文档，去除 spec 特有的"设计决策"痕迹，保留纯参考内容。

- [ ] **Step 1: 基于 spec 内容创建最终文档**

读取 `docs/superpowers/specs/2026-07-30-references-templates-design.md`，派生为 `docs/references-templates-guide.md`：
- 标题改为 "Tendo references/ 模板参考文档"
- 去除 Date / Author / Status 头
- 去除第 5 节"覆盖缺口分析"和第 6 节"维护策略"（这些是 spec 专有，不属于参考文档）
- 保留第 1 节（概述，简化）、第 2 节（速查总表）、第 3 节（模板间关系）、第 4 节（7 个模板详解）、附录（非模板文件）
- 文档顶部加一行："> 维护说明：新增模板/agent 时同步更新本文档。SKILL.md 的 agents 触发表以 SKILL.md 为准。"

- [ ] **Step 2: 校验文档结构完整**

确认文档包含：
- 概述（目的、读者、范围）
- 速查总表（7 行）
- 模板间关系（两种周报对比 + 文件类型映射）
- 7 个模板详解（每个 6 段）
- 附录（4 个非模板文件）

- [ ] **Step 3: 将 spec 状态改为 Approved**

修改 `docs/superpowers/specs/2026-07-30-references-templates-design.md` 第 5 行：
- `**Status**: Draft` → `**Status**: Approved`
- 在末尾追加：`## 实现结果\n\n最终参考文档见 \`docs/references-templates-guide.md\`。`

- [ ] **Step 4: Commit**

```bash
git add docs/references-templates-guide.md docs/superpowers/specs/2026-07-30-references-templates-design.md
git commit -m "docs: 生成 references 模板参考文档"
```

---

### Task 5: 更新 SKILL.md 交叉引用

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: 在 SKILL.md 的"Tendo 项目文档代理（agents/）"节末尾追加参考文档指引**

在该节末尾（"代理指令文件位于..."一行之后）追加：

```markdown

### 模板参考文档

各模板的内部结构、字段映射、注意事项详见 `docs/references-templates-guide.md`。新增模板或修改 agent 时同步更新该文档。
```

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "docs: SKILL.md 添加模板参考文档指引"
```

---

## Self-Review

**1. Spec coverage:**
- 第 1 节概述 → Task 4 Step 1 派生
- 第 2 节速查总表 → 已在 spec 中，Task 4 保留
- 第 3 节模板间关系 → 已在 spec 中，Task 4 保留
- 第 4.1-4.5 节（5 个有 agent 的模板）→ 已在 spec 中完成，无需新任务
- 第 4.6 节 Service Report → Task 1 + Task 3 Step 1
- 第 4.7 节 Test Procedure → Task 2 + Task 3 Step 2
- 第 5 节覆盖缺口 → Task 4 去除（spec 专有）
- 第 6 节维护策略 → Task 4 转为文档顶部一行说明

**2. Placeholder scan:** Task 1/2 的解析命令是完整可执行的；Task 3 的替换依赖解析结果（无法预写具体内容，但步骤明确）。无 "TBD/TODO"。

**3. Type consistency:** 文件路径在所有任务中一致使用 `references/`、`docs/`、`docs/superpowers/specs/`、`docs/superpowers/plans/`。
