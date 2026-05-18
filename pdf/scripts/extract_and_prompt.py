"""
Extract text from PDF and generate a structured review prompt for AI vision analysis.
Usage: python extract_and_prompt.py <input.pdf> <output_dir>

Outputs:
  <output_dir>/extracted_text.txt  - Raw extracted text from PDF
  <output_dir>/review_prompt.md     - Structured prompt ready for mcp__MiniMax__understand_image
"""
import sys
import os

PYTHON = "/c/Users/59620/AppData/Local/Python/bin/python.exe"


def extract_text(pdf_path):
    """Extract text from PDF using pdfplumber (best for text-heavy docs)."""
    try:
        import pdfplumber
    except ImportError:
        print("Error: pdfplumber not installed. Run: pip install pdfplumber")
        return None

    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                all_text.append(f"=== Page {i+1} ===\n{text}")

    return "\n\n".join(all_text) if all_text else ""


def extract_tables(pdf_path):
    """Extract tables as text for reference, skipping empty/meaningless ones."""
    try:
        import pdfplumber
    except ImportError:
        return ""

    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                if table:
                    # Filter out rows that are all empty
                    non_empty_rows = [row for row in table if any(cell for cell in row if cell)]
                    if non_empty_rows:
                        table_text = "\n".join(
                            [" | ".join([str(c).strip() if c else "" for c in row]) for row in non_empty_rows]
                        )
                        all_tables.append(f"=== Page {i+1} - Table {j+1} ===\n{table_text}")

    return "\n\n".join(all_tables) if all_tables else ""


PROMPT_TEMPLATE = """## 已知信息（来自文字提取）

以下信息提取自该图纸/文档，请结合图片进行核查：

### 提取文字
{extracted_text}

### 提取表格（如有）
{tables_text}

---

## 核查任务

请基于以上已知信息，对照图纸/图片进行核查：

1. **标注位置** — 图中标注位置是否与文字描述一致？
2. **文字一致性** — 文字提取内容与图片中可见标注是否匹配？
3. **完整性** — 是否有遗漏的房间名称、系统标注、标高、尺寸？
4. **新增发现** — 图片中可见但文字提取未包含的重要信息？
5. **准确性** — 系统类型标注是否正确（如弱电、消防、BA 等）？

## 输出格式

请按以下格式输出核查结果：

**核查结论：** 一致 / 存在差异 / 部分一致

**具体问题：**
1. [问题描述]
2. [问题描述]

**新增发现：**
- [补充信息]

**建议：**
- [如有问题，提出修改建议]
"""


def generate_review_prompt(extracted_text, tables_text, pdf_name):
    prompt = PROMPT_TEMPLATE.format(
        extracted_text=extracted_text if extracted_text else "(未提取到文字内容，请完全依赖视觉分析)",
        tables_text=tables_text if tables_text else "(无表格)"
    )
    return f"# AI 视觉复核 Prompt\n# 来源文件：{pdf_name}\n\n{prompt}"


def main(pdf_path, output_dir):
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found: {pdf_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print(f"Extracting text from: {pdf_path}")
    extracted_text = extract_text(pdf_path)
    tables_text = extract_tables(pdf_path)

    # Save extracted text
    text_file = os.path.join(output_dir, "extracted_text.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(extracted_text if extracted_text else "(No text extracted - PDF may be image-based)")
    print(f"Saved: {text_file}")

    # Save review prompt
    prompt_file = os.path.join(output_dir, "review_prompt.md")
    prompt_content = generate_review_prompt(extracted_text, tables_text, os.path.basename(pdf_path))
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt_content)
    print(f"Saved: {prompt_file}")

    print(f"\nDone. Files written to: {output_dir}")
    print(f"\nNext step: Use mcp__MiniMax__understand_image with review_prompt.md content as prompt.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
