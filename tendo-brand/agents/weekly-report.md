# Tendo Weekly Report Agent

通过对话采集进度数据、AI 图片理解、officecli 批量操作，生成项目周报 Excel 文件。

## 模板

```
tendo-brand/references/TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx
```

## 输出位置

```
{Project Dir}/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/
```

最终文件名：`TendoCN - {Client Name} - {Project Name} Weekly Progress Report (项目周报) {YYYY-MM-DD}.xlsx`

## 工作流程

### 模式选择

根据用户意图自动选择模式：

| 触发词 | 模式 | 说明 |
|--------|------|------|
| 生成、新建、create、generate | **生成模式** | 从模板创建新周报 |
| 编辑、修改、update、edit、加、改、删 | **编辑模式** | 在已有周报上增量修改 |

### 生成模式（Phase 1-5）

#### Phase 0: 计划确认

开始前列出操作计划，用户确认后执行：
```
Plan:
1. Project info: {Client}, {Project}, {Phases count} phases, {Sub-items count} sub-items
2. Copy template → apply project info → rename
3. Progress Report: delete rows 16-20, insert or delete columns for {N} phases, insert {M} sub-item rows
4. Site Photo: delete rows 13-23, insert {P} photo placeholder rows
5. Issue_RFA Log: delete rows 14-17, insert {Q} issue rows
Confirm to proceed?
```

### Phase 1: 采集项目信息

逐项询问用户：
1. Client name（如 "DBS Bank"）
2. Project name（如 "L35 Office Retrofit"）
3. Work phases list（如 "Cable Pulling, Termination, Faceplate Installation, Testing, Labelling"）
4. Sub-items list（如 "Reception, Open Office, Executive Office 1/2/3, Meeting Room"）
5. Floor identifier（如 "35F"）
6. Project directory 路径

### Phase 2: 采集进度数据

按 子项 × 阶段 矩阵逐项询问：
- Completion percentage（0-100）
- Status: In Progress / Delay / Not Started / Completed
- Till Date
- Target Date

### Phase 3: 生成照片占位符

根据 阶段 × 子项 自动生成标准照片需求：

| Phase | Standard photos (bilingual) |
|-------|----------------------------|
| Cable Pulling | Before cable pulling / 穿线前, Cable pulling completed / 穿线完成 |
| Termination | Termination in progress / 端接过程, Termination completed / 端接完成 |
| Faceplate Installation | Faceplate installed / 面板安装 |
| Testing | Test passed / 测试通过 |
| Labelling | Labels completed / 标签完成 |

展示完整列表供用户确认/修改。写入 Site Photo sheet 作为占位符（仅文字，无照片）。

### Phase 4: 采集 Issue / RFA

询问：
1. 本周是否有新问题？→ 逐项采集：描述、风险（Low/Medium/High）、方案、负责人、状态（Open/Closed）
2. 是否有 RFI/RFA？→ 逐项采集：日期、描述、发送对象、回复期限、状态

### Phase 5: 生成 Excel — 串行 Subagent Pipeline

采集完所有数据后，按以下步骤串行执行：

#### Step 0: 复制模板

```bash
TEMPLATE="C:/Users/59620/.claude/skills/tendo-brand/references/TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx"
OUTPUT="{Project Dir}/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/周报.xlsx"
cp "$TEMPLATE" "$OUTPUT"
```

#### Step 1-3: 串行执行三个 Subagent

每个 subagent 通过 `actor` 工具启动，传入精确的 JSON 参数。subagent 完成后返回成功/失败状态。

```
Subagent 1: weekly-report-progress  → Progress Report sheet
Subagent 2: weekly-report-photo     → Site Photo sheet
Subagent 3: weekly-report-issue     → Issue_RFA Log sheet
```

**调用格式**：
```
actor spawn:
  subagent_type: general
  description: "Generate Progress Report sheet"
  prompt: (读取 agents/weekly-report-progress.md + 注入 JSON 参数)
```

