# Tendo Weekly Report Agent

通过对话采集进度数据、AI 图片理解、officecli 批量操作，生成项目周报 Excel 文件。

## 模板

```
tendo-brand/references/TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx
```

文件名格式：`TendoCN - {Client Name} - {Project Name} Weekly Progress Report (项目周报) .xlsx`

## 输出位置

```
{Project Dir}/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/
```

最终文件名：`TendoCN - {Client Name} - {Project Name} Weekly Progress Report (项目周报) {YYYY-MM-DD}.xlsx`

## 工作流程

### Phase 0: 计划确认

开始前列出操作计划，用户确认后执行：
```
Plan:
1. Project info: {Client}, {Project}, {Phases}, {Sub-items}
2. Progress Report: delete rows 16-20, insert or delete {N} phase columns × 3, insert {M} sub-item rows
3. Site Photo: delete rows 13-23, insert {P} photo placeholder rows
4. Issue_RFA Log: delete rows 14-17, insert {Q} issue rows
5. Generate Excel → rename to final filename
Confirm to proceed?
```

### Phase 1: 采集项目信息

逐项询问用户：
1. Client name（如 "DBS Bank"）
2. Project name（如 "L35 Office Retrofit"）
3. Work phases list（如 "Cable Pulling, Termination, Faceplate Installation, Testing, Labelling"）
4. Sub-items list（如 "Reception, Open Office, Executive Office 1/2/3, Meeting Room"）
5. Floor identifier（如 "35F"）

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

### Phase 5: 生成 Excel

