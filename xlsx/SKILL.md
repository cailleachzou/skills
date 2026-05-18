---
name: xlsx
description: "Internal rules for Excel (.xlsx) spreadsheet creation and editing. Provides openpyxl for formulas and formatting, pandas for data analysis, LibreOffice recalculation (recalc.py), formula error checking, financial model color coding standards, and professional formatting rules."
license: Proprietary. LICENSE.txt has complete terms
---

# 输出文件要求

## 所有 Excel 文件

### 专业字体
- 所有交付物使用统一、专业字体（如 Arial、Times New Roman），除非用户另有要求

### 公式零错误
- 每个 Excel 模型交付时必须**零公式错误**（#REF!、#DIV/0!、#VALUE!、#N/A、#NAME?）

### 保留现有模板（更新模板时）
- 修改文件时须研究和**严格匹配**现有格式、样式和惯例
- 切勿将标准化格式强加于已有固定风格的文件
- 现有模板的惯例**始终优先于**本指南

## 财务模型

### 颜色编码标准
除非用户或现有模板另有说明

#### 行业标准颜色惯例
- **蓝色文字（RGB: 0,0,255）**：硬编码输入值，及用户用于情景切换的数字
- **黑色文字（RGB: 0,0,0）**：所有公式和计算
- **绿色文字（RGB: 0,128,0）**：同一工作簿内其他工作表的链接
- **红色文字（RGB: 255,0,0）**：指向外部文件的链接
- **黄色背景（RGB: 255,255,0）**：需要引起注意的关键假设，或需要更新的单元格

### 数字格式标准

#### 必须遵守的格式规则
- **年份**：格式化为文本字符串（如"2024"而非"2,024"）
- **货币**：使用 $#,##0 格式；表头务必注明单位（如"Revenue ($mm)"）
- **零值**：使用数字格式将所有零显示为"-"，百分比亦然（如"$#,##0;($#,##0);-"）
- **百分比**：默认使用 0.0% 格式（一位小数）
- **倍数**：格式化为 0.0x（估值倍数如 EV/EBITDA、P/E）
- **负数**：使用括号（123），而非负号 -123

### 公式编写规则

#### 假设条件放置
- 将**所有**假设（增长率、利润率、倍数等）放在独立的假设单元格中
- 公式中使用单元格引用，而非硬编码值
- 示例：用 `=B5*(1+$B$6)` 而非 `=B5*1.05`

#### 公式错误预防
- 验证所有单元格引用是否正确
- 检查范围是否存在 off-by-one 错误
- 确保所有预测周期的公式保持一致
- 用边界条件测试（零值、负数）
- 验证无意外循环引用

#### 硬编码值的文档要求
- 在旁边单元格注释或标注（表格末尾时）。格式：`Source: [系统/文档], [日期], [具体参考], [URL（如有]`
- 示例：
  - "Source: Company 10-K, FY2024, Page 45, Revenue Note, [SEC EDGAR URL]"
  - "Source: Company 10-Q, Q2 2025, Exhibit 99.1, [SEC EDGAR URL]"
  - "Source: Bloomberg Terminal, 8/15/2025, AAPL US Equity"
  - "Source: FactSet, 8/20/2025, Consensus Estimates Screen"

# XLSX 的创建、编辑与分析

## 概述

用户可能要求创建、编辑或分析 .xlsx 文件的内容。我们针对不同任务有不同的工具和工作流程。

## 重要要求

**LibreOffice 用于公式重算**：假设 LibreOffice 已安装，可通过 `scripts/recalc.py` 脚本重算公式值。该脚本在首次运行时自动配置 LibreOffice，包括在受限 Unix 套接字的环境下（由 `scripts/office/soffice.py` 处理）

**Windows 下的 Python**：使用 `/c/Users/59620/AppData/Local/Python/bin/python.exe`（而非 `python` 或 `python3`）。脚本假设你从技能目录 `C:\Users\59620\.claude\skills\xlsx` 运行。在 Windows 上，LibreOffice `soffice` 假设已在 PATH 中，或按需使用绝对路径引用。

