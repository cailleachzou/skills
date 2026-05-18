---
name: tendo-brand
description: Official Tendo Technology brand theme for presentations and artifacts. Use whenever the user mentions Tendo, applies Tendo styling, or creates company profile / sales / technical proposal documents for Tendo Technology. Based on the 2025 company profile visual identity.
---

# Tendo Brand Theme

Official Tendo Technology brand theme, extracted from the 2025 Company Profile PDF. Defines precise color palette, typography hierarchy, and visual patterns used across all Tendo collateral.

## Color Palette

### Primary Brand Colors
| Name | Hex | Usage |
|------|-----|-------|
| **Tendo Blue** | `#00AEEF` | Logo "TECHNOLOGY" wordmark, icon bars, primary accent |
| **Tendo Black** | `#000000` | Logo "TENDO" wordmark, maximum contrast elements |
| **Corporate Navy** | `#1A608F` | Section headers (OUR VISION, COMPANY BACKGROUND), primary titles |
| **Deep Navy** | `#215A81` | Body text, bullet points, secondary headers |

### Secondary Colors
| Name | Hex | Usage |
|------|-----|-------|
| **Accent Cyan** | `#98F2F4` | Photo borders, glow effects, circular masks |
| **Bright Blue** | `#009AF9` | Timeline boxes, process elements, CTAs |
| **Light Background Blue** | `#E0EAF4` | Decorative wave patterns, subtle backgrounds |
| **Neutral Gray** | `#A6A6A6` | Decorative arcs, sub-bullets, background elements |
| **Text Gray** | `#333333` | Body paragraphs on light backgrounds |
| **White** | `#FFFFFF` | Primary background, text on dark elements |
| **Light Gray** | `#F5F7FA` | Subtle section backgrounds |

### Color Application Rules
- **Tendo Blue** (`#00AEEF`): Logo, key icons, CTAs, accent lines, timeline elements
- **Corporate Navy** (`#1A608F`): Section headers, title text, primary dividers
- **Deep Navy** (`#215A81`): Body text, bullet points, descriptive paragraphs
- **Accent Cyan** (`#98F2F4`): Photo/circular image borders, glow treatments
- **Neutral Gray** (`#A6A6A6`): Decorative arcs, background elements only
- Maximum 3-4 colors from palette in any single composition

## Typography

### Font Stack
- **Headers (H1, Display)**: Montserrat Bold — bold, all-caps, slightly condensed for impact
- **Subheaders (H2, H3)**: Montserrat SemiBold — title case, medium weight
- **Body Text**: Montserrat Regular — clean, high legibility
- **Accent/Labels**: Montserrat Medium — navigation, tags, metadata

### Type Scale
| Element | Weight | Case | Style |
|---------|--------|------|-------|
| Logo Wordmark | Bold/Black | All-Caps | Wide, geometric, slightly rounded corners |
| Page Title | Bold | All-Caps | Extra bold, condensed (Bebas Neue feel) |
| Section Header | Bold | Title Case | Large, clean sans-serif |
| Subheader | SemiBold | Title Case | Medium size |
| Body | Regular | Sentence | Standard weight, high line-height |
| Bullet Text | SemiBold | Title Case | List items |
| Caption/Meta | Medium | Sentence | Small, subtle |

### Why Montserrat
Geometric sans-serif with OpenType support for multilingual content. Futuristic yet professional — aligns with Tendo's tech/ELV positioning. Wide letter-spacing on headers creates clean, premium corporate aesthetic.

## Visual Style

### Core Characteristics
- **High contrast**: Blue on white / White on navy / Blue on black
- **Geometric**: Rectangles, circles, horizontal bars — no organic shapes
- **Futuristic tech**: Circuit board patterns, wave/signal line backgrounds, circular image masks with cyan borders
- **Minimalist**: Generous whitespace, limited palette, clean compositions
- **No gradients** in primary brand elements — solid color blocks only