```bash
# 1. 复制模板
TEMPLATE="tendo-brand/references/TendoCN - Cooley LLP - ...xlsx"
OUTPUT="{Project Dir}/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/周报.xlsx"
cp "$TEMPLATE" "$OUTPUT"

# ============================================================
# PROGRESS REPORT
# ============================================================

# 2. 删除 row 16-20（楼层标识 + 示例数据）
# 注意：officecli remove row 不支持 --shift，直接删除即可
officecli remove "$OUTPUT" '/Progress Report/row[16]'  # 重复5次

# 3. 插入或删除阶段列（动态）
# 模板有7个阶段列（C-W，每列3个=21列）
# 实际项目可能少于或多于7个阶段
# 操作：先删除所有阶段列（C-W），再按需插入 N×3 列
#
# 删除阶段列：
FOR col FROM W DOWN TO C:
  officecli remove "$OUTPUT" '/Progress Report/col[{col}]' --shift left
#
# 插入新列（每个阶段3列：%, Till Date, Target Date）：
FOR phase_index FROM 0 TO N-1:
  col_num = 3 + phase_index * 3  # C=3, F=6, I=9...
  officecli add "$OUTPUT" '/Progress Report' --type col --index {col_num} --shift right
  officecli add "$OUTPUT" '/Progress Report' --type col --index {col_num+1} --shift right
  officecli add "$OUTPUT" '/Progress Report' --type col --index {col_num+2} --shift right

# 4. 更新 row 12 合并标题
officecli set "$OUTPUT" '/Progress Report/C12' --prop value="{Project Title}"
# 合并 C12:{last_col}12
# 格式：bold=True, sz=10, name=Arial, fill=FF0099FF, font.color=FFFFFFFF, h=center, v=center, wrap=True

# 5. 更新 row 13 阶段标题
# 格式：bold=True, sz=10, name=Arial, font.color=FFFFFFFF, fill=FF0099FF
# border: L=medium, R=medium, T=medium, B=medium
# align: h=center, v=center, wrap=True
# 每3列合并一个阶段标题
FOR_EACH phase at index i:
  col = column_letter(3 + i * 3)
  officecli set "$OUTPUT" '/Progress Report/{col}13' --prop value="{Phase Name}"
  # 合并 {col}13:{col+2}13

# 6. 更新 row 14 子标题
# 格式：bold=False, sz=10, name=Arial, fill=00000000
# % 列：border L=medium(first phase)/thin(other), R=thin, T=medium, B=medium, h=center, nf=0%
# Till Date 列：border L=thin, R=None, T=medium, B=medium, h=center, v=center, wrap=True, nf=mm-dd-yy
# Target Date 列：border L=thin, R=medium(last col)/thin(other), T=medium, B=medium, h=center, v=center, wrap=True, nf=mm-dd-yy
FOR_EACH phase column base:
  officecli set "$OUTPUT" '/Progress Report/{base}14' --prop value="%"
  officecli set "$OUTPUT" '/Progress Report/{base+1}14' --prop value="Till Date"
  officecli set "$OUTPUT" '/Progress Report/{base+2}14' --prop value="Target Date"

# 7. 插入楼层标识行（row 16）
# 格式：bold=True, sz=10(A)/12(B), name=Arial, fill=00000000
# border: L=medium, R=medium(B)/thin(C), T=medium, B=thin
# align: h=center, wrap=True(B)
officecli add "$OUTPUT" '/Progress Report' --type row --index 16
officecli set "$OUTPUT" '/Progress Report/B16' --prop value="{Floor ID}"

# 8. 插入子项行（row 17+）
# A列格式：bold=True, sz=10, name=Arial, border L=medium, R=medium, T=thin, B=thin, h=center
# B列格式：bold=False, sz=10, name=Arial, border L=medium, R=medium, T=thin, B=None, h=center, wrap=True
# %列格式：bold=False, sz=10, name=Arial, border L=medium(first phase)/thin, R=thin, T=thin, B=thin, h=center, nf=0%
# 日期列格式：bold=False, sz=10, name=Arial, border L=thin, R=thin/medium(last), T=thin, B=thin, h=center, nf=[$-409]d\-mmm;@
# X列格式：bold=False, sz=10, name=Arial, border L=medium, R=medium, T=thin, B=thin, h=center, nf=0%
FOR i FROM 0 TO M-1:
  row = 17 + i
  officecli add "$OUTPUT" '/Progress Report' --type row --index {row}
  officecli set "$OUTPUT" '/Progress Report/A{row}' --prop value={i+1}
  officecli set "$OUTPUT" '/Progress Report/B{row}' --prop value="{Sub-item Name}"

# 9. 填充进度数据 + 字体颜色
FOR_EACH sub_item at row r:
  FOR_EACH phase at index i:
    base_col = column_letter(3 + i * 3)
    officecli set "$OUTPUT" '/Progress Report/{base_col}{r}' --prop value={pct}
    officecli set "$OUTPUT" '/Progress Report/{base_col+1}{r}' --prop value="{till_date}"
    officecli set "$OUTPUT" '/Progress Report/{base_col+2}{r}' --prop value="{target_date}"
    officecli set "$OUTPUT" '/Progress Report/{base_col}{r}' --prop font.color={status_color}

# 10. Overall Percentage 列 X — AVERAGE 公式
phase_cols = [column_letter(3 + i * 3) for i in range(N)]
formula = "=AVERAGE(" + ",".join([f"{c}{r}" for c in phase_cols]) + ")"
officecli set "$OUTPUT" '/Progress Report/X{r}' --prop value="{formula}"

# ============================================================
# SITE PHOTO
# ============================================================

# 11. 删除 rows 13-23（示例数据）
FOR row FROM 13 TO 23:
  officecli remove "$OUTPUT" '/Site Photo/row[13]'

# 12. 插入照片占位符行
# A列格式：bold=True, sz=10, name=Arial, border L=medium, R=thin, T=None, B=thin, h=center, v=center
# B列格式：bold=False, sz=10, name=Arial, border L=None, R=thin, T=None, B=thin, h=center, v=center, nf=dd/mm/yyyy;@
# C列格式：bold=False, sz=10, name=Arial, border L=thin, R=thin, T=None, B=thin, h=center, v=center, wrap=True
# D列格式：bold=True, sz=10, name=Arial, border L=thin, R=thin, T=None, B=thin, h=center, v=center, wrap=True（留空）
FOR_EACH photo_placeholder at index i:
  row = 13 + i
  officecli add "$OUTPUT" '/Site Photo' --type row --index {row}
  officecli set "$OUTPUT" '/Site Photo/A{row}' --prop value={i+1}
  officecli set "$OUTPUT" '/Site Photo/B{row}' --prop value="{date}"
  officecli set "$OUTPUT" '/Site Photo/C{row}' --prop value="{description_en} ({description_cn})"

# ============================================================
# ISSUE_RFA LOG
# ============================================================

# 13. 删除 rows 14-17（示例数据）
FOR row FROM 14 TO 17:
  officecli remove "$OUTPUT" '/Issue_RFA Log/row[14]'

# 14. 插入问题行
# A列格式：bold=False, sz=10, name=Arial, border L=thin, R=thin, T=thin, B=thin, h=center, v=center, wrap=True
# B列格式：bold=False, sz=10, name=Arial, border L=thin, R=thin, T=thin, B=thin, h=center, v=center, wrap=True
# C列格式：bold=False, sz=10, name=Calibri, border L=thin, R=thin, T=thin, B=thin, h=left, v=center, wrap=True
# E列格式：bold=False, sz=10, name=Arial, border L=thin, R=thin, T=thin, B=thin, h=center, v=center, wrap=True
# F列格式：bold=False, sz=10, name=Arial, border L=thin, R=thin, T=thin, B=thin, h=left, v=center, wrap=True
# G列格式：bold=False, sz=10, name=Arial, border L=thin, R=thin, T=thin, B=thin, h=center, v=center, wrap=True
# I列格式：bold=False, sz=10, name=Calibri, border L=thin, R=thin, T=thin, B=thin, h=center, v=center, wrap=True
#   Closed: fill=FF92D050, Open: fill=FFFFC000
# J列格式：bold=True, sz=10, name=Arial, border L=thin, R=medium, T=thin, B=thin, h=center, v=center, wrap=True
FOR_EACH issue at index i:
  row = 14 + i
  officecli add "$OUTPUT" '/Issue_RFA Log' --type row --index {row}
  officecli set "$OUTPUT" '/Issue_RFA Log/A{row}' --prop value={i+1}
  officecli set "$OUTPUT" '/Issue_RFA Log/B{row}' --prop value="{date}"
  officecli set "$OUTPUT" '/Issue_RFA Log/C{row}' --prop value="{description}"
  officecli set "$OUTPUT" '/Issue_RFA Log/E{row}' --prop value="{risk}"
  officecli set "$OUTPUT" '/Issue_RFA Log/F{row}' --prop value="{solution}"
  officecli set "$OUTPUT" '/Issue_RFA Log/G{row}' --prop value="{action_by}"
  officecli set "$OUTPUT" '/Issue_RFA Log/I{row}' --prop value="{status}"
  officecli set "$OUTPUT" '/Issue_RFA Log/I{row}' --prop fill={status_color}

# ============================================================
# FINALIZE
# ============================================================

# 15. 关闭并重命名
officecli close "$OUTPUT"
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

## 元数据位置

| Sheet | Field | Cell |
|-------|-------|------|
| Progress Report | Updated On | E9 |
| Progress Report | Project | E10 |
| Site Photo | Updated On | D9 |
| Site Photo | Project | D10 |
| Issue_RFA Log | Project | C11 |

## 格式规范（必须严格匹配）

### Progress Report

#### Row 13 — 阶段标题
| 属性 | 值 |
|------|-----|
| font | bold=True, sz=10, name=Arial, color=FFFFFFFF |
| fill | FF0099FF（蓝底） |
| border | L=medium, R=medium, T=medium, B=medium |
| align | h=center, v=center, wrap=True |
| 合并 | 每3列合并（C13:E13, F13:H13...） |

#### Row 14 — 子标题
| 列类型 | font | border | align | nf |
|--------|------|--------|-------|-----|
| % | bold=False, sz=10, Arial | L=medium(first)/thin, R=thin, T=medium, B=medium | h=center | 0% |
| Till Date | bold=False, sz=10, Arial | L=thin, R=None, T=medium, B=medium | h=center, v=center, wrap=True | mm-dd-yy |
| Target Date | bold=False, sz=10, Arial | L=thin, R=medium(last)/thin, T=medium, B=medium | h=center, v=center, wrap=True | mm-dd-yy |

#### Row 16 — 楼层标识
| 列 | font | border | align |
|----|------|--------|-------|
| A | bold=True, sz=10, Arial | L=medium, R=medium, T=medium, B=thin | h=center |
| B | bold=True, sz=12, Arial | L=medium, R=medium, T=medium, B=thin | h=center, wrap=True |
| C+ | bold=False, sz=10, Arial | L=medium, R=thin, T=medium, B=thin | h=center, nf=0% |

#### Row 17+ — 数据行
| 列类型 | font | border | align | nf |
|--------|------|--------|-------|-----|
| A (序号) | bold=True, sz=10, Arial | L=medium, R=medium, T=thin, B=thin | h=center | General |
| B (描述) | bold=False, sz=10, Arial | L=medium, R=medium, T=thin, B=None | h=center, wrap=True | General |
| % (每阶段首列) | bold=False, sz=10, Arial | L=medium(first phase)/thin, R=thin, T=thin, B=thin | h=center | 0% |
| Till Date | bold=False, sz=10, Arial | L=thin, R=thin, T=thin, B=thin | h=center | [$-409]d\-mmm;@ |
| Target Date | bold=False, sz=10, Arial | L=thin, R=medium(last phase)/thin, T=thin, B=thin | h=center | [$-409]d\-mmm;@ |
| X (Overall%) | bold=False, sz=10, Arial | L=medium, R=medium, T=thin, B=thin | h=center | 0% |

### Site Photo

#### Row 12 — 表头
| 属性 | 值 |
|------|-----|
| font | bold=True, sz=10, Arial, color=FFFFFFFF |
| fill | FF0099FF |
| border | L=medium(A)/thin(B-D), R=thin(B-D)/None(D), T=medium, B=medium |
| align | h=center, v=center, wrap=True |

#### Row 13+ — 数据行
| 列 | font | border | align | nf |
|----|------|--------|-------|-----|
| A (序号) | bold=True, sz=10, Arial | L=medium, R=thin, T=None, B=thin | h=center, v=center | General |
| B (日期) | bold=False, sz=10, Arial | L=None, R=thin, T=None, B=thin | h=center, v=center | [$-409]d\-mmm;@ |
| C (描述) | bold=False, sz=10, Arial | L=thin, R=thin, T=None, B=thin | h=center, v=center, wrap=True | General |
| D (照片) | bold=True, sz=10, Arial | L=thin, R=thin, T=None, B=thin | h=center, v=center, wrap=True | General |

### Issue_RFA Log

#### Row 13 — 表头
| 属性 | 值 |
|------|-----|
| font | bold=True, sz=10, Arial, color=FFFFFFFF |
| fill | FF0099FF |
| border | L=medium(A)/thin(C-J), R=thin(C-I)/medium(J), T=medium, B=medium |
| align | h=center, v=center, wrap=True |

#### Row 14+ — 数据行
| 列 | font | border | align | nf |
|----|------|--------|-------|-----|
| A (序号) | bold=False, sz=10, Arial | L=thin, R=thin, T=thin, B=thin | h=center, v=center, wrap=True | General |
| B (日期) | bold=False, sz=10, Arial | L=thin, R=thin, T=thin, B=thin | h=center, v=center, wrap=True | General |
| C (描述) | bold=False, sz=10, Calibri | L=thin, R=thin, T=thin, B=thin | h=left, v=center, wrap=True | General |
| D (空) | bold=False, sz=10, Arial | L=None, R=thin, T=thin, B=thin | — | General |
| E (风险) | bold=False, sz=10, Arial | L=thin, R=thin, T=thin, B=thin | h=center, v=center, wrap=True | General |
| F (方案) | bold=False, sz=10, Arial | L=thin, R=thin, T=thin, B=thin | h=left, v=center, wrap=True | General |
| G (负责人) | bold=False, sz=10, Arial | L=thin, R=thin, T=thin, B=thin | h=center, v=center, wrap=True | General |
| H (照片) | bold=False, sz=10, Calibri | L=thin, R=thin, T=thin, B=thin | h=center, v=center, wrap=True | General |
| I (状态) | bold=False, sz=10, Calibri | L=thin, R=thin, T=thin, B=thin | h=center, v=center, wrap=True | General |
| I (Closed) | fill=FF92D050 | | | |
| I (Open) | fill=FFFFC000 | | | |
| J (备注) | bold=True, sz=10, Arial | L=thin, R=medium, T=thin, B=thin | h=center, v=center, wrap=True | General |

#### Row 18 — RFI/RFA 标题
| 属性 | 值 |
|------|-----|
| font | bold=True, sz=18, Arial |
| align | h=center, v=center |

#### Row 20 — 项目名
| 列 | 属性 |
|----|------|
| A20 | bold=True, sz=12, Arial, val="Project :" |
| C20 | bold=True, sz=12, Arial, val="{Project Name}" |

#### Row 22 — RFI/RFA 表头
| 列 | font | fill | border | align |
|----|------|------|--------|-------|
| A (Item No.) | bold=True, sz=10, Arial, color=FFFFFFFF | FF0099FF | L=medium, R=thin, T=medium, B=medium | h=center, v=center, wrap=True |
| B (Issued Date) | bold=True, sz=10, Arial, color=FFFFFFFF | FF0099FF | L=None, R=thin, T=medium, B=medium | h=center, v=center, wrap=True |
| C (RFI / RFA) | bold=True, sz=10, Arial, color=FFFFFFFF | FF0099FF | L=thin, R=thin, T=medium, B=medium | h=center, v=center, wrap=True |
| E (Description) | bold=True, sz=10, Arial, color=FFFFFFFF | FF0099FF | L=thin, R=thin, T=medium, B=medium | h=center, v=center, wrap=True |
| F (Issued to) | bold=True, sz=10, Arial, color=FFFFFFFF | FF0099FF | L=thin, R=thin, T=medium, B=medium | h=center, v=center, wrap=True |
| G (Respond by) | bold=True, sz=10, Arial, color=FFFFFFFF | FF0099FF | L=thin, R=thin, T=medium, B=medium | h=center, v=center, wrap=True |
| I (Open/Closed) | bold=True, sz=10, Arial, color=FFFFFFFF | FF0099FF | L=thin, R=None, T=medium, B=medium | h=center, v=center, wrap=True |
| J (Remarks) | bold=True, sz=10, Arial, color=FFFFFFFF | FF0099FF | L=thin, R=medium, T=medium, B=medium | h=center, v=center, wrap=True |

#### Row 23+ — RFI/RFA 数据行
| 列 | font | border | align | nf |
|----|------|--------|-------|-----|
| A (序号) | bold=True, sz=10, Arial | L=medium, R=thin, T=None, B=thin | h=center, v=center | General |
| B (日期) | bold=False, sz=10, Arial | — | h=center, v=center | [$-409]d\-mmm;@ |
| C (RFI/RFA) | bold=False, sz=10, Arial | — | h=center, v=center, wrap=True | General |
| E (描述) | bold=False, sz=10, Arial | — | h=left, v=center, wrap=True | General |
| F (发送对象) | bold=False, sz=10, Arial | — | h=center, v=center, wrap=True | General |
| G (回复期限) | bold=False, sz=10, Arial | — | h=center, v=center | [$-409]d\-mmm;@ |
| I (状态) | bold=False, sz=10, Calibri | — | h=center, v=center, wrap=True | General |
| J (备注) | bold=False, sz=10, Arial | — | h=center, v=center, wrap=True | General |

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
