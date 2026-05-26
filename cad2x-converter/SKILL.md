---
name: cad2x-converter
description: |
  Use when the user wants to convert CAD files between formats. Triggers when user mentions converting DXF/DWG files, CAD conversion, exporting CAD to PDF/PNG/SVG, or converting between CAD formats. This skill handles downloading the cad2x binary and executing conversions.

  Example triggers:
  - "convert DXF to PDF"
  - "帮我把这个 DWG 转成 PNG"
  - "cad2x 转换"
  - "export this drawing to SVG"
  - batch converting multiple CAD files
---

# cad2x-converter

cad2x 是一个最小化的单文件命令行工具，用于将 CAD 文件（DXF / DWG）转换为其他格式（DXF / PDF / PNG / SVG）。

## 安装

检查是否已有 cad2x 二进制文件：

```bash
CAD2X_BIN="$HOME/.claude/skills/cad2x-converter/bin/cad2x.exe"
# Windows
ls "$CAD2X_BIN" 2>/dev/null && echo "exists" || echo "not found"
```

如果不存在，从 GitHub 下载：

```bash
CAD2X_BASE="https://github.com/orcastor/addon-previewer"
CAD2X_BIN_DIR="$HOME/.claude/skills/cad2x-converter/bin"
mkdir -p "$CAD2X_BIN_DIR"

# 下载 Windows 二进制
gh api repos/orcastor/addon-previewer/contents/back/cad2x/win_x64/cad2x.exe --jq '.content' | base64 -d > "$CAD2X_BIN_DIR/cad2x.exe"

# 下载字体包
mkdir -p "$CAD2X_BIN_DIR/fonts"
for font in $(gh api repos/orcastor/addon-previewer/contents/back/cad2x/common/fonts --jq '.[].name'); do
  gh api "repos/orcastor/addon-previewer/contents/back/cad2x/common/fonts/$font" --jq '.content' | base64 -d > "$CAD2X_BIN_DIR/fonts/$font"
done

# 下载图案包
mkdir -p "$CAD2X_BIN_DIR/patterns"
for pat in $(gh api repos/orcastor/addon-previewer/contents/back/cad2x/common/patterns --jq '.[].name'); do
  gh api "repos/orcastor/addon-previewer/contents/back/cad2x/common/patterns/$pat" --jq '.content' | base64 -d > "$CAD2X_BIN_DIR/patterns/$pat"
done
```

**注意**：首次使用需要下载，后续直接使用本地缓存。字体包必须存在，否则中文字符无法显示。

## 使用方法

```bash
cad2x [选项] <输入文件>
```

### 常用选项

| 选项 | 说明 |
|------|------|
| `-o, --outfile <file>` | 输出文件（DXF v2007 / PDF / PNG / SVG） |
| `-a, --auto-orientation` | 根据图纸边界框自动设置纸张方向 |
| `-c, --fit` | 自动适应并居中绘图到页面 |
| `-b, --monochrome` | 单色输出（黑/白） |
| `-p, --paper <WxH>` | 页面尺寸（宽×高，毫米） |
| `-m, --margins <L,T,R,B>` | 页面边距（毫米） |
| `-r, --resolution <dpi>` | 输出分辨率（DPI） |
| `-s, --scale <ratio>` | 输出比例，如 0.01（表示 1:100） |
| `-e, --code-page <codepage>` | DXF 文件编码，默认为 ANSI_1252 |
| `-f, --default-font <font>` | 默认字体，如 simsun |
| `-l, --font-dirs <dirs>` | 额外字体目录（逗号分隔） |
| `-t, --directory <path>` | 目标输出目录 |

### 代码页参考

| 语言 | DXF 代码页 |
|------|-----------|
| 中文（简体） | ANSI_936 |
| 日语 | ANSI_932 |
| 韩语 | ANSI_949 |
| 泰语 | ANSI_874 |
| 西欧 | ANSI_1252 |

### 常用示例

**单文件转换（DWG → PDF）**
```bash
cad2x -o output.pdf input.dwg
```

**批量转换（所有 DWG → PDF，自动方向+居中）**
```bash
cad2x -o pdf *.dwg -t output -ac
```

**导出为 PNG（A3 纸，300 DPI）**
```bash
cad2x -o output.png input.dxf -p 297x210 -r 300
```

**DWG → DXF v2007（版本升级）**
```bash
cad2x -o output.dxf input.dwg
```

**中文图纸（指定编码+字体）**
```bash
cad2x -o output.pdf input.dxf -e ANSI_936 -f simsun -ac
```

**指定比例尺（1:100）**
```bash
cad2x -o output.pdf input.dxf -s 0.01 -ac
```

**多页打印（2×3）**
```bash
cad2x -o output.pdf input.dxf -n 2x3
```

## 工作流程

1. **确定输入文件** — 用户提供的 DXF/DWG 文件路径
2. **确定输出格式** — PDF/PNG/SVG/DXF
3. **确定选项** — 根据需求添加：
   - 中文图纸 → `-e ANSI_936 -f simsun`
   - 批量转换 → `-t output_dir`
   - 打印样式 → `-ac`（自动方向+居中）
4. **执行转换** — 使用绝对路径执行
5. **告知结果** — 输出文件路径

## 注意事项

- 字体包和图案包必须存在，否则中文字符无法显示或图案丢失
- 批量转换时，输出文件名与输入相同（仅扩展名变化）
- Windows 上用 `.exe`，Linux/macOS 上用无扩展名的二进制文件