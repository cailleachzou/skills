# /weekly-report Skill 设计文档

## 概述

一个 MiMoCode Skill，用于自动化生成 Tendo 项目周报 Excel 文件。通过对话式采集进度数据、AI 图像理解现场照片，一键输出格式完整的周报。

## 目标用户

项目管理者（Cailleach / ShiHao），每周使用一次。

## 触发方式

```
/weekly-report
```

## 核心流程

```
Phase 1: 采集项目基本信息
  → 项目名称、工作阶段列表、子项（工位/房间）列表
  ↓
Phase 2: 逐阶段×子项采集进度
  → 每个子项在每个阶段的：完成百分比、状态（In Progress/Delay/Not Started/Completed）、Till Date、Target Date
  ↓
Phase 3: 照片处理
  → 扫描指定文件夹 → MiMo 图片理解 → 自动填写 Description
  → 图片插入：优先尝试自动插入，失败则提示用户手动插入
  ↓
Phase 4: 采集 Issue / RFA 数据
  → 问题描述、风险等级、解决方案、负责人、状态
  ↓
Phase 5: 生成 Excel
  → officecli batch 批量操作，原子性输出
```

## 输出位置

```
项目目录/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/
```

文件命名：`TendoCN - {Client Name} - {Project Name} Weekly Progress Report (项目周报) {YYYY-MM-DD}.xlsx`

命名规则：
- 源模板名：`TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx`
- 输出文件名从模板名派生，替换 Client Name / Project Name / 加入日期
- Agent 完成所有数据填充后，根据采集到的上下文（项目名、客户名）重命名文件

## 模板来源

```
references/TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx
```

文件名格式：`TendoCN - {Client Name} - {Project Name} Weekly Progress Report (项目周报) .xlsx`

## Sheet 结构

### Sheet 1: Progress Report

```
Row 12: [阶段标题行] - 合并单元格，如 "Cable installation" (C12:W12)
Row 13: [列标题] - Item No.(A) | Description(B) | 阶段1: Demolition(C-E) | 阶段2: Protection(F-H) | ... | Overall Percentage(X)
Row 14: [子标题] - Floor(B) | %(C) | Till Date(D) | Target Date(E) (每个阶段重复3列)
Row 15: (空)
Row 16: [楼层标识] - 如 "L35" (B16)
Row 17+: [子项数据行] - A=序号, B=子项名称, C-W=各阶段数据（%, Till Date, Target Date）
```

**颜色编码（状态 → 单元格前景色）：**

| 状态 | 颜色名 | Hex (officecli fill=) |
|------|--------|----------------------|
| In Progress | Green | FF00B050 |
| Delay | Red | FFFF0000 |
| Not Started | Orange | FFFFC000 |
| Completed | Black | FF000000 |

**数据填充逻辑：**
- 列结构由阶段数量决定（每个阶段占3列：%, Till Date, Target Date）
- 新增子项时插入行（`add --type row --shift down`），保持合并单元格偏移
- Overall Percentage 列（X列）= 该子项所有阶段的平均百分比，颜色根据整体状态设置

### Sheet 2: Site Photo

```
Row 12: [列标题] - Item No. | Date | Description | Photos
Row 13+: [照片条目] - 每张照片/每组照片一行
```

**处理方式：**
1. Agent 扫描用户指定的照片文件夹
2. MiMo 图片理解识别照片内容 → 自动生成中英文 Description
3. 照片插入：尝试 `officecli add --type image`，失败则提示用户手动插入
4. 用户可在对话中补充或修正 Description

### Sheet 3: Issue_RFA Log

**Issue Log 部分：**
```
Row 13: [列标题] - Item No. | Date | Issue Description | Risk | Proposed solution | Action By | Completed Photos | Issue Open/Closed | Remarks
Row 14+: [问题条目]
```

**RFI/RFA Log 部分：**
```
Row 22: [列标题] - Item No. | Issued Date | RFI/RFA | Description | Issued to | Respond by | Issue Open/Closed | Remarks
Row 23+: [RFA条目]
```

