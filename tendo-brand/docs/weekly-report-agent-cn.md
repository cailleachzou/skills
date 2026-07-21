# Tendo 项目周报生成器

通过对话采集进度数据、AI 图片理解、officecli 批量操作，生成项目周报 Excel 文件。

## 模板

```
tendo-brand/references/TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx
```

文件名格式：`TendoCN - {客户名称} - {项目名称} Weekly Progress Report (项目周报) .xlsx`

## 输出位置

```
{项目目录}/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/
```

最终文件名：`TendoCN - {客户名称} - {项目名称} Weekly Progress Report (项目周报) {YYYY-MM-DD}.xlsx`

## 工作流程

### Phase 0: 计划确认

开始前列出操作计划，用户确认后执行：
```
计划：
1. 项目信息：{客户}、{项目}、{阶段}、{子项}
2. Progress Report：删除 row 16-20，插入 {N} 个阶段列 × 3，插入 {M} 个子项行
3. Site Photo：删除 row 13-23，插入 {P} 个照片占位符行
4. Issue_RFA Log：删除 row 14-17，插入 {Q} 个问题行
5. 生成 Excel → 重命名为最终文件名
确认执行？
```

### Phase 1: 采集项目信息

逐项询问用户：
1. 客户名称（如 "DBS Bank"）
2. 项目名称（如 "L35 Office Retrofit"）
3. 工作阶段列表（如 "Cable Pulling, Termination, Faceplate Installation, Testing, Labelling"）
4. 子项列表（如 "Reception, Open Office, Executive Office 1/2/3, Meeting Room"）
5. 楼层标识（如 "35F"）

### Phase 2: 采集进度数据

按 子项 × 阶段 矩阵逐项询问：
- 完成百分比（0-100）
- 状态：In Progress / Delay / Not Started / Completed
- Till Date（实际完成日期）
- Target Date（目标日期）

### Phase 3: 生成照片占位符

根据 阶段 × 子项 自动生成标准照片需求：

| 阶段 | 标准照片（中英文） |
|------|-------------------|
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

### Phase 5: 生成 Excel

```bash
# 1. 复制模板
TEMPLATE="tendo-brand/references/TendoCN - Cooley LLP - ...xlsx"
OUTPUT="{项目目录}/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/周报.xlsx"
cp "$TEMPLATE" "$OUTPUT"

# ============================================================
# PROGRESS REPORT
# ============================================================

# 2. 删除 row 16-20（楼层标识 + 示例数据）
officecli remove "$OUTPUT" '/Progress Report/row[16]'  # 重复5次

# 3. 删除现有阶段列（C-W），保留 A、B、X
officecli remove "$OUTPUT" '/Progress Report/col[C]' --shift left  # 重复删除C-W

# 4. 插入 N×3 个阶段列（N = 阶段数）
# 每个阶段 = 3列：%、Till Date、Target Date
# 按阶段数动态插入列

# 5. 更新 row 12 合并标题
officecli set "$OUTPUT" '/Progress Report/C12' --prop value="{项目标题}"

# 6. 更新 row 13 阶段标题
# 每3列一个阶段标题

# 7. 更新 row 14 子标题（% | Till Date | Target Date）
# 每个阶段重复3个子标题

# 8. 插入楼层标识行（row 16）
officecli set "$OUTPUT" '/Progress Report/B16' --prop value="{楼层}"

# 9. 插入子项行（row 17+）
# 按子项数量动态插入行，设置序号和名称

# 10. 填充进度数据 + 字体颜色
# 每个子项 × 每个阶段：设置%、日期、字体颜色
# 字体颜色：In Progress=绿, Delay=红, Not Started=橙, Completed=黑

# 11. Overall Percentage 列 X — AVERAGE 公式
# =AVERAGE(C{row},F{row},I{row},L{row},O{row})
# 动态引用实际阶段列
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

## 元数据位置

| Sheet | 字段 | 单元格 |
|-------|------|--------|
| Progress Report | Updated On | E9 |
| Progress Report | Project | E10 |
| Site Photo | Updated On | D9 |
| Site Photo | Project | D10 |
| Issue_RFA Log | Project | C11 |

## 列结构（Progress Report）

动态 — 列数 = 3 (A,B) + N×3 (阶段) + 1 (X=Overall%)

5个阶段示例：
| A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q | X |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 序号 | 描述 | % | 完成日 | 目标日 | % | 完成日 | 目标日 | % | 完成日 | 目标日 | % | 完成日 | 目标日 | % | 完成日 | 目标日 | 总进度% |

C-E=穿线, F-H=端接, I-K=面板安装, L-N=测试, O-Q=标签

## 行结构（Progress Report）

| 行 | 内容 |
|----|------|
| 9 | Updated On: 标签(A) + 值(E) |
| 10 | Project: 标签(A) + 值(E) |
| 12 | 阶段总标题（合并居中） |
| 13 | 阶段标题（每3列合并） |
| 14 | 子标题：% \| Till Date \| Target Date |
| 16 | 楼层标识 (B16) |
| 17+ | 数据行：A=序号, B=子项名, 阶段列, X=AVERAGE公式 |

## 颜色编码

### Progress Report — 字体颜色（非填充）

| 状态 | 色值 |
|------|------|
| In Progress | FF00B050（绿） |
| Delay | FFFF0000（红） |
| Not Started | FFFFC000（橙） |
| Completed | FF000000（黑） |

### Issue_RFA Log — 填充颜色

| 状态 | 色值 |
|------|------|
| Closed | FF92D050（浅绿） |
| Open | FFFFC000（橙） |
