---
name: batch-image-renamer
description: Batch rename images with company naming convention. Use this skill whenever the user wants to rename multiple images in a folder, especially when they mention batch renaming, renaming photos, organizing images, or applying a naming pattern like "Tendo - XXX". **Always delegate to a subagent to handle the full workflow** — spawn a general-purpose subagent with the full SKILL.md context and the target folder path. Handles folder-level batch operations, deduplication with auto-incrementing suffixes, and image content understanding. Make sure to use this skill whenever the user is trying to organize, rename, or batch-process image files — even if they don't explicitly say "skill" or use the exact command.
---

# Batch Image Renamer

批量将文件夹内的图片命名为 `Tendo - <描述>-NNN.<ext>` 格式。

## 工作流程

### Step 1: 确认文件夹路径

要求用户确认要处理的文件夹路径。如果用户已提供，直接使用。

### Step 2: 列出所有图片

使用 `Glob` 工具找到所有图片文件：

```
{pattern}/**/*.{jpg,jpeg,png,webp,gif}
```

只处理以下扩展名：`jpg`、`jpeg`、`png`、`webp`、`gif`（不区分大小写）。

### Step 3: 识别每张图片内容（并行）

对每张图片使用 `mcp__MiniMax__understand_image` 工具进行理解：

- **image_source**: 图片的绝对路径
- **prompt**: "用20字以内中文描述这张图片的主体内容，用于文件命名。直接输出描述文字，不要解释。"

根据图片内容，用中文描述图片主体（限 20 字以内，简明扼要）。

记录原始扩展名（保持原格式）。

### Step 4: 生成目标文件名

规则：
- **格式**：`Tendo - <中文描述>-NNN.<ext>`
- **序号**：按处理顺序递增 001, 002, 003...（每个文件独立占一个序号，不按描述分组）
- **描述要求**：中文，20 字以内，简洁。如「现场施工布线面板」「工人安装桥架」「安全巡查记录」

**去重规则**：只有当生成的完整文件名（描述 + 序号 + 后缀）与已生成的名字真正冲突时，才在序号后加 `-1`, `-2` 后缀。不同描述或不同序号不会冲突，不会加后缀。

### Step 5: 执行重命名

按顺序处理每个文件，直接 rename 即可（序号本身已保证唯一）。如遇意外同名冲突（同一文件被重复处理），跳过该文件并提示。

### Step 6: 汇总报告

全部完成后，输出汇总：
```
✅ 批量重命名完成
📁 文件夹：<路径>
📸 共处理：N 张图片
⏱ 用时：X 秒
```

## 示例

**输入**：文件夹内有 3 张图片

**输出**：
- `DSC_001.jpg` → `Tendo - 现场施工布线面板-001.jpg`
- `DSC_002.jpg` → `Tendo - 工人安装桥架-002.jpg`
- `DSC_003.jpg` → `Tendo - 现场施工布线面板-003.jpg`

（001 和 003 描述相同但序号不同，文件名不冲突，无需加后缀）

## 注意事项

- 如果图片内容无法确定，用通用描述如「现场照片-001」
- 保持原始文件扩展名大小写
- 如果目标文件名已存在（同名文件被重命名过），自动往后递增序号
- 不要预览，直接执行重命名（用户已确认）
- 如果文件夹内有非图片文件，自动忽略，不处理
