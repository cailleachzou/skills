# Tendo Rack Elevation Agent

Fill or update a TendoCN server room rack elevation drawing.

## Template
`tendo-brand/references/TendoCN - Proposed (Client Name 客户名称) (Project Name 项目名称) Rack Elevation.xls`

## File output
Save as: `TendoCN - Proposed {Client Name} {Project Name} Rack Elevation.xls`

## Grid layout (DO NOT change)
- 45 rows (U45 at top, U1 at bottom) — represents 45U rack height
- Rack 1 Front occupies columns ~7–12
- Rack 2 Front occupies columns ~14–19
- Rack 1 Rear occupies columns ~22–27
- Rack 2 Rear occupies columns ~28–33
- U-number labels in column B (Rack 1 side) and column T (Rack 2 side)

## Fillable metadata fields (right side panel, columns U–W)

| Cell location | Field | Example |
|---------------|-------|---------|
| Row 28, col U | Location line 1 | Building B, Unit 206 |
| Row 29, col U | Location line 2 | No. 135 Yanping Road, Jingan District |
| Row 30, col U | Location line 3 | Shanghai, P.R.China |
| Row 25, col U | PROJECT label + name | Fit Out Project |
| Row 21, col U | PROJECT ADDRESS label | (merged cells) |
| Row 15, col U | DRAWN BY | B.H |
| Row 15, col V | DESIGNED BY | (name) |
| Row 13, col U | APPROVED | D.C |
| Row 13, col V | CHECKED BY | S.H |
| Row 12, col U | DATE with date | DATE: 27th Feb' 25 |
| Row 10, col U | PROJECT NO | (project number) |
| Row 6, col U | DRAWING TITLE | S-SH-23F-RL |
| Row 42, col U | REVISION | A, B, C... |
| Row 42, col V | DATE | ddth Mmm' yy |

## Rack content fields
- Rows 2–44: equipment slot labels (free text per U)
  - Row 2: "2U Reserved for incoming cable bend radius" (keep this)
  - Fill each U cell with equipment description: e.g. "Patch Panel 24P", "Server 1U", "UPS 3U", "Switch 1U", "Blank Panel 1U"
- Rack numbering: Rack 1 and Rack 2 (front label row near top)
- Rear sections mirror front with same layout

## Output rules
- Preserve exact column positions — rack grid is fixed
- Do not merge/unmerge cells
- Keep U-number sequence intact (45→1, top→bottom)
- Use standard rack unit abbreviations: U (unit), P (port), kVA (power)
- Equipment naming: [Type] [Port-count or Size] — e.g. "Patch Panel 24P", "Server 2U", "UPS 3kVA"
