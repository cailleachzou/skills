# cli-anything — Routerized Redesign
**Date** : 2026-06-15
**Authors** : DUDU & Cailleach
**Status** : Approved, Implementation Phase
---
## Objective
Merge 6 independent CLI skills (umi-ocr / dxf-dwg-converter / cli-anything-ffmpeg / cli-anything-pdf2zh / cli-anything-web-search-fast / mimo-multimodal) into one **router-type meta-skill** — `cli-anything/`, using a "selector + secondary loading" model.
**Motivation**:
- All 6 skills are of the "CLI Manual" nature (wrapping external CLI tools), with no essential differences.
- A unified entry point reduces the user's cognitive load ("use CLI tools" → router → hit sub-skill).
- Simplifies subsequent expansion (add new CLI = write sub SKILL.md + add one line in router index).
---
## Architecture
### Nested Layout
```
cli-anything/                      ← The only external entry point
├── SKILL.md                       ← Router (handwritten)
└── sub-skills/                    ← 6 sub-skills
    ├── ffmpeg/                    ← Original cli-anything-ffmpeg
    ├── pdf2zh/                    ← Original cli-anything-pdf2zh
    ├── web-search-fast/           ← Original cli-anything-web-search-fast
    ├── ocr/                       ← Renamed umi-ocr
    ├── dwg/                       ← Renamed dxf-dwg-converter
    └── mimo/                      ← Renamed mimo-multimodal
```
**Key Premise**: Sub-skills are in `sub-skills/`, and Claude does not automatically discover them when starting. The only thing automatically discovered is `cli-anything/SKILL.md`. All calls go through the router entry.
### Workflow (Secondary Loading)
```
User: "Help me OCR this image"
  ↓
Claude reads cli-anything/SKILL.md (router: trigger word + index)
  ↓ trigger word match → hit sub-skills/ocr
Claude uses the Read tool to read cli-anything/sub-skills/ocr/SKILL.md (detailed instructions)
  ↓
Claude calls Umi-OCR according to the instructions
```
---
## Frontmatter Schema
### Router (cli-anything/SKILL.md)
```yaml
---
name: cli-anything
description: |
  CLI tool unified entry router. This skill is triggered when the user needs to perform any of the following actions:
  OCR text recognition, image to text conversion, screenshot text recognition; DWG/DXF conversion, CAD text extraction and translation, layer management;
  video/audio transcoding, FFmpeg encoding; PDF translation (with layout preservation);
  internet search, web scraping; image/audio/video multimodal content analysis.
  Upon a match, the Read tool is used to retrieve the detailed commands from sub-skills/<name>/SKILL.md.
type: meta
---
```
**Do not list old names** (umi-ocr / dxf-dwg-converter / mimo-multimodal), force users to use new trigger words.
### Sub-skills (add 1 field to original frontmatter)
**General template**:
```yaml
---
name: <Subskill name field - depends on subskill>   # See §Migration Details
description: <Original description retained as is>
type: cli-sub                                     # New, marks this as a cli-anything sub-skill
---
```
**`name` field strategy**:
- 3 renamed sub-skills (ocr / dwg / mimo): change `name` to new short name (`umi-ocr` → `ocr` etc.)
- 3 retained sub-skills (ffmpeg / pdf2zh / web-search-fast): keep `name` as original (`cli-anything-ffmpeg` etc.)
**Do not add new fields such as trigger word, prefix, binary, etc.** Sub-skills in `sub-skills/` are not visible to Claude, trigger words are maintained by the router.
---
## Migration Details
### Migration actions for 6 sub-skills
| Original Path | New Path | Renamed | SKILL.md Changes |
|--------------|----------|--------|-----------------|
| `umi-ocr/` | `cli-anything/sub-skills/ocr/` | `umi-ocr` → `ocr` | `name` change + `type: cli-sub` |
| `dxf-dwg-converter/` | `cli-anything/sub-skills/dwg/` | `dxf-dwg-converter` → `dwg` | Same as above |
| `mimo-multimodal/` | `cli-anything/sub-skills/mimo/` | `mimo-multimodal` → `mimo` | Same as above |
| `cli-anything-ffmpeg/` | `cli-anything/sub-skills/ffmpeg/` | (Keep `cli-anything-ffmpeg` as original name) | Only add `type: cli-sub` |
| `cli-anything-pdf2zh/` | `cli-anything/sub-skills/pdf2zh/` | Same as above | Same as above |
| `cli-anything-web-search-fast/` | `cli-anything/sub-skills/web-search-fast/` | Same as above | Same as above |
### Path security validation
- `sub-skills/dwg/scripts/convert.py` — relative path `scripts/`, next to SKILL.md still has `scripts/` ✅
- `sub-skills/mimo/mimo_multimodal.py` — relative path `./mimo_multimodal.py`, still there ✅
- `sub-skills/ocr/` no `scripts/`, original SKILL.md inline script `python -c "..."` ✅
- 3 pip installed packages (ffmpeg / pdf2zh / web-search-fast) — package names unchanged, import paths unaffected by directory migration ✅
- `cli-anything-pdf2zh` uses absolute path `C:\Program Files\pdf2zh\build\pdf2zh.exe`, unaffected ✅
---
## Add New CLI Process
1. Create SKILL.md in `cli-anything/sub-skills/<name>/` (+ optional scripts/)
2. Add a line to the router index table in `cli-anything/SKILL.md` (tool name + trigger word + brief description)
Two steps, zero code.
---
## Test Plan
### 4 Core Scenarios
| # | Scene | Test Material | Expected |
|---|------|---------|------|
| 1 | OCR Text Extraction | `%USERPROFILE%\Downloads\Documents\MiniMax_TokenPlan_UsageReport.png` | router → ocr → non-empty text output |
| 2 | Multimodal Understanding | Same as above | router → mimo → MiMo returns a description |
| 3 | DWG to DXF Conversion | `%USERPROFILE%\OneDrive\Desktop\Tendo-rochling suzhou 2#.dwg` | router → dwg → generates .dxf |
| 4 | PDF Translation | `%USERPROFILE%\Downloads\Documents\smart_building_dc_power_distribution_and_backup_with_cisco_panduit_fmps.pdf` | router → pdf2zh → generates `*-zh.pdf` |
### 2 Edge Scenarios
| # | Scenario | Operation | Expected |
|---|----------|----------|----------|
| 5 | FFmpeg Video Cutting | `%USERPROFILE%\Downloads\Video\Tidying Center - Tidying.mp4` → Extract the first 3 seconds | router → ffmpeg → Output a 3-second mp4 |
| 6 | router Failure Fallback | "I have an Excel table for pivot analysis" | router miss → Claude gives a "no matching subskill" prompt |
### PASS Criteria
- ✅ 1-5: Output file **successfully generated** + router hits the correct sub-skill once
- ✅ 6: router concedes defeat proactively (does not call any sub-skills)
---
## Risks and Boundaries
| Risk | Mitigation |
|------|------|
| Sub-skill description is too broad, router fails to trigger correctly | Sub-skills in `sub-skills/` are not automatically discovered, no trigger issue exists |
| Nested SKILL.md loading path error | Each relative path has been verified (see "Path Security Validation") |
| Old names (such as umi-ocr) become invalid | Intentional action — router description does not list old names, forcing migration to new trigger words |
| Adding new CLI forgets to add index in router | Router index is a small hand-written table (6 rows), if Claude is missing, it will proactively use `LS sub-skills/` fallback to discover |
---
## Implementation Checklist
### Phase 1 — Create the Skeleton
- [ ] Create `cli-anything/` and `cli-anything/sub-skills/`
- [ ] Write `cli-anything/SKILL.md` (main router body)
### Phase 2 — Migrate 6 sub-skills
- [ ] `git mv cli-anything-ffmpeg/ cli-anything/sub-skills/ffmpeg/`
- [ ] `git mv cli-anything-pdf2zh/ cli-anything/sub-skills/pdf2zh/`
- [ ] `git mv cli-anything-web-search-fast/ cli-anything/sub-skills/web-search-fast/`
- [ ] `git mv umi-ocr/ cli-anything/sub-skills/ocr/`
- [ ] `git mv dxf-dwg-converter/ cli-anything/sub-skills/dwg/`
- [ ] `git mv mimo-multimodal/ cli-anything/sub-skills/mimo/`
### Phase 3 — Update frontmatter
- [ ] Rename 3 sub-skills: add `type: cli-sub` to `name`
- [ ] Add `type: cli-sub` to 3 cli-anything-* sub-skills
### Phase 4 — Verify script paths
- [ ] dwg/scripts/*.py relative path
- [ ] mimo/mimo_multimodal.py relative path
- [ ] paths for 3 pip packages
### Phase 5 — Run 6 test scenarios
### Phase 6 — Documentation and Submission
- [ ] Update `README.md` (skills list + changelog)
- [ ] Update `CLAUDE.md` to mention router mechanism
- [ ] `git add <files>` + `git commit`
---
## Implementation Pre-Conditions
- [x] Clean baseline commit (`bd1992a`)
- [ ] Archive design document (this file)
- [ ] Final user review
---
## Confirmed Decisions
| Decision | Choice |
|------|------|
| Merge Scope | All 6 CLI skills |
| Router Form | Router type (meta-skill) |
| Sub-Skill Discovery | Secondary loading (router → Read sub-skill) |
| Directory Layout | Nested (`cli-anything/sub-skills/<name>/`) |
| Implementation Complexity | Pure documentation (no scripts/, no REGISTRY.json) |
| Handling Old Names | Force new trigger words (router description does not list old names) |
| Sub-Skill Frontmatter | Add only `type: cli-sub` field |
| Test Materials | MiniMax_TokenPlan_UsageReport.png / Tendo-rochling 2#.dwg / cisco panduit fmps.pdf / Clean Center Clean.mp4 |