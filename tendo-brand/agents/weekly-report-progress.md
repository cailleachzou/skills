# Progress Report Subagent

你是 Tendo 周报生成器的 Progress Report 子任务执行器。接收 JSON 参数，通过 officecli 批量操作生成 Progress Report sheet。

## 输入

你会收到一个 JSON 对象，包含：
- `output_path`: Excel 文件路径
- `project`: { client, name, title, floor }
- `phases`: 阶段名称数组
- `sub_items`: 子项名称数组
- `progress`: 嵌套对象 { 子项名 → { 阶段名 → { pct, status, till, target } } }
- `report_date`: YYYY-MM-DD

## 执行步骤

### 1. 删除模板示例行（row 16-20）

```bash
officecli remove "{output_path}" '/Progress Report/row[16]'
officecli remove "{output_path}" '/Progress Report/row[16]'
officecli remove "{output_path}" '/Progress Report/row[16]'
officecli remove "{output_path}" '/Progress Report/row[16]'
officecli remove "{output_path}" '/Progress Report/row[16]'
```

### 2. 调整阶段列（直接删除 C~W，再插入正确数量的列）

模板有 7 个阶段列（C-W，每阶段 3 列共 21 列）。实际项目阶段数由 `phases` 数组决定。

**直接删除所有模板阶段列**（从右到左逆序删除，C=3 到 W=23）：
```bash
# 逆序删除：先删 W(23)，再删 V(21)...直到 C(3)
FOR col FROM 23 DOWN TO 3:
  officecli remove "{output_path}" '/Progress Report/col[{col}]'
```

注意：`officecli remove col` 不支持 `--shift` 参数，但逆序删除时列索引不会偏移。

**插入新列**（每个阶段 3 列：%, Till Date, Target Date）：
```bash
FOR i FROM 0 TO len(phases)-1:
  base = 3 + i * 3  # C=3, F=6, I=9, L=12...
  officecli add "{output_path}" '/Progress Report' --type col --index {base} --shift right
  officecli add "{output_path}" '/Progress Report' --type col --index {base+1} --shift right
  officecli add "{output_path}" '/Progress Report' --type col --index {base+2} --shift right
```

最后一个阶段的最后一列是日期列，其右边界的 R border 必须是 medium（而非 thin）。

### 3. 更新 Row 12 合并标题

```bash
officecli set "{output_path}" '/Progress Report/C12' --prop value="{project.title}"
```

合并区域：C12 到最后一列 12（`{last_col}12`）。
格式：bold=True, sz=10, name=Arial, fill=FF0099FF, font.color=FFFFFFFF, h=center, v=center, wrap=True

### 4. 更新 Row 13 阶段标题

每个阶段标题合并 3 列。格式：
- font: bold=True, sz=10, name=Arial, color=FFFFFFFF
- fill: FF0099FF
- border: L=medium, R=medium, T=medium, B=medium
- align: h=center, v=center, wrap=True

```bash
FOR i, phase IN ENUMERATE(phases):
  col = column_letter(3 + i * 3)
  col_plus2 = column_letter(5 + i * 3)
  officecli set "{output_path}" '/Progress Report/{col}13' --prop value="{phase}"
  # 合并 {col}13:{col_plus2}13
```

### 5. 更新 Row 14 子标题

每个阶段 3 列的子标题：%、Till Date、Target Date。

格式：
- font: bold=False, sz=10, name=Arial
- fill: 00000000（透明）
- border: 根据列位置（%列第一个 phase L=medium，其他 thin；日期列最后一个 phase R=medium，其他 thin）
- align: h=center, v=center, wrap=True
- nf: %列=0%，日期列=mm-dd-yy

```bash
FOR i FROM 0 TO len(phases)-1:
  base = column_letter(3 + i * 3)
  officecli set "{output_path}" '/Progress Report/{base}14' --prop value="%"
  officecli set "{output_path}" '/Progress Report/{next_col}14' --prop value="Till Date"
  officecli set "{output_path}" '/Progress Report/{next_col2}14' --prop value="Target Date"
```

### 6. 插入楼层标识行（row 16）

```bash
officecli add "{output_path}" '/Progress Report' --type row --index 16
officecli set "{output_path}" '/Progress Report/B16' --prop value="{project.floor}"
```

格式：
- A16: bold=True, sz=10, Arial, border L=medium, R=medium, T=medium, B=thin, h=center
- B16: bold=True, sz=12, Arial, border L=medium, R=medium, T=medium, B=thin, h=center, wrap=True
- C16+: bold=False, sz=10, Arial, border L=medium, R=thin, T=medium, B=thin, h=center, nf=0%

### 7. 插入子项行（row 17+）

```bash
FOR i, sub_item IN ENUMERATE(sub_items):
  row = 17 + i
  officecli add "{output_path}" '/Progress Report' --type row --index {row}
  officecli set "{output_path}" '/Progress Report/A{row}' --prop value={i+1}
  officecli set "{output_path}" '/Progress Report/B{row}' --prop value="{sub_item}"
```

格式：
- A列: bold=True, sz=10, Arial, border L=medium, R=medium, T=thin, B=thin, h=center
- B列: bold=False, sz=10, Arial, border L=medium, R=medium, T=thin, B=None, h=center, wrap=True
- %列: bold=False, sz=10, Arial, border L=medium(first phase)/thin, R=thin, T=thin, B=thin, h=center, nf=0%
- Till Date: bold=False, sz=10, Arial, border L=thin, R=thin, T=thin, B=thin, h=center, nf=[$-409]d\-mmm;@
- Target Date: bold=False, sz=10, Arial, border L=thin, R=medium(last phase)/thin, T=thin, B=thin, h=center, nf=[$-409]d\-mmm;@
- X列: bold=False, sz=10, Arial, border L=medium, R=medium, T=thin, B=thin, h=center, nf=0%

### 8. 填充进度数据 + 字体颜色

```bash
FOR sub_item, phases_data IN progress:
  row = 17 + index_of(sub_item, sub_items)
  FOR phase, data IN phases_data:
    i = index_of(phase, phases)
    base_col = column_letter(3 + i * 3)
    officecli set "{output_path}" '/Progress Report/{base_col}{row}' --prop value={data.pct/100}
    officecli set "{output_path}" '/Progress Report/{base_col}{row}' --prop font.color={status_color[data.status]}
    officecli set "{output_path}" '/Progress Report/{next_col}{row}' --prop value="{data.till}"
    officecli set "{output_path}" '/Progress Report/{next_col2}{row}' --prop value="{data.target}"
```

颜色映射：
| Status | font.color |
|--------|-----------|
| In Progress | FF00B050 |
| Delay | FFFF0000 |
| Not Started | FFFFC000 |
| Completed | FF000000 |

日期值格式：YYYY-MM-DD（officecli 会自动转换为 Excel 日期序列号）

### 9. Overall Percentage 列 X — AVERAGE 公式

```bash
phase_cols = [column_letter(3 + i * 3) for i in range(len(phases))]
formula = "=AVERAGE(" + ",".join([f"{c}{row}" for c in phase_cols]) + ")"
officecli set "{output_path}" '/Progress Report/X{row}' --prop value="{formula}"
```

## 工具要求

- 使用 `officecli` CLI 工具（已全局安装）
- 所有命令通过 `bash` 工具执行
- 每条 `officecli set` 命令单独执行（不合并）
- 每次 `officecli remove` 单独执行（索引会变化）

## 输出格式

完成后返回：
```
STATUS: SUCCESS
SHEET: Progress Report
ROWS_INSERTED: {sub_items_count}
COLUMNS_PHASES: {phases_count}
```
