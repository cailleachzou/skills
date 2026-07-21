# Tendo Weekly Report Agent

Generate a weekly progress report Excel file by conversational data collection, AI photo understanding, and officecli batch operations.

## Template

```
tendo-brand/references/TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx
```

File name format: `TendoCN - {Client Name} - {Project Name} Weekly Progress Report (项目周报) .xlsx`

## Output location

```
{Project Dir}/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/
```

Final file name: `TendoCN - {Client Name} - {Project Name} Weekly Progress Report (项目周报) {YYYY-MM-DD}.xlsx`

## Workflow phases

### Phase 0: Plan confirmation

Before starting, list the operation plan for user confirmation:
```
Plan:
1. Project info: {Client}, {Project}, {Phases}, {Sub-items}
2. Progress Report: delete rows 16-20, insert {N} phase columns × 3, insert {M} sub-item rows
3. Site Photo: delete rows 13-23, insert {P} photo placeholder rows
4. Issue_RFA Log: delete rows 14-17, insert {Q} issue rows
5. Generate Excel → rename to final filename
Confirm to proceed?
```

### Phase 1: Collect project info

Ask the user one at a time:
1. Client name (e.g. "DBS Bank")
2. Project name (e.g. "L35 Office Retrofit")
3. Work phases list (e.g. "Cable Pulling, Termination, Faceplate Installation, Testing, Labelling")
4. Sub-items list (e.g. "Reception, Open Office, Executive Office 1/2/3, Meeting Room")
5. Floor identifier (e.g. "35F")

### Phase 2: Collect progress data

For each sub-item × phase combination, ask:
- Completion percentage (0-100)
- Status: In Progress / Delay / Not Started / Completed
- Till Date
- Target Date

### Phase 3: Generate photo placeholders

Auto-generate standard photo requirements based on phases × sub-items:

| Phase | Standard photos (bilingual) |
|-------|----------------------------|
| Cable Pulling | Before cable pulling / 穿线前, Cable pulling completed / 穿线完成 |
| Termination | Termination in progress / 端接过程, Termination completed / 端接完成 |
| Faceplate Installation | Faceplate installed / 面板安装 |
| Testing | Test passed / 测试通过 |
| Labelling | Labels completed / 标签完成 |

Present the full list to user for confirmation/modification. Write to Site Photo sheet as placeholders (text only, no photos).

### Phase 4: Issue / RFA collection

Ask:
1. Any new issues this week? → for each: description, risk (Low/Medium/High), solution, action by, status (Open/Closed)
2. Any RFI/RFA? → for each: date, description, issued to, respond by, status

### Phase 5: Generate Excel