### Design Patterns
1. **Circular image masks**: Photos inside circles with thin `#98F2F4` cyan borders
2. **Decorative arcs**: Large gray (`#A6A6A6`) partial circles in bottom corners — frame-breaking depth elements
3. **Wave patterns**: Light blue (`#E0EAF4`) flowing diagonal lines suggesting connectivity/data flow
4. **Horizontal dividers**: Thin navy lines ending with small circular "nodes"
5. **Timeline blocks**: Left-aligned vertical stack of bright blue rectangles for history/milestones

### Logo Reference
- Icon: Square shape with 5-6 horizontal bars of varying lengths (data stream / modular architecture motif)
- Wordmark: Heavy geometric sans-serif "TENDO" in black
- Descriptor: "TECHNOLOGY" in `#00AEEF` bright blue, aligned to match TENDO width
- Tagline: Italicized sans-serif, medium weight, all-caps ("TECHNOLOGY THAT MOVES YOU FORWARD")

### Background Treatments
- White (`#FFFFFF`) primary background with generous whitespace
- Subtle circuit board / motherboard graphic with gradient fade (opacity 20-40%) for hero sections
- Corner accent gradients (dark blue, subtle) to frame page content
- Light gray wave patterns in corners suggesting connectivity

## Component Guidelines

### Headers
```
Background: White
Text: Corporate Navy (#1A608F) or Tendo Blue (#00AEEF)
Decoration: Thin underline + thicker accent bar (right-aligned)
```

