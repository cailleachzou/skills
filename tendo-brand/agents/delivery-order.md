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
3. 用 openpyxl 复制模板并填充数据，保存 xlsx
4. 通过 Excel COM 自动化将 xlsx 导出为 PDF
5. 用 PyMuPDF 在 PDF 签名区域叠加签名图片并填写 Name/Title/Date
6. 保存最终 PDF（xlsx 同步保留）

## Field Mapping

| 字段 | 单元格 | 数据来源 | 默认值 |
|------|--------|----------|--------|
| Material Requisition No. | G4 | 文本 `出库单号：TCMR...` | 必填 |
| Date | G5 | 文本或当天日期 | datetime 对象，模板 number_format 自动渲染为 `DD MONTH, YYYY` |
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
| Signature Date | A50 | 当天日期 | `Date:DD/MM/YY`（模板已有标签前缀，仅更新日期部分） |

## Signature Section

### xlsx 签名填充

模板中签名区域位于 rows 40-50。A48:A50 已包含固定标签+值（`Name:Cailleach Zou` 等），脚本仅更新 A50 的日期部分：

| 单元格 | 内容 | 说明 |
|--------|------|------|
| A48 | 模板已有 | `Name:Cailleach Zou`，不覆盖 |
| A49 | 模板已有 | `Title:Senior Project Engineer`，不覆盖 |
| A50 | 脚本更新 | `Date:DD/MM/YY`，从 G5 datetime 转换 |

### PDF 签名叠加

仅叠加签名图片，不写文字 — xlsx 导出 PDF 时已包含 Name/Title/Date：

| 元素 | 位置 | 内容 |
|------|------|------|
| 签名图片 | "Signature:" 文字下方（Requested By 侧） | `assets/cailleach.png`，宽度 80pt，保持比例 |

签名区域在 PDF 中的布局（Requested By 侧 = 左侧）：
```
Requested By:
Signature: ________
┌─────────────────────┐
│   [签名图片]          │  ← cailleach.png，居中放置在 Signature: 下方框内
└─────────────────────┘
Name: Cailleach Zou        ← xlsx 自带
Title: Senior Project Engineer  ← xlsx 自带
Date: 22/07/26              ← xlsx 自带
```

## Parsing Rules

从用户粘贴的文本中提取：

1. **出库单号** — 匹配 `出库单号[：:]\s*(TCMR[\d-]+)`
2. **Company** — 匹配 `Company[：:]\s*(.+)`
3. **Address** — 匹配 `Address[：:]\s*(.+)`
4. **Sales Order No.** — 匹配 `Sales Order No\.?[：:]\s*(.+)`
5. **Sales Quotation No.** — 匹配 `Sales Quotation No\.?[：:]\s*(.+)`
6. **Date** — 默认当天日期，格式 `DD-MM-YY`
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
{项目目录}/Tendo - 03_资料 Technical Archive/出库单 Material Requisition/{Requisition No}- Material Requisition - {Sales Order No.}.pdf
```

- 目录不存在时用 `os.makedirs(exist_ok=True)` 自动创建
- xlsx 和 PDF 同时输出，文件名相同仅后缀不同
- 文件名示例：`TCMR2607-00010- Material Requisition - TCSO2607-00110.xlsx`

## Python Script Template

### Step 1: 生成 xlsx

```python
import openpyxl
import shutil
import os
from datetime import date, datetime
from openpyxl.styles import Alignment

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

    # G5: write as datetime object (template number_format renders as "DD MONTH, YYYY")
    date_str = data.get("date", str(date.today()))
    if isinstance(date_str, str):
        from datetime import datetime as dt
        ws["G5"] = dt.strptime(date_str, "%Y-%m-%d")
    elif isinstance(date_str, dt):
        ws["G5"] = date_str
    else:
        from datetime import datetime as dt
        ws["G5"] = dt.now()

    ws["G6"] = data.get("currency", "CNY")

    # Enable wrap_text on C4-C9 for long content (address, etc.)
    # C6:D6 is merged — increase row 6 height for address wrapping
    wrap_align = Alignment(wrap_text=True, vertical='center')
    for row in range(4, 10):
        ws.cell(row=row, column=3).alignment = wrap_align
    ws.row_dimensions[6].height = 45

    # Items (start from row 12)
    for i, item in enumerate(data["items"]):
        row = 12 + i
        ws.cell(row=row, column=2, value=item["part_no"])      # B: Part No.
        ws.cell(row=row, column=3, value=item["description"])   # C: Description
        ws.cell(row=row, column=5, value=item["qty"])           # E: Qty
        ws.cell(row=row, column=6, value=item["unit"])          # F: Unit
        ws.cell(row=row, column=7, value=item["unit_cost"])     # G: Unit Cost
        # A (No.) and H (Total Cost) use formulas — don't touch

    # Signature section (Requested By = left side, A48:C48 / A49:C49 / A50:C50 merged)
    # Template already has "Name:Cailleach Zou" / "Title:Senior Project Engineer" / "Date:DD/MM/YY"
    # Only update A50 date part — keep "Date:" prefix
    g5_val = ws["G5"].value
    if isinstance(g5_val, datetime):
        ws["A50"] = "Date:" + g5_val.strftime("%d/%m/%y")
    else:
        ws["A50"] = "Date:" + str(g5_val)

    wb.save(output_path)
    return output_path
