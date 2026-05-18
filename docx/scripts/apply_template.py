"""
Apply the TendoCN Letterhead template styles to a pandoc-generated .docx.

Usage:
    python apply_template.py <input.docx> <output.docx>

What it does:
  1. Unpacks the docx
  2. Reads numbering.xml to find pandoc-generated numIds:
       - numId whose abstractNum has numFmt="bullet"  → map to template numId=1
       - numId whose abstractNum has numFmt="decimal" → map to template numId=2
  3. In document.xml, replaces those pandoc numIds with the template numIds
     (so list items use the template's bullet/decimal styles)
  4. Repacks and validates
"""
import sys, os, re, shutil
# Set up path so that 'from helpers.merge_runs' resolves inside office/
# and 'from office.unpack' resolves from scripts/
_scripts = os.path.dirname(os.path.abspath(__file__))
# _scripts = .../scripts
# _skills = .../skills/docx
_skills = os.path.dirname(_scripts)
sys.path.insert(0, os.path.join(_scripts, 'office'))  # for 'from helpers.merge_runs'
sys.path.insert(0, _skills)                          # for 'from office.unpack'
sys.path.insert(0, _scripts)                        # for 'from office.pack'
from office.unpack import unpack
from office.pack import pack

TEMPLATE_NUMBERS = {"1": "bullet", "2": "decimal"}  # template numId → format name

def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else input("Input .docx: ").strip().strip('"')
    output_path = sys.argv[2] if len(sys.argv) > 2 else input("Output .docx: ").strip().strip('"')

    work_dir = os.path.join(os.environ.get('TEMP', '/tmp'), 'apply_template_work')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    print(f"Unpacking {input_path}...")
    unpack(input_file=input_path, output_directory=work_dir)

    # --- Step 1: parse numbering.xml, build pandoc numId → template numId map ---
    numbering_path = os.path.join(work_dir, 'word', 'numbering.xml')
    with open(numbering_path, encoding='utf-8') as f:
        content = f.read()

    # Find all abstractNum definitions with their id and numFmt
    abstract_map = {}  # abstractNumId → format
    for m in re.finditer(r'<w:abstractNum[^>]+w:abstractNumId="(\d+)"', content):
        aid = m.group(1)
        # Find first numFmt inside this abstractNum block
        start = m.end()
        block_end = content.find('</w:abstractNum>', start)
        block = content[start:block_end]
        fmt_m = re.search(r'<w:numFmt[^>]+w:val="([^"]+)"', block)
        if fmt_m:
            abstract_map[aid] = fmt_m.group(1)

    # Find all num definitions and their abstractNumId
    pandoc_nums = {}  # numId → abstractNumId
    for m in re.finditer(r'<w:num[^>]+w:numId="(\d+)"', content):
        nid = m.group(1)
        # Find abstractNumId inside
        start = m.end()
        block_end = content.find('</w:num>', start)
        if block_end == -1:
            block_end = content.find('/>', start)
        block = content[start:block_end]
        am_m = re.search(r'<w:abstractNumId[^>]+w:val="([^"]+)"', block)
        if am_m:
            pandoc_nums[nid] = am_m.group(1)

    # Template numIds (1 and 2) should already exist in numbering.xml.
    # Remap ALL pandoc numIds of each format to the corresponding template numId:
    #   bullet   → template numId=1
    #   decimal  → template numId=2
    # This handles multiple independent bullet/decimal lists in the same document.
    replacement_map = {}  # pandoc_numId → template_numId

    for pnum, aid in pandoc_nums.items():
        if pnum in ('1', '2'):
            continue  # skip template numIds
        fmt = abstract_map.get(aid, '')
        for tnum, tfmt in TEMPLATE_NUMBERS.items():
            if fmt == tfmt:
                replacement_map[pnum] = tnum
                print(f"  Map pandoc numId={pnum} ({fmt}) → template numId={tnum}")

    if not replacement_map:
        print("  WARNING: No pandoc numIds to remap. Template may already be applied.")

    # --- Step 2: replace numIds in document.xml ---
    doc_path = os.path.join(work_dir, 'word', 'document.xml')
    with open(doc_path, encoding='utf-8') as f:
        doc = f.read()

    for pnum, tnum in sorted(replacement_map.items(), key=lambda x: -int(x[0])):
        # Replace w:numId w:val="1002" → w:numId w:val="2" etc.
        # Only within w:numId context (not other attributes)
        doc = re.sub(
            r'(<w:numId\s+w:val=")' + pnum + r'(")',
            r'\g<1>' + tnum + r'\g<2>',
            doc
        )

    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(doc)
    print(f"  Replaced {len(replacement_map)} numId reference(s) in document.xml")

    # --- Step 3: repack ---
    print(f"Packing to {output_path}...")
    pack(input_directory=work_dir, output_file=output_path, original_file=input_path)
    shutil.rmtree(work_dir)
    print("Done.")

if __name__ == '__main__':
    main()
