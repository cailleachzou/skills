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
| Submitted By | C9 | 文本 `Submitted By:` | Liu Shi Hao |
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
8. **Submitted By** — 默认 Liu Shi Hao
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
        "submitted_by": "Liu Shi Hao",
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
    ws["C9"] = data.get("submitted_by", "Liu Shi Hao")
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
    "submitted_by": "Liu Shi Hao",
    "date": "2026-07-22",
    "currency": "CNY",
    "items": [
        {"part_no": "760191940", "description": "Faceplate 2-Port, White", "qty": 4, "unit": "个", "unit_cost": 10.00},
    ]
}
```

输出路径：`test/TCMR2607-00010- Material Requisition - TCSO2607-00110.xlsx`