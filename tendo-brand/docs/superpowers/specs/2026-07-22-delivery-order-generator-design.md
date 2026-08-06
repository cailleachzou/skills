# Design: 出库单 Material Requisition Generator

**Date**: 2026-07-22
**Author**: DUDU & Cailleach
**Status**: Draft

## Overview

基于现有 Material Requisition Excel 模板，创建一个 agent 指令文件，支持从用户粘贴的邮件/消息文本中解析出库单信息，自动填充模板并输出到指定项目目录。

## Template Reference

模板文件：`references/TCMR2603-00005- Material Requisition - TCSO2603-00085.xlsx`

### 模板结构

| 区域 | 行范围 | 内容 |
|------|--------|------|
| 标题 | A1:H2 (merged) | "Material Requisition"，18pt bold Arial |
| 头部信息 | Row 4-9 | 左侧：Deliver To / Company / Address / Sales Order / Quotation / Submitted By |
|  |  | 右侧：Requisition No / Date / Currency / Sub-Total / Tax / Total |
| 物料表头 | Row 11 | No. / Part No. / Description / Qty / Unit / Unit Cost / Total Cost |
| 物料数据 | Row 12-37 | 最多 26 行物料，A 列和 H 列含公式 |
| 签字区 | Row 39-50 | 确认声明 + Requested By / Approved By 签名栏 |

### 公式保留规则

- **A12**: `1`（手动值）
- **A13-A37**: `=A12+1` 等递增公式 — 填充物料行时自动处理
- **H12-H37**: `=E{row}*G{row}` — Qty × Unit Cost，不要覆盖
- **G7**: `=SUM(H12:H37)/1.13` — Sub-Total（含税拆分）
- **G8**: `=G7*0.13` — Tax
- **G9**: `=SUM(G7:G8)` — Total

## Field Mapping

| 字段 | 单元格 | 数据来源 | 默认值 |
|------|--------|----------|--------|
| Material Requisition No. | G4 | 邮件文本 `出库单号：TCMR...` | 必填 |
| Date | G5 | 邮件文本或当天日期 | 当天 |
| Currency | G6 | 邮件文本 `Currency:` | CNY |
| Company | C5 | 邮件文本 `Company:` | 必填 |
| Address | C6 | 邮件文本 `Address:` | 必填 |
| Sales Order No. | C7 | 邮件文本 `Sales Order No.:` | 必填 |
| Sales Quotation No. | C8 | 邮件文本 `Sales Quotation No.:` | 必填 |
| Submitted By | C9 | 邮件文本 `Submitted By:` | Cailleach.Zou |
| Deliver To | C4 | 邮件文本 `Deliver To:` | 空 |
| Part No. | B12-B37 | 物料表格 | 必填 |
| Description | C12-C37 | 物料表格（取英文部分） | 必填 |
| Qty | E12-E37 | 物料表格 | 必填 |
| Unit | F12-F37 | 物料表格 | 必填 |
| Unit Cost | G12-G37 | 物料表格 | 必填 |

## Email Text Parsing Rules

Agent 从用户粘贴的文本中提取以下信息：

1. **出库单号** — 正则：`出库单号[：:]\s*(TCMR\d{4}-\d{5})`
2. **Company** — 正则：`Company[：:]\s*(.+)`
3. **Address** — 正则：`Address[：:]\s*(.+)`
4. **Sales Order No.** — 正则：`Sales Order No\.?[：:]\s*(.+)`
5. **Sales Quotation No.** — 正则：`Sales Quotation No\.?[：:]\s*(.+)`
6. **Date** — 默认当天 `YYYY-MM-DD`
7. **Currency** — 默认 `CNY`
8. **Submitted By** — 默认 `Cailleach.Zou`
9. **物料行** — 从表格数据区提取：
   - 每行格式：`Part No.` + `Description`（可能有中英文两行）+ `Qty` + `Unit` + `Unit Cost`
   - 提取英文 Description 存入 C 列
   - Unit Cost 提取纯数字（去掉 ¥ 符号和逗号）

## Output

### 文件路径

```
{项目目录}/Tendo - 03_资料 Technical Archive/出库单 Material Requisition/{Requisition No}- Material Requisition - {Sales Order No.}.xlsx
```

- `{Requisition No}` — 出库单号，如 `TCMR2607-00010`
- `{Sales Order No.}` — 销售订单号，如 `TCSO2607-00110`
- 目录不存在时自动创建

### 文件命名示例

`TCMR2607-00010- Material Requisition - TCSO2607-00110.xlsx`

## Agent File Structure

新建 `tendo-brand/agents/delivery-order.md`，包含：

1. 模板路径引用
2. 字段映射表（同上）
3. 解析规则（同上）
4. 输出路径规则（同上）
5. 公式保留说明
6. 调用方式说明

## SKILL.md Registration

在 `tendo-brand/SKILL.md` 的 agents 触发表中添加：

| 触发关键词 | 代理文件 | 模板 |
|-----------|---------|------|
| 出库单、Material Requisition、TCMR、delivery order | `agents/delivery-order.md` | `TCMR2603-00005- Material Requisition - TCSO2603-00085.xlsx` |

## Test Case

使用以下邮件文本进行测试：

```
出库单号：TCMR2607-00010

Part No. 760191940 - 2-孔面板，白色 / Faceplate 2-Port, White
品牌: Commscope / COMMSCOPE
Qty: 4
Unit: 个
Unit Cost: ¥10.00

Company: Cooley LLP Shanghai Representative Office
Address: IFC - Tower 2 Level 35, Unit 3510, 8 Century Avenue, Pudong New Area, Shanghai, 200120
Sales Order No.: TCSO2607-00110
Sales Quotation No.: TCSQ2607-00184R2
```

预期输出：填充完整的 Excel 文件，保存到 test 目录。

## Scope

- [x] Agent 指令文件 `agents/delivery-order.md`
- [x] SKILL.md 注册触发关键词
- [x] 测试验证
- [ ] 不涉及：批量处理、数据库集成、Web UI