**JSON 参数模板**（传给每个 subagent）：
```json
{
  "output_path": "{OUTPUT}",
  "project": { "client": "...", "name": "...", "title": "...", "floor": "..." },
  "phases": ["Cable Pulling", "Termination", ...],
  "sub_items": ["Reception", "Open Office", ...],
  "progress": {
    "Reception": {
      "Cable Pulling": { "pct": 100, "status": "Completed", "till": "2026-07-14", "target": "2026-07-14" },
      "Termination": { "pct": 50, "status": "In Progress", "till": "2026-07-18", "target": "2026-07-25" }
    }
  },
  "issues": [
    { "date": "2026-07-14", "description": "...", "risk": "Medium", "solution": "...", "action_by": "Cailleach", "status": "Open" }
  ],
  "rfas": [
    { "date": "2026-07-15", "type": "RFI", "description": "...", "issued_to": "...", "respond_by": "2026-07-22", "status": "Open" }
  ],
  "photo_placeholders": [
    { "sub_item": "Reception", "phase": "Cable Pulling", "description": "Before cable pulling / 穿线前" }
  ],
  "report_date": "2026-07-20"
}
```

#### Step 4: 写入元数据（所有 subagent 完成后）

```bash
# 更新所有 sheet 的日期和项目信息
officecli set "$OUTPUT" '/Progress Report/E9' --prop value="{YYYY-MM-DD}"
officecli set "$OUTPUT" '/Progress Report/E10' --prop value="{Client Name} - {Project Name}"
officecli set "$OUTPUT" '/Site Photo/D9' --prop value="{YYYY-MM-DD}"
officecli set "$OUTPUT" '/Site Photo/D10' --prop value="{Client Name} - {Project Name}"
officecli set "$OUTPUT" '/Issue_RFA Log/C11' --prop value="{Client Name} - {Project Name}"

# 关闭文件
officecli close "$OUTPUT"

# 重命名为最终文件名
mv "$OUTPUT" "{Project Dir}/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/TendoCN - {Client} - {Project} Weekly Progress Report (项目周报) {DATE}.xlsx"
```

### Phase 6: 照片匹配（后续会话）

用户施工完成后返回：
1. 询问照片文件夹路径
2. 扫描图片文件（jpg, jpeg, png, heic）
3. MiMo 理解每张照片内容 → 生成描述
4. 自动匹配到 Site Photo 占位符（对比 MiMo 描述与占位符文字）
5. 展示匹配结果供用户确认
6. 匹配成功的照片填入对应行的 D 列
7. 未匹配的照片 → 提示用户手动指定或新建条目

---

### 编辑模式（Edit Mode）

在已有周报上增量修改，不重新生成。

#### Edit Phase 0: 定位现有文件

```bash
# 搜索项目目录下已有的周报文件
ls "{Project Dir}/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/"
```

如果只有一个文件，直接使用。如果有多个，让用户选择。

#### Edit Phase 1: 读取当前状态

用 `officecli get` 读取关键信息，确认当前结构：

```bash
# 读取 Progress Report 阶段列标题（row 13）
# 读取子项列表（B17, B18, ...）
# 读取 Issue_RFA Log 现有问题数
```

向用户展示当前结构摘要：
```
Current structure:
- Phases: Cable Pulling, Termination, Faceplate Installation (3 phases)
- Sub-items: Reception, Open Office, Meeting Room (3 sub-items)
- Issues: 2 open, 1 closed
- RFI/RFA: 1 open
What would you like to change?
```

#### Edit Phase 2: 执行增量修改

根据用户指令，分类处理：

**A. 新增阶段**（如 "加一套安防系统"）
```
用户: "加一个 CCTV Installation 阶段"
→ 插入 3 列（%, Till Date, Target Date）到指定位置
→ 更新 row 12 合并标题
→ 更新 row 13 阶段标题
→ 更新 row 14 子标题
→ 为所有子项设置新阶段的默认进度（0%, Not Started）
→ 更新 AVERAGE 公式（X 列）
→ 在 Site Photo 中插入对应的占位符行
```

**B. 删除阶段**
```
用户: "删掉 Labelling 阶段"
→ 删除对应 3 列
→ 更新 row 12 合并标题
→ 更新 AVERAGE 公式
→ 删除 Site Photo 中对应的占位符行
```

**C. 新增子项**（如 "多了一个会议室"）
```
用户: "加一个 VIP Meeting Room"
→ 插入新行到指定位置
→ 设置序号、名称
→ 为所有阶段设置默认进度
→ 在 Site Photo 中插入对应的占位符行
```

**D. 修改进度数据**
```
用户: "Reception 的 Cable Pulling 改成 80%，In Progress"
→ officecli set 指定单元格的值和字体颜色
```