```

### Step 2: xlsx → PDF（Excel COM 自动化）

需要 Excel installed + pywin32。如果环境没有 Excel，跳过 PDF 生成，只输出 xlsx。

```python
import win32com.client

def xlsx_to_pdf(xlsx_path):
    """Convert xlsx to PDF using Excel COM. Returns pdf path or None."""
    try:
        xl = win32com.client.Dispatch('Excel.Application')
        xl.Visible = False
        wb = xl.Workbooks.Open(os.path.abspath(xlsx_path))
        pdf_path = xlsx_path.rsplit('.', 1)[0] + '.pdf'
        wb.ExportAsFixedFormat(0, pdf_path)  # 0 = xlTypePDF
        wb.Close(False)
        xl.Quit()
        return pdf_path
    except Exception as e:
        print(f"PDF conversion failed: {e}")
        return None
```

### Step 3: PDF 签名叠加（PyMuPDF）

```python
import fitz

def overlay_signature(pdf_path):
    """Overlay signature image on PDF. Text (Name/Title/Date) comes from xlsx."""
    skill_dir = os.path.join(os.path.dirname(__file__), '..')
    sig_img = os.path.join(skill_dir, 'assets', 'cailleach.png')

    doc = fitz.open(pdf_path)
    page = doc[0]

    # Find 'Signature:' and 'Name:' on the left side (Requested By)
    # There are two of each — index [0] is right (Approved), [1] is left (Requested)
    sig_instances = page.search_for('Signature:')
    sig_left = sig_instances[1] if len(sig_instances) > 1 else sig_instances[0]

    name_instances = page.search_for('Name:')
    name_left = name_instances[1] if len(name_instances) > 1 else name_instances[0]

    # Place signature image inside the box below 'Signature:' label
    box_top = sig_left.y1 + 1       # just below 'Signature:' text
    box_bottom = name_left.y0 - 2   # just above 'Name:' text
    box_left = sig_left.x0 - 2
    box_right = 185                  # left column boundary
    box_center_x = (box_left + box_right) / 2

    img_w = 80  # pt
    img_h = int(img_w * 50 / 99)  # maintain aspect ratio of cailleach.png (99x50)
    img_x = box_center_x - img_w / 2
    img_y = (box_top + box_bottom) / 2 - img_h / 2

    sig_rect = fitz.Rect(img_x, img_y, img_x + img_w, img_y + img_h)
    page.insert_image(sig_rect, filename=sig_img)

    doc.save(pdf_path, incremental=True, encryption=0)
    doc.close()
```

### 完整调用流程

```python
# 1. 生成 xlsx
xlsx_path = gen_delivery_order(data, output_dir)

# 2. 转 PDF（可选，需要 Excel）
pdf_path = xlsx_to_pdf(xlsx_path)

# 3. 叠加签名图片（仅 PDF，不写文字）
if pdf_path:
    overlay_signature(pdf_path)
    print(f"PDF: {pdf_path}")

print(f"XLSX: {xlsx_path}")
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

输出路径：`test/TCMR2607-00010- Material Requisition - TCSO2607-00110.xlsx` + `.pdf`
