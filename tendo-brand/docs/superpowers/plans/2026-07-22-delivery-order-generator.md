# Delivery Order Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an agent instruction file that parses email text and fills a Material Requisition Excel template, producing a delivery order file.

**Architecture:** Single agent instruction file (`agents/delivery-order.md`) that guides the LLM to parse unstructured text, map fields to template cells, and use openpyxl to fill the template. Registered as a triggered agent in `SKILL.md`.

**Tech Stack:** Python openpyxl, agent markdown instructions

---

### Task 1: Create Agent Instruction File

**Files:**
- Create: `tendo-brand/agents/delivery-order.md`

- [ ] **Step 1: Write the agent instruction file**

Create `tendo-brand/agents/delivery-order.md` with the following content:

```markdown
# Agent: Delivery Order (出库单) Generator

## Trigger

当用户提到以下关键词时激活本代理：
- 出库单、出库
- Material Requisition
- TCMR
- delivery order

## Template

模板路径：`references/TCMR2603-00005- Material Requisition - TCSO2603-00085.xlsx`

## Workflow

1. 读取用户粘贴的邮件/消息文本
2. 按解析规则提取各字段
3. 用 openpyxl 复制模板并填充数据
4. 保存到目标目录

## Field Mapping

| 字段 | 单元格 | 数据来源 | 默认值 |
|------|--------|----------|--------|
| Material Requisition No. | G4 | 文本 `出库单号：TCMR...` | 必填 |
| Date | G5 | 文本或当天日期 | 当天 `YYYY-MM-DD` |
| Currency | G6 | 文本 `Currency:` | CNY |
| Company | C5 | 文本 `Company:` | 必填 |
| Address | C6 | 文本 `Address:` | 必填 |
| Sales Order No. | C7 | 文本 `Sales Order No.:` | 必填 |
| Sales Quotation No. | C8 | 文本 `Sales Quotation No.:` | 必填 |
| Submitted By | C9 | 文本 `Submitted By:` | Cailleach.Zou |
| Deliver To | C4 | 文本 `Deliver To:` | 空 |
| Part No. | B12-B37 | 物料表格 | 必填 |
| Description | C12-C37 | 物料表格（取英文部分） | 必填 |
| Qty | E12-E37 | 物料表格 | 必填 |
| Unit | F12-F37 | 物料表格 | 必填 |
| Unit Cost | G12-G37 | 物料表格 | 必填 |

## Parsing Rules

从用户粘贴的文本中提取：

1. **出库单号** — 匹配 `出库单号[：:]\s*(TCMR[\d-]+)`
2. **Company** — 匹配 `Company[：:]\s*(.+)`
3. **Address** — 匹配 `Address[：:]\s*(.+)`
4. **Sales Order No.** — 匹配 `Sales Order No\.?[：:]\s*(.+)`
5. **Sales Quotation No.** — 匹配 `Sales Quotation No\.?[：:]\s*(.+)`
6. **Date** — 默认当天日期
7. **Currency** — 默认 CNY
8. **Submitted By** — 默认 Cailleach.Zou
9. **物料行** — 从表格/列表区域提取每行的 Part No.、Description、Qty、Unit、Unit Cost
   - Description 可能有中英文，取英文部分
   - Unit Cost 去掉 ¥ 和逗号，保留数字

## Formula Preservation

填充时不要覆盖以下单元格的公式：
- **A12**: 值为 `1`（手动设置）
- **A13-A37**: 公式 `=A{row-1}+1`，自动递增
- **H12-H37**: 公式 `=E{row}*G{row}`，Qty × Unit Cost
- **G7**: `=SUM(H12:H37)/1.13` — Sub-Total
- **G8**: `=G7*0.13` — Tax
- **G9**: `=SUM(G7:G8)` — Total

填充物料行时，A 列和 H 列留空（让公式自动计算）。

## Output Path

```
{项目目录}/Tendo - 03_资料 Technical Archive/出库单 Material Requisition/{Requisition No}- Material Requisition - {Sales Order No.}.xlsx
```

- 目录不存在时用 `os.makedirs(exist_ok=True)` 自动创建
- 文件名示例：`TCMR2607-00010- Material Requisition - TCSO2607-00110.xlsx`

## Python Script Template

使用 openpyxl 操作模板时，参考以下核心逻辑：

```python
import openpyxl
import shutil
import os
from datetime import date