## 数据读取与分析

### 使用 pandas 进行数据分析
对于数据分析、可视化和基础操作，使用 **pandas**，它提供强大的数据处理能力：

```python
import pandas as pd

# 读取 Excel
df = pd.read_excel('file.xlsx')  # 默认：第一个 sheet
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # 所有 sheet 作为字典

# 分析
df.head()      # 预览数据
df.info()      # 列信息
df.describe()  # 统计信息

# 写入 Excel
df.to_excel('output.xlsx', index=False)
```

## Excel 文件工作流程

## 关键原则：使用公式，而非硬编码值

**始终使用 Excel 公式，而不是在 Python 中计算后硬编码。** 这确保电子表格保持动态可更新。

### 错误做法 — 硬编码计算值
```python
# 错误：在 Python 中计算后硬编码
total = df['Sales'].sum()
sheet['B10'] = total  # 硬编码了 5000

# 错误：在 Python 中计算增长率
growth = (df.iloc[-1]['Revenue'] - df.iloc[0]['Revenue']) / df.iloc[0]['Revenue']
sheet['C5'] = growth  # 硬编码了 0.15

# 错误：在 Python 中计算平均值
avg = sum(values) / len(values)
sheet['D20'] = avg  # 硬编码了 42.5
```

### 正确做法 — 使用 Excel 公式
```python
# 正确：让 Excel 计算求和
sheet['B2'] = '=SUM(A1:A10)'

# 正确：增长率使用 Excel 公式
sheet['C5'] = '=(C4-C2)/C2'

# 正确：使用 Excel 函数计算平均
sheet['D20'] = '=AVERAGE(D2:D19)'
```

这适用于**所有**计算——汇总、百分比、比率、差异等。当源数据变化时，电子表格应能自动重新计算。

## 常见工作流程
1. **选工具**：数据用 pandas，公式/格式用 openpyxl
2. **创建/加载**：新建工作簿或加载已有文件
3. **修改**：添加/编辑数据、公式和格式
4. **保存**：写入文件
5. **重算公式（使用公式时必须执行）**：从技能目录运行：
   ```bash
   cd C:\Users\59620\.claude\skills\xlsx
   /c/Users/59620/AppData/Local/Python/bin/python.exe scripts/recalc.py output.xlsx
   ```
6. **验证并修复错误**：
   - 脚本返回包含错误详情的 JSON
   - 若 `status` 为 `errors_found`，检查 `error_summary` 获取具体错误类型和位置
   - 修复问题后重新计算
   - 常见错误及修复：
     - `#REF!`：无效的单元格引用
     - `#DIV/0!`：除数为零
     - `#VALUE!`：公式中数据类型错误
     - `#NAME?`：无法识别的公式名称

### 创建新的 Excel 文件

```python
# 使用 openpyxl 处理公式和格式
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

# 添加数据
sheet['A1'] = 'Hello'
sheet['B1'] = 'World'
sheet.append(['Row', 'of', 'data'])

# 添加公式
sheet['B2'] = '=SUM(A1:A10)'

# 格式设置
sheet['A1'].font = Font(bold=True, color='FF0000')
sheet['A1'].fill = PatternFill('solid', start_color='FFFF00')
sheet['A1'].alignment = Alignment(horizontal='center')

# 列宽
sheet.column_dimensions['A'].width = 20

wb.save('output.xlsx')
```

### 编辑现有 Excel 文件

```python
# 使用 openpyxl 保留公式和格式
from openpyxl import load_workbook

# 加载现有文件
wb = load_workbook('existing.xlsx')
sheet = wb.active  # 或 wb['SheetName'] 指定 sheet

# 处理多个 sheet
for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]
    print(f"Sheet: {sheet_name}")

# 修改单元格
sheet['A1'] = 'New Value'
sheet.insert_rows(2)  # 在第 2 行插入
sheet.delete_cols(3)  # 删除第 3 列

# 新增 sheet
new_sheet = wb.create_sheet('NewSheet')
new_sheet['A1'] = 'Data'

wb.save('modified.xlsx')
```

