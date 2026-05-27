# Tendo Weekly Status Report Agent

Fill or update a TendoCN weekly project status report (Chinese).

## Template
`tendo-brand/references/SBY - 每周项目状态报告 (中文).docx`

## File output
Save as: `Tendo - DES-{YYYY}-{Project Name} - 周报 #{NN}.docx`

## Fixed structure — DO NOT change
- Header table: 项目名称 | 客户名称 | 地点/地址 | 报告日期 | 项目经理
- Legend row: 蓝色=已完成 | 绿色=符合预期 | 橙色=轻微延误 | 红色=严重延误
- Section letters: A. 结构化布线系统 | B. 机房及IT系统 | C.1/C.2 IT设备搬迁 | D. AV设备搬迁 | E. 检查与验收期
- Work item columns: 项目 | 工作项 | 开始日期 | 结束日期 | 完成度(%) | 备注
- 主要成果 / 下一步关键计划  two-column table
- 风险与问题  table: 项目 | 风险描述 | 描述/影响/解决方案 | 优先级 | 记录日期 | 预计完成 | 备注
- 现场照片  gallery table with captions

## Fillable fields

### Header (replace all placeholders)
| Field | Example |
|-------|---------|
| 项目名称 | 塞恩斯伯里上海新办公室装修项目 |
| 客户名称 | Sainsbury's Argos 亚洲有限公司 |
| 地点/地址 | 上海市静安区天目西路128号嘉里企业中心1座20层 |
| 报告日期 | 2025年9月29日 |
| 项目经理 | Dayne Chea |

### Work progress table
| Field | What to fill |
|-------|-------------|
| 工作项 | Task description (Chinese) |
| 开始日期 | dd/mm/yy format |
| 结束日期 | dd/mm/yy format |
| 完成度 | 0–100% integer |
| 备注 | Status note (已完成/进行中/轻微延误/严重延误/暂定) |

### Color coding for 备注
- 100% + 备注"已完成" → blue text
- 50–99% + on track → green text
- 1–49% or slight delay → orange text
- 0% + major issue → red text

### 主要成果 / 下一步关键计划
- Left: accomplishments with dates
- Right: upcoming activities

### 风险与问题
- Priority: 高 / 中 / 低
- Fill description, impact, solution

## Output rules
- Date format: dd/mm/yy (e.g. 07/09/25)
- Preserve all existing formatting and table structure
- Report number (#NN) increments each week
- Project number in filename: DES-YYYY format
