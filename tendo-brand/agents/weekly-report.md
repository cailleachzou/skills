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

### Phase 1: Collect project info

Ask the user one at a time:
1. Client name (e.g. "Cooley LLP")
2. Project name (e.g. "Cooley Shanghai Meeting Room Retrofit")
3. Work phases list (e.g. "Cable Pulling, Termination, Faceplate Installation, Testing, Labelling")
4. Sub-items list (e.g. "Reception, Open Office, Executive Office 1/2/3, Meeting Room")
5. Floor identifier (e.g. "L35")

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

> **Note:** These are PLACEHOLDERS — photos will be matched later during Phase 6.

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

# 2. Update metadata cells
officecli set "$OUTPUT" '/Progress Report/D9' --prop value="{DATE}"
officecli set "$OUTPUT" '/Progress Report/D10' --prop value="{Client Name} {Project Name}"

# 3. Insert new sub-item rows if needed (template has 4 items in rows 17-20)
# Use --shift down to preserve merged cells
FOR_EACH new_sub_item:
  officecli add "$OUTPUT" '/Progress Report' --type row --index {insert_at} --shift down

# 4. Batch fill Progress Report data
# Build JSON array of set commands, then:
officecli batch "$OUTPUT" --input data.json --json

# 5. Set FONT COLOR coding per cell (NOT fill color)
# Status → font.color:
#   In Progress → FF00B050 (green)
#   Delay → FFFF0000 (red)
#   Not Started → FFFFC000 (orange)
#   Completed → FF000000 (black)
FOR_EACH phase_column in [C,F,I,L,O,R,U]:
  officecli set "$OUTPUT" '/Progress Report/{col}{row}' --prop font.color={color_hex}

# 6. Set Overall Percentage (column X)
# Calculate average of all phase percentages for each sub-item
officecli set "$OUTPUT" '/Progress Report/X{row}' --prop value={avg_pct}

# 7. Fill Site Photo sheet with placeholders
FOR_EACH photo_placeholder:
  officecli set "$OUTPUT" '/Site Photo/A{row}' --prop value={item_no}
  officecli set "$OUTPUT" '/Site Photo/B{row}' --prop value="{date}"
  officecli set "$OUTPUT" '/Site Photo/C{row}' --prop value="{description_en} ({description_cn})"
  # D column left empty — photos matched later in Phase 6

# 8. Fill Issue Log
FOR_EACH issue:
  officecli set "$OUTPUT" '/Issue_RFA Log/A{row}' --prop value={item_no}
  officecli set "$OUTPUT" '/Issue_RFA Log/B{row}' --prop value={date}
  officecli set "$OUTPUT" '/Issue_RFA Log/C{row}' --prop value="{description}"
  officecli set "$OUTPUT" '/Issue_RFA Log/E{row}' --prop value="{risk}"
  officecli set "$OUTPUT" '/Issue_RFA Log/F{row}' --prop value="{solution}"
  officecli set "$OUTPUT" '/Issue_RFA Log/G{row}' --prop value="{action_by}"
  officecli set "$OUTPUT" '/Issue_RFA Log/I{row}' --prop value="{status}"
  # Issue status uses FILL color: Closed→FF92D050, Open→FFFFC000
  officecli set "$OUTPUT" '/Issue_RFA Log/I{row}' --prop fill={status_color}

# 9. Fill RFI/RFA Log (if any)
FOR_EACH rfa:
  officecli set "$OUTPUT" '/Issue_RFA Log/A{row}' --prop value={item_no}
  ...

# 10. Close and rename
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

## Sheet structure reference

### Progress Report

| Row | Content |
|-----|---------|
| 12 | Phase title (merged C12:W12) |
| 13 | Headers: Item No.(A) \| Description(B) \| Phase1(C-E) \| Phase2(F-H) \| ... \| Overall%(X) |
| 14 | Sub-headers: Floor(B) \| %(C) \| Till Date(D) \| Target Date(E) per phase |
| 16 | Floor ID (B16) |
| 17+ | Data rows: A=seq, B=sub-item name, C-W=phase data |

Each phase = 3 columns: %, Till Date, Target Date

### Site Photo

| Row | Content |
|-----|---------|
| 12 | Headers: Item No. \| Date \| Description \| Photos |
| 13+ | Photo placeholders — text in A/B/C, D column filled during Phase 6 matching |

### Issue_RFA Log

| Row | Content |
|-----|---------|
| 13 | Issue headers: Item No. \| Date \| Issue Description \| Risk \| Solution \| Action By \| Photos \| Status \| Remarks |
| 14+ | Issue entries |
| 18 | "RFI / RFA LOG" title |
| 22 | RFA headers |
| 23+ | RFA entries |

## Color coding

### Progress Report — FONT color (not fill)

| Status | Hex | Meaning |
|--------|-----|---------|
| In Progress | FF00B050 | Green font |
| Delay | FFFF0000 | Red font |
| Not Started | FFFFC000 | Orange font |
| Completed | FF000000 | Black font |

### Issue_RFA Log — FILL color

| Status | Hex | Meaning |
|--------|-----|---------|
| Closed | FF92D050 | Light green fill |
| Open | FFFFC000 | Orange fill |