**E. 调整日期**
```
用户: "Termination 目标日期推迟到 7/30"
→ officecli set 指定 Target Date 单元格
```

**F. 新增问题**
```
用户: "加一个问题：现场发现线缆规格不对"
→ 在 Issue_RFA Log 插入新行
→ 填写描述、风险、方案、负责人、状态
```

**G. 新增 RFI/RFA**
```
用户: "加一个 RFI：问甲方桥架走向"
→ 在 RFI/RFA 区域插入新行
→ 填写日期、类型、描述、发送对象、回复期限、状态
```

**H. 添加/匹配照片**（施工进度更新的核心场景）
```
用户: "这批是这周拍的照片" / "加照片" / "匹配照片"
→ 进入照片识别+匹配流程（见下方 Edit Phase 2-H）
```

#### Edit Phase 2-H: 照片识别 + 匹配

这是编辑模式中最常用的流程——项目随施工进度逐步补充照片。

**Step 1: 询问照片来源**
```
请提供照片文件夹路径（支持 jpg, jpeg, png, heic）
```

**Step 2: 扫描 + MiMo 理解**
```bash
# 扫描文件夹中的图片
ls "{photo_folder}"/*.jpg "{photo_folder}"/*.jpeg "{photo_folder}"/*.png "{photo_folder}"/*.heic
```

对每张照片使用 MiMo 多模态理解，生成描述：
```
照片 1: "Reception 区域穿线完成，蓝色网线已入桥架"
照片 2: "Meeting Room 端接进行中，标签已贴"
照片 3: "Open Office 面板安装完成"
```

**Step 3: 读取现有占位符**
```bash
# 读取 Site Photo sheet 当前内容
# C 列 = 占位符描述（如 "Before cable pulling / 穿线前"）
# D 列 = 照片（当前为空或已有照片）
```

**Step 4: 自动匹配**
将 MiMo 生成的描述与占位符文字进行语义匹配：

| MiMo 描述 | 占位符 | 匹配度 |
|-----------|--------|--------|
| "Reception 穿线完成" | "Cable pulling completed / 穿线完成" (Reception) | 高 |
| "Meeting Room 端接进行中" | "Termination in progress / 端接过程" (Meeting Room) | 高 |
| "Open Office 面板安装完成" | "Faceplate installed / 面板安装" (Open Office) | 高 |

**Step 5: 展示匹配结果**
```
照片匹配结果：
✅ 照片 1 → Reception / Cable pulling completed (行 15)
✅ 照片 2 → Meeting Room / Termination in progress (行 20)
✅ 照片 3 → Open Office / Faceplate installed (行 18)

未匹配的照片：
❓ 照片 4: "走廊桥架安装" → 无对应占位符
   → 新建占位符？还是跳过？

确认写入？
```

**Step 6: 写入照片**
匹配成功的照片 → 将文件路径写入对应行的 D 列：
```bash
officecli set "$OUTPUT" '/Site Photo/D{row}' --prop value="{photo_filename}"
```

未匹配的照片 → 用户选择：
- 新建占位符行（自动插入到对应子项+阶段的位置）
- 跳过（不处理）

#### Edit Phase 3: 更新元数据

```bash
# 更新所有 sheet 的日期
officecli set "$OUTPUT" '/Progress Report/E9' --prop value="{YYYY-MM-DD}"
officecli set "$OUTPUT" '/Site Photo/D9' --prop value="{YYYY-MM-DD}"
```

#### Edit Phase 4: 确认变更

展示修改摘要，用户确认后完成：
```
Changes applied:
- [A] Added phase: CCTV Installation (3 columns inserted at position 4)
- [D] Updated: Reception / Cable Pulling → 80%, In Progress
- [F] Added issue: "线缆规格不对" (Medium, Open)
- [H] Matched 3 photos, 1 new placeholder created
Metadata updated: date → 2026-07-20
```

## 颜色编码

### Progress Report — 字体颜色（非填充）

| Status | Hex |
|--------|-----|
| In Progress | FF00B050 |
| Delay | FFFF0000 |
| Not Started | FFFFC000 |
| Completed | FF000000 |

### Issue_RFA Log — 填充颜色

| Status | Hex |
|--------|-----|
| Closed | FF92D050 |
| Open | FFFFC000 |
