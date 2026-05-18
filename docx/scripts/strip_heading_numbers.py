"""
Strip heading numbers from Markdown content before converting to docx.

Word will auto-generate heading numbers from the heading styles.
Having manual numbers like "1.1", "1.2.3" in the MD text causes double-numbering.

Usage:
    python strip_heading_numbers.py <input.md> <output.md>

Patterns stripped:
    - ^1.1 ...  (h1/h2 level: digit.digit at line start)
    - ^1.2.3 ... (any depth: digit.digit.digit etc.)
    - ^1.2.3.4 ... and so on
    - Also strips trailing space after the number

The regex covers:
    ^(\d+\.)+\d+\s*   → multi-level like 1.1, 1.2.3, 2.1.4.5
    ^\d+\.\s*         → single level like 1.  2.  (only when followed by heading)
"""
import re
import sys

def strip_heading_numbers(md_content):
    """
    Remove manual heading numbers from markdown lines that start with headings.
    E.g. "## 1.1 设计范围" → "## 设计范围"
    """
    lines = md_content.split('\n')
    result = []

    for line in lines:
        # Match heading lines: starts with # then space then number pattern
        # Pattern: optional ###..., space, then (digit.digit... digit(s)) then space
        # Examples: "## 1.1 Design Scope", "### 1.2.3.4 Sub Section"
        # We only strip the number pattern, not if the number appears after text

        # Two patterns:
        # 1. Single-level: digit(s) + dot + space(s) at line start (e.g. "3. 设备清单" → "设备清单")
        #    Must be followed by space to distinguish from cases like "条款3.适用于..."
        # 2. Multi-level: digit.digit... (e.g. "1.1", "1.2.3") at line start
        #    Used for sub-numbering like "## 1.2.3 Section"
        single_level_pattern = r'^((?:#{1,6})\s+)(\d+)\.(\s+)(.*)$'
        multi_level_pattern  = r'^((?:#{1,6})\s+)(\d+(?:\.\d+)+)(\s+)(.*)$'

        match = re.match(single_level_pattern, line)
        if match:
            # Single level like "## 3. 标题"
            prefix = match.group(1)    # "## "
            heading_text = match.group(4)  # actual heading text
            result.append(prefix + heading_text)
        else:
            match = re.match(multi_level_pattern, line)
            if match:
                # Multi level like "## 1.1.3 标题"
                prefix = match.group(1)    # "## "
                heading_text = match.group(4)  # actual heading text
                result.append(prefix + heading_text)
            else:
                result.append(line)

    return '\n'.join(result)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python strip_heading_numbers.py <input.md> <output.md>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    stripped = strip_heading_numbers(content)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(stripped)

    # Count how many lines were changed
    original_lines = content.split('\n')
    new_lines = stripped.split('\n')
    changed = sum(1 for o, n in zip(original_lines, new_lines) if o != n)
    print(f"Stripped heading numbers from {changed} line(s)")
    print(f"Output written to: {output_path}")