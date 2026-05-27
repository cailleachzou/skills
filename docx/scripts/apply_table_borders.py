"""
Apply explicit table borders AND auto-fit width to all tables in a pandoc-generated .docx.

Usage:
    python apply_table_borders.py <input.docx> <output.docx>

What it does:
  1. Unpacks the docx
  2. For every <w:tbl>:
       - Sets <w:tblW w:w="0" w:type="auto"/> (auto-fit table width)
       - Injects <w:tblBorders> with all insideH/insideV borders
  3. For every <w:tc>:
       - Sets <w:tcW w:w="0" w:type="auto"/> (auto-fit cell width)
       - Injects <w:tcBorders> with all four sides
  4. Repacks

Why (borders): Pandoc's Table style only defines borders for firstRow/lastRow.
     All other data cells have no borders. This fills those gaps.
Why (auto-fit): Pandoc fixes column widths in DXA units. Setting type="auto"
     on both the table and cell level makes Word auto-calculate widths from
     content, matching Word's "AutoFit > AutoFit Contents" behavior.
"""
import sys, os, shutil, re

_scripts = os.path.dirname(os.path.abspath(__file__))
_skills = os.path.dirname(_scripts)
sys.path.insert(0, os.path.join(_scripts, 'office'))
sys.path.insert(0, _scripts)
from office.unpack import unpack
from office.pack import pack


def _build_border_xml():
    """Return border XML strings for tbl-level and cell-level borders."""
    color = "009DFF"
    sz = "4"
    return (
        # Table-level borders (insideH + insideV)
        '<w:tblBorders>'
        f'<w:top w:val="single" w:sz="{sz}" w:color="{color}"/>'
        f'<w:left w:val="single" w:sz="{sz}" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="{sz}" w:color="{color}"/>'
        f'<w:right w:val="single" w:sz="{sz}" w:color="{color}"/>'
        f'<w:insideH w:val="single" w:sz="{sz}" w:color="{color}"/>'
        f'<w:insideV w:val="single" w:sz="{sz}" w:color="{color}"/>'
        '</w:tblBorders>',
        # Cell-level borders (all four sides)
        '<w:tcBorders>'
        f'<w:top w:val="single" w:sz="{sz}" w:color="{color}"/>'
        f'<w:left w:val="single" w:sz="{sz}" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="{sz}" w:color="{color}"/>'
        f'<w:right w:val="single" w:sz="{sz}" w:color="{color}"/>'
        '</w:tcBorders>',
    )


def apply_borders(content):
    """
    Scan document.xml text for table elements and inject missing border XML.
    Also sets table and cell widths to auto (w:type="auto") so Word auto-fits
    columns based on content — matching Word's "AutoFit" behavior.
    Returns modified content string.
    """
    tbl_borders, tc_borders = _build_border_xml()

    # --- Step 0: auto-fit table width ---
    # Replace <w:tblW w:w="..." w:type="auto|NIL"/> with <w:tblW w:w="0" w:type="auto"/>
    # (type="auto" = Word auto-calculates width; w:w="0" preferred = no fixed size)
    content = re.sub(
        r'<w:tblW\b[^/]*/>',
        '<w:tblW w:w="0" w:type="auto"/>',
        content,
    )

    # --- Step A: ensure <w:tblBorders> inside every <w:tblPr> ---
    def add_tbl_borders(m):
        tblpr = m.group(0)
        if '<w:tblBorders>' in tblpr:
            return tblpr
        return tblpr.replace('</w:tblPr>', tbl_borders + '</w:tblPr>')

    content = _re_sub_ranged(
        r'<w:tblPr>(?:(?!</w:tblPr>)[\s\S])*</w:tblPr>',
        add_tbl_borders,
        content,
    )

    # --- Step B: ensure <w:tcBorders> for every cell ---
    # Handle TWO forms: <w:tcPr/> (self-closing empty) and <w:tcPr>...</w:tcPr>
    def add_tc_borders(m):
        tcpr = m.group(0)
        if '<w:tcBorders>' in tcpr:
            return tcpr
        if tcpr.endswith('/>'):
            # Self-closing: <w:tcPr/> → <w:tcPr><w:tcBorders>...</w:tcBorders></w:tcPr>
            return tcpr[:-2] + '>' + tc_borders + '</w:tcPr>'
        else:
            return tcpr.replace('</w:tcPr>', tc_borders + '</w:tcPr>')

    # Self-closing tcPr
    content = re.sub(r'<w:tcPr/>', add_tc_borders, content)

    # tcPr with content
    content = _re_sub_ranged(
        r'<w:tcPr>(?:(?!</w:tcPr>)[\s\S])*</w:tcPr>',
        add_tc_borders,
        content,
    )

    # --- Step C: auto-fit cell widths ---
    # Replace <w:tcW w:w="..." w:type="dxa|pct|auto"/> with <w:tcW w:w="0" w:type="auto"/>
    content = re.sub(
        r'<w:tcW\b[^/]*/>',
        '<w:tcW w:w="0" w:type="auto"/>',
        content,
    )

    return content


def _re_sub_ranged(pattern, replacer, content, flags=0):
    """
    Non-greedy re.sub that works on patterns containing newlines
    without DOTALL. Handles the fact that our table XML spans multiple lines.
    """
    compiled = re.compile(pattern, flags)
    result = []
    last_end = 0
    for m in compiled.finditer(content):
        result.append(content[last_end:m.start()])
        result.append(replacer(m))
        last_end = m.end()
    result.append(content[last_end:])
    return ''.join(result)


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else input("Input .docx: ").strip().strip('"')
    output_path = sys.argv[2] if len(sys.argv) > 2 else input("Output .docx: ").strip().strip('"')

    work_dir = os.path.join(os.environ.get('TEMP', '/tmp'), 'apply_table_borders_work')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    print(f"Unpacking {input_path}...")
    unpack(input_file=input_path, output_directory=work_dir)

    doc_path = os.path.join(work_dir, 'word', 'document.xml')
    with open(doc_path, encoding='utf-8') as f:
        content = f.read()

    original = content
    content = apply_borders(content)

    if content == original:
        print("  No changes needed — borders already present.")
    else:
        # Count changes
        tbl_count = content.count('<w:tblBorders>') - original.count('<w:tblBorders>')
        tc_count = content.count('<w:tcBorders>') - original.count('<w:tcBorders>')
        print(f"  Added {tbl_count} <w:tblBorders> block(s)")
        print(f"  Added {tc_count} <w:tcBorders> block(s)")

    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Packing to {output_path}...")
    pack(input_directory=work_dir, output_file=output_path, original_file=None)
    shutil.rmtree(work_dir)
    print("Done.")


if __name__ == '__main__':
    main()