**状态颜色：**
- Closed: Green (FF92D050)
- Open: Orange (FFFFC000)

## 对话采集协议

### Phase 1: 项目信息

Agent 依次询问：
1. 项目名称（如 "Cooley Shanghai Meeting Room Retrofit"）
2. 项目代码（如 "DES-2026-CSM"）
3. 工作阶段列表（如 "Demolition, Protection, Restoration, New Point Wiring, Testing, Labelling, System trial operation"）
4. 子项列表（如 "Reception and large conference room, Central Park, 103, Open office"）
5. 楼层标识（如 "L35"）

### Phase 2: 进度数据

Agent 按子项×阶段矩阵逐项询问：

```
Agent: 子项 "Reception and large conference room" - Demolition 阶段：
  - 完成百分比？（0-100）
  - 状态？（In Progress / Delay / Not Started / Completed）
  - Till Date？
  - Target Date？
```

### Phase 3: 照片

Agent 询问：
1. 照片文件夹路径
2. 扫描后展示识别结果，用户确认/修正
3. 尝试插入照片，失败则提示手动操作

### Phase 4: Issue/RFA

Agent 询问：
1. 本周是否有新问题？
2. 逐项采集：描述、风险、方案、负责人、状态
3. 是否有 RFI/RFA？

## 技术实现

### 工具链

- **officecli**: Excel 读写、格式设置、行插入、图片插入
- **MiMo**: 图片内容理解
- **shell**: 文件复制、目录创建

### 关键操作序列

```bash
# 1. 复制模板
TEMPLATE="references/TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx"
OUTPUT="项目目录/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/周报.xlsx"
cp "$TEMPLATE" "$OUTPUT"

# 2. 读取模板结构
officecli get "$OUTPUT" '/Sheet1' --depth 2 --json

# 3. 插入新子项行（如有新增）
officecli add "$OUTPUT" '/Sheet1' --type row --index 17 --shift down

# 4. 批量填充数据（原子操作）
echo '[...]' | officecli batch "$OUTPUT" --json

# 5. 设置颜色编码
officecli set "$OUTPUT" '/Sheet1/C17' --prop fill=FF00B050  # Green = In Progress

# 6. 插入照片（Site Photo sheet）
officecli add "$OUTPUT" '/Sheet2' --type image --prop path="photo.jpg" --prop anchor="D13"

# 7. 根据上下文重命名文件
# 文件名格式：TendoCN - {Client Name} - {Project Name} Weekly Progress Report (项目周报) {YYYY-MM-DD}.xlsx
mv "$OUTPUT" "项目目录/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/TendoCN - {Client} - {Project} Weekly Progress Report (项目周报) {DATE}.xlsx"
```

### 错误处理

- 模板文件不存在 → 提示用户检查 references 目录
- officecli 未安装 → 自动安装指引
- 照片插入失败 → 回退到手动插入提示
- 合并单元格冲突 → 使用 `--shift down` 自动处理

## 文件结构

```
skills/tendo-brand/
├── SKILL.md                          ← 技能入口（添加 /weekly-report 触发）
├── scripts/
│   └── weekly-report/
│       └── generate.sh               ← 核心生成脚本（可选，复杂逻辑用）
├── references/
│   └── TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx  ← 周报模板
└── docs/superpowers/specs/
    └── 2026-07-20-weekly-report-workflow-design.md  ← 本文件
```

## 验证标准

1. 复制模板后格式完整（合并单元格、列宽、字体不变）
2. 新增行自动保持合并单元格偏移
3. 颜色编码正确（4种状态对应4种颜色）
4. Site Photo 的 Description 正确反映照片内容
5. Issue/RFA Log 数据完整填充
6. 输出文件可直接在 Excel/WPS 中打开无报错
7. 文件根据上下文正确重命名（Client Name + Project Name + Date）