### Bullet Lists
- Primary bullets: Solid navy circles (`#215A81`)
- Sub-bullets: Small dots in neutral gray (`#A6A6A6`)
- Text: Deep Navy (#215A81) or Corporate Navy (#1A608F) based on hierarchy

### Photo/Cards
- Border: 2px solid `#98F2F4` (Accent Cyan)
- Shape: Circular mask or rounded rectangle
- Shadow: None (clean flat design)

### Timeline
- Box fill: `#009AF9` (Bright Blue)
- Box text: White (`#FFFFFF`)
- Connector: Small navy squares between blocks

### Process Diagrams
- 5-column horizontal layout with circular image + header + centered paragraph per column
- Wave-shaped navy divider separating visual and text sections

## Application Notes

**Use Tendo Blue** (`#00AEEF`) for:
- Logo wordmark and icon
- Key accent lines and CTAs
- Timeline and process elements

**Use Corporate Navy** (`#1A608F`) for:
- Section headers and page titles
- Primary dividers

**Use Deep Navy** (`#215A81`) for:
- Body text and bullet points
- Descriptive paragraphs

**Use Accent Cyan** (`#98F2F4`) for:
- Photo borders and circular masks
- Glow effects on dark backgrounds

## Tendo Table Style

A professional 3-column table component styled for Tendo Technology proposals and technical documents. Based on Word's `ListTable3-Accent4` structure, adapted with Tendo Blue.

### Visual Specs
| Element | Value |
|---------|-------|
| Border color | `#00AEEF` (Tendo Blue) |
| Header fill | `#00AEEF` (Tendo Blue) |
| Header text | White, Bold, 10pt Montserrat |
| Body text | Deep Navy `#215A81`, 10pt |
| Body fill | White `#FFFFFF` |
| Last-row top border | Double-line `#00AEEF` |
| First/last column | Inner borders removed |
| Row banding | Via horizontal borders only (no fill) |

### docx-js Usage

```javascript
const { BorderStyle, ShadingType, WidthType, Table, TableRow, TableCell,
        Paragraph, TextRun, AlignmentType } = require('docx');
const TENDO_BLUE = "00AEEF";
const TENDO_NAVY = "215A81";
const WHITE = "FFFFFF";

// Helper: single border
const border = (color) => ({ style: BorderStyle.SINGLE, size: 4, color });
// Helper: no border
const noBorder = () => ({ style: BorderStyle.NIL, size: 0, color: "auto" });
// Helper: double top border (for last row)
const doubleTopBorder = (color) => ({ style: BorderStyle.DOUBLE, size: 4, color });

// Build a header row
function headerRow(cells) {
  return new TableRow({
    tableHeader: true,
    children: cells.map(text => new TableCell({
      borders: {
        top: border(TENDO_BLUE), bottom: border(TENDO_BLUE),
        left: border(TENDO_BLUE), right: border(TENDO_BLUE),
      },
      shading: { fill: TENDO_BLUE, type: ShadingType.CLEAR },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({
        children: [new TextRun({ text, bold: true, color: WHITE, font: "Montserrat" })],
      })],
    }))
  });
}

// Build a body row (isLast = true adds double top border)
function bodyRow(cells, isLast = false) {
  return new TableRow({
    children: cells.map((text, i) => new TableCell({
      borders: {
        top:    isLast ? doubleTopBorder(TENDO_BLUE) : border(TENDO_BLUE),
        bottom: border(TENDO_BLUE),
        left:   i === 0 ? border(TENDO_BLUE) : (i === cells.length - 1 ? border(TENDO_BLUE) : border(TENDO_BLUE)),
        right:  i === cells.length - 1 ? border(TENDO_BLUE) : border(TENDO_BLUE),
      },
      shading: { fill: WHITE, type: ShadingType.CLEAR },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({
        children: [new TextRun({ text, color: TENDO_NAVY, font: "Montserrat" })],
      })],
    }))
  });
}

// Example: 3-column application summary table
// Total width = 9026 DXA (A4 with 1800 margins each side)
const table = new Table({
  width: { size: 9026, type: WidthType.DXA },
  columnWidths: [2000, 4513, 2513],  // must sum to 9026
  rows: [
    headerRow(["应用领域", "主要内容", "典型案例"]),
    bodyRow(["智能家居", "家居设备的互联与自动化控制", "智能灯光、空调、门锁"]),
    bodyRow(["智慧建筑", "楼宇的能耗管理与安防监控", "智能电梯、节能系统"]),
    bodyRow(["工业制造", "生产流程的自动化与优化", "智能机器人、质量检测"]),
    bodyRow(["智慧城市", "城市基础设施的数字化管理", "智能交通、环境监测"], true),
  ],
});
```

**Width calculation (A4, 1800 DXA margins):**
- Content width = 11906 − 3600 = **9026 DXA**
- Column widths must sum to 9026
- For Letter (12240 − 3600 = 8640 DXA), adjust columnWidths accordingly

### Column Width Quick Reference

| Columns | Total Width | Suggested splits (DXA) |
|---------|-------------|----------------------|
| 2 | 9026 | 3000 + 6026, or 4513 + 4513 |
| 3 | 9026 | 2000 + 4513 + 2513 (shown above) |
| 3 | 9026 | 2500 + 3500 + 3026 |
| 4 | 9026 | 1800 + 2700 + 2526 + 2000 |

## Brand Colors in Context (from PDF pages)

| Page | Primary Use | Color(s) |
|------|-------------|----------|
| Cover | Logo, tagline | `#000000` / `#00AEEF` |
| Vision/Mission | Headers, dividers | `#1A5B7F` / `#98F2F4` |
| Company Background | Timeline, headers | `#009AF9` / `#215A81` |
| Innovative Strategy | Wave divider, process circles | `#13527D` / `#00A8E1` |
| ELV/ICT Solutions | Section headers, bullets | `#1A4B6D` / `#2571A2` / `#2D7FB4` |
| References | Dark frame border, text | `#1A4B6D` |

## Best Used For
- Company profile presentations
- IT/ELV services proposals
- Cloud infrastructure decks
- Managed services pitches
- Security solution proposals
- Tendo Technology sales collateral

## Logo Assets (in `assets/` folder)
Available for direct use when applying the theme:
- `Logo Transparent.png` — Main logo on transparent background
- `Logo Transparent (Header).png` — Header-optimized logo variant
- `Logo2Dec24 (Big).png` — Updated logo (December 2024 version)
- `White Logo.png` — For use on dark backgrounds
- `Tendo Colour Code.jpg` — Official color reference swatch
- `APAC Map (Tendo Blue).png` — Regional coverage map graphic
- `Business Card Front - AC.ai` / `Business Card Back.ai` — Business card template
- `Tendo CN - Businees Card (Amendment).pdf` — CN business card reference

## Font Loading
```html
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
```

Font: **Montserrat** (400, 500, 600, 700 weights) — loaded via Google Fonts