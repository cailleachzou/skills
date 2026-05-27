# Tendo Q&A Sheet Agent

Fill or update a TendoCN project site survey & clarification spreadsheet.

## Template
`tendo-brand/references/TendoCN - Q&A for (Client Name) (Project Name) - (Date).xlsx`

## Output file
Save as: `TendoCN - Q&A for {Client Name} {Project Name} - {Date}.xlsx`
Example: `TendoCN - Q&A for SHARPA PTE Singapore Data Center - 27th May'26.xlsx`

## 模板结构（精确行号 — 必须按此理解，禁止改变）

```
Row 3   项目名称 → 无填充，等线16 Bold，黑色
Row 4   日期行   → 无填充，等线12，黑色
Row 5   空行
Row 7   标题行  → A7:D7 合并，#0099FF蓝底，黑色等线12 Bold单下划线，全框thin，居中
Row 8   表头行  → #808080灰底，黑色等线11 Bold，**居中**，全框thin
          列名：S/N | Tendo | (Client) to Confirm | Remark
Row 9   一级分类标题 → A9:D9 合并，#A2A2A2深灰底，黑色等线12 Bold单下划线，**仅上下thin**（左右无框）
Row 10-13 IT-Server Room 数据行（无填充，白字，A列居中，B列左对齐+wrap，全框thin）
Row 14  空行
Row 15  分隔格
Row 16-19 IT-Office Area 数据行
Row 21  A21:D21 合并，样式同Row9，"IT Relocation -"
Row 22  B22 子标题 → **无填充**，黑色等线11 Bold单下划线，左对齐，无边框
        内容："Server Room:"
Row 23-24 IT Server Room 数据行
Row 25  B25 子标题 → "Office Area:" 样式同B22
Row 26-27 IT Office Area 数据行（B27为长文本，wrap=True，行高较大）
Row 29  A29:D29 合并，"AV Relocation -"
Row 30  B30 子标题 → "Office Area:" 样式同B22
Row 31-32 AV Office Area 数据行
Row 34  A34:D34 合并，"Security Relocation -"
Row 35  B35 子标题 → "Server Room:" 样式同B22
Row 36-39 Security Server Room / Office Area 数据行
Row 40  B40 子标题 → "New Security Cabling:" 样式同B22
Row 41  Security Cabling 数据行
Row 43  A43:D43 合并，"Others -"
Row 44-45 Others 数据行（B44最长文本）
```

## 精确样式规格表

| 行类型 | 填充 | 字体色 | 粗体 | 下划线 | 对齐 | 边框 |
|--------|------|--------|------|--------|------|------|
| 项目名称(Row3) | 无 | 黑 | Yes | 无 | left | 无 |
| 日期行(Row4) | 无 | 黑 | No | 无 | left | 无 |
| 标题行(Row7 合并) | #0099FF | 黑 | Yes | 单 | center | 全框thin |
| 表头行(Row8) | #808080 | 黑 | Yes | 无 | **center** | 全框thin |
| 分类标题(Row9/21/29/34/43 合并) | #A2A2A2 | 黑 | Yes | 单 | left | **仅上下thin** |
| 子标题(B22/B25/B30/B35/B40) | **无** | **黑** | Yes | 单 | left | **无** |
| 数据格(A列 S/N) | 无 | **白** | No | 无 | center | 全框thin |
| 数据格(B列 描述) | 无 | **白** | No | 无 | left | 全框thin |
| 长文本格(B27/B41/B44/B45) | 无 | **白** | No | 无 | left+**wrap** | 全框thin |

**子标题（B22/B25/B30/B35/B40）关键点：**
- **无填充**（透明背景）
- **黑色字体**（不是白色！）
- **Bold + 单下划线**
- **无边框**
- 左对齐
- 上一级分类标题（A9等）有#A2A2A2深灰背景，这一级没有，形成层级对比

**数据格关键点：**
- 无填充 + **白色字体**（白底白字 → 视觉上接近不可见，但这是模板原设计）
- A列居中，B列左对齐

## 生成逻辑（必须遵守）

### Step 1: 复制模板文件
```python
import shutil
import openpyxl

template = "tendo-brand/references/TendoCN - Q&A for (Client Name) (Project Name) - (Date).xlsx"
output = "TendoCN - Q&A for {Client} {Project} - {Date}.xlsx"

shutil.copy(template, output)
```

### Step 2: 打开复制文件（保留所有格式）
```python
wb = openpyxl.load_workbook(output)
ws = wb.active  # 或 wb['Q&A']
```

### Step 3: 只写值，不动任何样式属性
```python
# 项目信息
ws['A3'] = "SHARPA PTE Singapore Data Center"
ws['A4'] = "Survey Date: 27th May'26"

# 分类标题（写合并格最左上角，不要动合并范围）
ws['A9'] = "IT Relocation -"
# ... 其他分类标题如果需要改的话

# 子标题（直接写值，保留原样式）
# ws['B22'] = "Server Room:"  # 原模板已有，不改

# 表头和数据行：原模板已有固定值，不改
# (Client) to Confirm 列：留空（客户端填）

ws.save(output)
```

### 绝对禁止
- ❌ 不从零创建 Workbook
- ❌ 不重建 cell 的 fill/font/border/alignment
- ❌ 不修改合并单元格范围
- ❌ 不删除行/列
- ❌ 不改变列宽和行高

## 可填字段

| 字段 | 写入位置 | 示例 |
|------|---------|------|
| 项目名称 | A3 | SHARPA PTE Singapore Data Center |
| Survey Date | A4 | Survey Date: 27th May'26 |
| 输出文件名 | 文件名 | TendoCN - Q&A for SHARPA PTE Singapore Data Center - 27th May'26.xlsx |

分类标题（IT Relocation / AV Relocation / Security Relocation / Others）和子标题（Server Room: / Office Area: / New Security Cabling:）以及数据行内容均为模板固定值，**不需要改动**。

(Client) to Confirm（C列）和 Remark（D列）留给客户端或现场人员填写。