def gen_delivery_order(data, output_dir):
    """
    data = {
        "requisition_no": "TCMR2607-00010",
        "company": "Cooley LLP Shanghai Representative Office",
        "address": "IFC - Tower 2 Level 35, Unit 3510, 8 Century Avenue, Pudong New Area, Shanghai, 200120",
        "sales_order_no": "TCSO2607-00110",
        "sales_quotation_no": "TCSQ2607-00184R2",
        "submitted_by": "Cailleach.Zou",
        "date": "2026-07-22",
        "currency": "CNY",
        "deliver_to": "",
        "items": [
            {"part_no": "760191940", "description": "Faceplate 2-Port, White", "qty": 4, "unit": "个", "unit_cost": 10.00},
        ]
    }
    """
    template_path = os.path.join(os.path.dirname(__file__), '..', 'references',
                                  'TCMR2603-00005- Material Requisition -  TCSO2603-00085.xlsx')

    # Copy template
    req_no = data["requisition_no"]
    so_no = data["sales_order_no"]
    filename = f"{req_no}- Material Requisition - {so_no}.xlsx"
    output_path = os.path.join(output_dir, filename)
    os.makedirs(output_dir, exist_ok=True)
    shutil.copy2(template_path, output_path)

    # Load and fill
    wb = openpyxl.load_workbook(output_path)
    ws = wb["Material Requisition"]

    # Header fields
    ws["C4"] = data.get("deliver_to", "")
    ws["C5"] = data["company"]
    ws["C6"] = data["address"]
    ws["C7"] = data["sales_order_no"]
    ws["C8"] = data["sales_quotation_no"]
    ws["C9"] = data.get("submitted_by", "Cailleach.Zou")
    ws["G4"] = data["requisition_no"]
    ws["G5"] = data.get("date", str(date.today()))
    ws["G6"] = data.get("currency", "CNY")

    # Items (start from row 12)
    for i, item in enumerate(data["items"]):
        row = 12 + i
        ws.cell(row=row, column=2, value=item["part_no"])      # B: Part No.
        ws.cell(row=row, column=3, value=item["description"])   # C: Description
        ws.cell(row=row, column=5, value=item["qty"])           # E: Qty
        ws.cell(row=row, column=6, value=item["unit"])          # F: Unit
        ws.cell(row=row, column=7, value=item["unit_cost"])     # G: Unit Cost
        # A (No.) and H (Total Cost) use formulas — don't touch

    wb.save(output_path)
    return output_path
```

## Test

用以下数据测试：

```python
test_data = {
    "requisition_no": "TCMR2607-00010",
    "company": "Cooley LLP Shanghai Representative Office",
    "address": "IFC - Tower 2 Level 35, Unit 3510, 8 Century Avenue, Pudong New Area, Shanghai, 200120",
    "sales_order_no": "TCSO2607-00110",
    "sales_quotation_no": "TCSQ2607-00184R2",
    "submitted_by": "Cailleach.Zou",
    "date": "2026-07-22",
    "currency": "CNY",
    "items": [
        {"part_no": "760191940", "description": "Faceplate 2-Port, White", "qty": 4, "unit": "个", "unit_cost": 10.00},
    ]
}
```

输出路径：`test/TCMR2607-00010- Material Requisition - TCSO2607-00110.xlsx`
```

- [ ] **Step 2: Verify file was created**

Run: `ls tendo-brand/agents/delivery-order.md`
Expected: file exists

- [ ] **Step 3: Commit**

```bash
git add tendo-brand/agents/delivery-order.md
git commit -m "feat: add delivery order agent instruction file"
```

---

### Task 2: Register Agent in SKILL.md

**Files:**
- Modify: `tendo-brand/SKILL.md` (add trigger entry to agent table)