## 公式重算

openpyxl 创建或修改的 Excel 文件中，公式以字符串形式存在，但没有计算值。从技能目录运行：

```bash
cd C:\Users\59620\.claude\skills\xlsx
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/recalc.py <excel_file> [timeout_seconds]
```

示例：
```bash
cd C:\Users\59620\.claude\skills\xlsx
/c/Users/59620/AppData/Local/Python/bin/python.exe scripts/recalc.py output.xlsx 30
```

该脚本：
- 首次运行时自动配置 LibreOffice 宏
- 重算所有 sheet 中的所有公式
- 扫描**所有**单元格中的 Excel 错误（#REF!、#DIV/0! 等）
- 返回包含错误位置和计数的详细 JSON
- 支持 Linux、macOS 和 Windows
- 在 Windows 上，自动解析 soffice 路径（如 `C:\Program Files\LibreOffice\program\soffice.exe`）和宏路径（如 `~\AppData\Roaming\LibreOffice\4\user\basic\Standard`）

## 公式验证检查清单

快速检查公式是否正确工作：

### 核心验证
- [ ] **测试 2-3 个样本引用**：构建完整模型前先验证是否拉取正确数值
- [ ] **列映射**：确认 Excel 列对应正确（如第 64 列 = BL，而非 BK）
- [ ] **行偏移**：记住 Excel 行是 1 索引的（DataFrame 第 5 行 = Excel 第 6 行）

### 常见陷阱
- [ ] **NaN 处理**：用 `pd.notna()` 检查空值
- [ ] **最右侧列**：FY 数据常在第 50 列之后
- [ ] **多重匹配**：搜索所有匹配项，而非仅第一个
- [ ] **除数为零**：公式中使用 `/` 前检查分母（#DIV/0!）
- [ ] **错误引用**：验证所有单元格引用指向目标单元格（#REF!）
- [ ] **跨 sheet 引用**：链接不同 sheet 时使用正确格式（Sheet1!A1）

### 公式测试策略
- [ ] **从小处着手**：广泛应用前先在 2-3 个单元格上测试公式
- [ ] **验证依赖**：检查公式中引用的所有单元格是否存在
- [ ] **边界测试**：包含零、负数和极大值

### 解读 scripts/recalc.py 输出
脚本返回包含错误详情的 JSON：
```json
{
  "status": "success",           // 或 "errors_found"
  "total_errors": 0,              // 错误总数
  "total_formulas": 42,           // 文件中公式总数
  "error_summary": {              // 仅在发现错误时存在
    "#REF!": {
      "count": 2,
      "locations": ["Sheet1!B5", "Sheet1!C10"]
    }
  }
}
```

## 最佳实践

### 库选择
- **pandas**：最适合数据分析、批量操作和简单数据导出
- **openpyxl**：最适合复杂格式、公式和 Excel 特有功能

### openpyxl 使用技巧
- 单元格索引从 1 开始（row=1, column=1 指的是单元格 A1）
- 使用 `data_only=True` 读取计算后的值：`load_workbook('file.xlsx', data_only=True)`
- **警告**：用 `data_only=True` 打开并保存后，公式会被值替换并永久丢失
- 大文件：读取用 `read_only=True`，写入用 `write_only=True`
- 公式会被保留但不会求值——用 scripts/recalc.py 更新数值

### pandas 使用技巧
- 指定数据类型以避免推断问题：`pd.read_excel('file.xlsx', dtype={'id': str})`
- 大文件：读取指定列：`pd.read_excel('file.xlsx', usecols=['A', 'C', 'E'])`
- 正确处理日期：`pd.read_excel('file.xlsx', parse_dates=['date_column'])`

## 代码风格指南
**重要提示**：生成 Excel 操作的 Python 代码时：
- 写最精简、最简洁的代码，不必要的注释不要写
- 避免冗长的变量名和冗余操作
- 避免不必要的 print 语句

**Excel 文件本身**：
- 复杂公式或重要假设的单元格添加注释
- 为硬编码值记录数据来源
- 为关键计算和模型部分添加说明