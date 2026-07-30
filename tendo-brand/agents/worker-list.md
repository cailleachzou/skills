# Tendo Worker Name List Agent

Fill or update a TendoCN project personnel roster.

## Template
`tendo-brand/references/TendoCN - Worker Name List.xlsx`

## File output
Save as: `TendoCN - Worker Name List - {Project Name}.xlsx`

## Fixed structure — DO NOT change
- Row 8: Title "TendoCN - Worker Name List" (merged A8:K8)
- Column headers (row 9): `No.` | `First Name` | `Last Name` | `Gender` | `Designation` | `Mobile No.` | `Email` | `National ID/Passport No.` | `Nationality` | `Remarks` (A9-J9)
- Table data starts at row 10
- Rows 10-11 have sample data (Wai Kiat Chea / Sai Sai He) — DELETE before filling new project
- Rows 12-15 have pre-filled sequence numbers (3-6) in column A — CLEAR before filling new project

## Fillable fields

| Field | What to fill |
|-------|-------------|
| All 10 columns | One row per team member |
| No. | Sequential number starting at 1 |
| First Name | Given name |
| Last Name | Family name |
| Gender | `M` or `F` |
| Designation | Job title (e.g. Project Director, Sales Manager, Project Engineer) |
| Mobile No. | Full number including country code |
| Email | Company email |
| National ID/Passport No. | ID number — may be blank if N/A |
| Nationality | Country name |
| Remarks | Optional notes |

## Output rules
- Delete sample rows (rows 10-11) and clear pre-filled sequence numbers (rows 12-15) before adding new staff
- Start filling new staff at row 10
- Keep column widths and formatting intact
- Add new rows below row 10 as needed (preserve formatting from row 10)
- Sort by No. ascending
- Nationality use full country name (e.g. "Singapore", "P.R.China")