- [ ] **Step 1: Add agent entry to SKILL.md**

In `tendo-brand/SKILL.md`, find the `## Tendo 项目文档代理（agents/）` section and add a new row to the table:

```markdown
| 出库单、Material Requisition、TCMR、delivery order | `agents/delivery-order.md` | `TCMR2603-00005- Material Requisition - TCSO2603-00085.xlsx` |
```

- [ ] **Step 2: Verify SKILL.md update**

Run: `grep -n "delivery-order" tendo-brand/SKILL.md`
Expected: shows the new line with `agents/delivery-order.md`

- [ ] **Step 3: Commit**

```bash
git add tendo-brand/SKILL.md
git commit -m "feat: register delivery order agent in SKILL.md"
```

---

### Task 3: Test with Sample Data

**Files:**
- Create: `tendo-brand/test/TCMR2607-00010- Material Requisition - TCSO2607-00110.xlsx`

- [ ] **Step 1: Run the Python script to generate test output**

```python
import sys
sys.path.insert(0, r"C:\Users\59620\.claude\skills\tendo-brand")
from agents import delivery_order  # or inline the function

test_data = {
    "requisition_no": "TCMR2607-00010",
    "company": "Cooley LLP Shanghai Representative Office",
    "address": "IFC - Tower 2 Level 35, Unit 3510, 8 Century Avenue, Pudong New Area, Shanghai, 200120",
    "sales_order_no": "TCSO2607-00110",
    "sales_quotation_no": "TCSQ2607-00184R2",
    "submitted_by": "Cailleach.Zou",
    "date": "2026-07-22",
    "currency": "CNY",
    "items": [
        {"part_no": "760191940", "description": "Faceplate 2-Port, White", "qty": 4, "unit": "个", "unit_cost": 10.00},
    ]
}

output = gen_delivery_order(test_data, r"C:\Users\59620\.claude\skills\tendo-brand\test")
print(f"Generated: {output}")
```

Run: `py -3 scripts/gen_delivery_order.py` (or inline)
Expected: `test/TCMR2607-00010- Material Requisition - TCSO2607-00110.xlsx` created

- [ ] **Step 2: Verify output file contents**

```python
import openpyxl
wb = openpyxl.load_workbook(r"C:\Users\59620\.claude\skills\tendo-brand\test\TCMR2607-00010- Material Requisition - TCSO2607-00110.xlsx")
ws = wb["Material Requisition"]

# Check header fields
assert ws["G4"].value == "TCMR2607-00010", f"G4: {ws['G4'].value}"
assert ws["C5"].value == "Cooley LLP Shanghai Representative Office", f"C5: {ws['C5'].value}"
assert ws["C7"].value == "TCSO2607-00110", f"C7: {ws['C7'].value}"
assert ws["C8"].value == "TCSQ2607-00184R2", f"C8: {ws['C8'].value}"

# Check item row
assert ws["B12"].value == "760191940", f"B12: {ws['B12'].value}"
assert ws["C12"].value == "Faceplate 2-Port, White", f"C12: {ws['C12'].value}"
assert ws["E12"].value == 4, f"E12: {ws['E12'].value}"
assert ws["G12"].value == 10.00, f"G12: {ws['G12'].value}"

# Check formulas exist
assert str(ws["H12"].value).startswith("="), f"H12: {ws['H12'].value}"
assert str(ws["G7"].value).startswith("="), f"G7: {ws['G7'].value}"

print("All assertions passed!")
```

Run: `py -3 -c "..."`
Expected: `All assertions passed!`

- [ ] **Step 3: Visual QA with audit script**

Run: `py -3 "C:\Users\59620\.local\share\mimocode\builtin_skills\0.1.7\skills\xlsx-official\scripts\audit.py" "C:\Users\59620\.claude\skills\tendo-brand\test\TCMR2607-00010- Material Requisition - TCSO2607-00110.xlsx"`
Expected: status OK

- [ ] **Step 4: Commit test output**

```bash
git add tendo-brand/test/
git commit -m "test: verify delivery order generator with sample data"
```