```bash
# 1. Copy template
TEMPLATE="tendo-brand/references/TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx"
OUTPUT="{Project Dir}/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/周报.xlsx"
cp "$TEMPLATE" "$OUTPUT"

# ============================================================
# PROGRESS REPORT
# ============================================================

# 2. Delete rows 16-20 (floor ID + sample data)
# officecli remove with shift=up to close gaps
officecli remove "$OUTPUT" '/Progress Report/row[16]' --shift up
officecli remove "$OUTPUT" '/Progress Report/row[16]' --shift up
officecli remove "$OUTPUT" '/Progress Report/row[16]' --shift up
officecli remove "$OUTPUT" '/Progress Report/row[16]' --shift up
officecli remove "$OUTPUT" '/Progress Report/row[16]' --shift up

# 3. Delete existing phase columns (C through W), keep A, B, X
# Remove columns C-W to make room for dynamic phase columns
officecli remove "$OUTPUT" '/Progress Report/col[C]' --shift left
# ... repeat for each column C through W

# 4. Insert N×3 phase columns (N = number of phases)
# Each phase = 3 columns: %, Till Date, Target Date
FOR phase_index FROM 0 TO N-1:
  base_col = column_letter(3 + phase_index * 3)  # C, F, I, L, O, R, U...
  officecli add "$OUTPUT" '/Progress Report' --type col --index {col_number} --shift right
  officecli add "$OUTPUT" '/Progress Report' --type col --index {col_number+1} --shift right
  officecli add "$OUTPUT" '/Progress Report' --type col --index {col_number+2} --shift right

# 5. Update row 12 merged title
officecli set "$OUTPUT" '/Progress Report/C12' --prop value="{Project Title}"
# Merge C12:{last_phase_col}12

# 6. Update row 13 phase headers
FOR_EACH phase at index i:
  col = column_letter(3 + i * 3)
  officecli set "$OUTPUT" '/Progress Report/{col}13' --prop value="{Phase Name}"

# 7. Update row 14 sub-headers (% | Till Date | Target Date per phase)
FOR_EACH phase column base:
  officecli set "$OUTPUT" '/Progress Report/{base}14' --prop value="%"
  officecli set "$OUTPUT" '/Progress Report/{base+1}14' --prop value="Till Date"
  officecli set "$OUTPUT" '/Progress Report/{base+2}14' --prop value="Target Date"

# 8. Insert floor ID row (row 16)
officecli add "$OUTPUT" '/Progress Report' --type row --index 16
officecli set "$OUTPUT" '/Progress Report/B16' --prop value="{Floor ID}"

# 9. Insert sub-item rows (row 17+)
FOR i FROM 0 TO M-1:
  row = 17 + i
  officecli add "$OUTPUT" '/Progress Report' --type row --index {row}
  officecli set "$OUTPUT" '/Progress Report/A{row}' --prop value={i+1}
  officecli set "$OUTPUT" '/Progress Report/B{row}' --prop value="{Sub-item Name}"

# 10. Fill progress data with font colors
# For each sub-item row, for each phase:
FOR_EACH sub_item at row r:
  FOR_EACH phase at index i:
    base_col = column_letter(3 + i * 3)
    # Set % value
    officecli set "$OUTPUT" '/Progress Report/{base_col}{r}' --prop value={pct}
    # Set dates
    officecli set "$OUTPUT" '/Progress Report/{base_col+1}{r}' --prop value="{till_date}"
    officecli set "$OUTPUT" '/Progress Report/{base_col+2}{r}' --prop value="{target_date}"
    # Set FONT color based on status
    officecli set "$OUTPUT" '/Progress Report/{base_col}{r}' --prop font.color={status_color}

# 11. Set Overall Percentage column X with AVERAGE formula
# X column is always the last column after all phases
# Build AVERAGE formula referencing all phase % columns
last_col = column_letter(3 + N * 3 - 3)  # last phase's % column
# Formula: =AVERAGE(C{r},F{r},I{r},L{r},...)
phase_cols = [column_letter(3 + i * 3) for i in range(N)]
formula = "=AVERAGE(" + ",".join([f"{c}{r}" for c in phase_cols]) + ")"
officecli set "$OUTPUT" '/Progress Report/X{r}' --prop value="{formula}"

# ============================================================
# SITE PHOTO
# ============================================================

# 12. Delete rows 13-23 (sample data)
FOR row FROM 13 TO 23:
  officecli remove "$OUTPUT" '/Site Photo/row[13]' --shift up

# 13. Insert photo placeholder rows
FOR_EACH photo_placeholder at index i:
  row = 13 + i
  officecli add "$OUTPUT" '/Site Photo' --type row --index {row}
  officecli set "$OUTPUT" '/Site Photo/A{row}' --prop value={i+1}
  officecli set "$OUTPUT" '/Site Photo/B{row}' --prop value="{date}"
  officecli set "$OUTPUT" '/Site Photo/C{row}' --prop value="{description_en} ({description_cn})"
  # D column left empty — photos matched later

# ============================================================
# ISSUE_RFA LOG
# ============================================================

# 14. Delete rows 14-17 (sample issue data)
FOR row FROM 14 TO 17:
  officecli remove "$OUTPUT" '/Issue_RFA Log/row[14]' --shift up

# 15. Insert issue rows
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
  # Issue status uses FILL color: Closed→FF92D050, Open→FFFFC000
  officecli set "$OUTPUT" '/Issue_RFA Log/I{row}' --prop fill={status_color}

# ============================================================
# FINALIZE
# ============================================================

# 16. Close and rename
officecli close "$OUTPUT"
mv "$OUTPUT" "{Project Dir}/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/TendoCN - {Client} - {Project} Weekly Progress Report (项目周报) {DATE}.xlsx"
```

### Phase 6: Photo matching (separate session, after construction)

When user returns with construction photos:
1. Ask for photo folder path
2. Glob for image files (jpg, jpeg, png, heic)
3. For each image: use MiMo to understand content → generate description
4. Auto-match to existing placeholders in Site Photo sheet by comparing MiMo description with placeholder text
5. Present match results to user for confirmation
6. Fill matched photos into D column of corresponding rows
7. Unmatched photos → prompt user to manually assign or create new entries

## Metadata positions

| Sheet | Field | Cell |
|-------|-------|------|
| Progress Report | Updated On | E9 |
| Progress Report | Project | E10 |
| Site Photo | Updated On | D9 |
| Site Photo | Project | D10 |
| Issue_RFA Log | Project | C11 |

## Column structure (Progress Report)

Dynamic — number of columns = 3 (A,B) + N×3 (phases) + 1 (X=Overall%)

Example with 5 phases:
| A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q | X |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Item | Desc | % | TD | Tgt | % | TD | Tgt | % | TD | Tgt | % | TD | Tgt | % | TD | Tgt | Overall% |

Where: C-E=Cable Pulling, F-H=Termination, I-K=Faceplate, L-N=Testing, O-Q=Labelling

## Row structure (Progress Report)

| Row | Content |
|-----|---------|
| 9 | Updated On: label(A) + value(E) |
| 10 | Project: label(A) + value(E) |
| 12 | Phase title (merged, centered) |
| 13 | Phase headers (merged per 3 cols) |
| 14 | Sub-headers: % | Till Date | Target Date |
| 16 | Floor ID (B16) |
| 17+ | Data rows: A=seq, B=sub-item, phase cols, X=AVERAGE formula |

## Color coding

### Progress Report — FONT color (not fill)

| Status | Hex |
|--------|-----|
| In Progress | FF00B050 |
| Delay | FFFF0000 |
| Not Started | FFFFC000 |
| Completed | FF000000 |

### Issue_RFA Log — FILL color

| Status | Hex |
|--------|-----|
| Closed | FF92D050 |
| Open | FFFFC000 |
