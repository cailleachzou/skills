---
name: cli-anything
description: |
  CLI 工具统一入口路由器。当用户需要以下任一操作时触发本技能：
  OCR 文字识别、图片转文字、截图识字；DWG/DXF 转换、CAD 文字提取与翻译、图层管理；
  DXF 视觉复查、渲染预览、多模态对比、自动验证；
  视频/音频转码、FFmpeg 编码；PDF 翻译（含 layout 保留）；
  摄像机覆盖范围 CAD 平面图生成（画覆盖图、cctv coverage、摄像机平面图）。
  命中后用 Read 工具读取 sub-skills/<name>/SKILL.md 获取详细命令。
type: meta
---

# cli-anything — CLI 工具统一入口

所有 CLI 工具的**路由器**。本技能不直接执行命令，只负责定位子技能、读取其详细说明书、按说明书执行。

## 工作流

```
1. 用户提出 CLI 相关需求
2. 在下方索引表匹配触发词，定位子技能
3. 用 Read 工具读 sub-skills/<name>/SKILL.md（详细说明书）
4. 按说明书执行命令
```

## 子技能索引（手动维护）

| 子技能 | 一句话 | 触发词 | 脚本 | 命令示例 | 依赖 |
|--------|--------|--------|------|----------|------|
| `ocr` | 离线 OCR 文字提取（Umi-OCR HTTP API） | OCR / 文字识别 / 图片转文字 / 截图识字 | ocr/sub-skills/ocr.py | `python scripts/ocr.py input.png` | Umi-OCR |
| `dwg` | CAD 格式转换、文字提取与翻译、SVG 导出、批量处理 | DWG / DXF / CAD / 图层 / 文字提取与翻译 | dwg/sub-skills/dwg.py | `python scripts/dwg.py --input drawing.dwg --convert dxf` | ezdxf |
| `dxf-review` | DXF 视觉复查：渲染预览、多模态对比、自动验证 | 视觉复查 / 预览 / DXF检查 / 对比原图 / 渲染看下 | dxf-review/sub-skills/dxf_visual_review.py | `python scripts/dxf_visual_review.py full input.dxf --reference original.png` | ezdxf, matplotlib, mimo |
| `ffmpeg` | 音视频转码、批量处理、预设管理、会话管理 | FFmpeg / 转码 / 视频 / 音频 / 视频剪辑 | ffmpeg/sub-skills/ffmpeg.py | `python scripts/ffmpeg.py --input video.mp4 --preset h264` | ffmpeg |
| `pdf2zh` | PDF 翻译（保留 layout，23+ 引擎，含 MiMo 补丁） | PDF 翻译 / pdf2zh / PDFMathTranslate | pdf2zh/sub-skills/pdf2zh.py | `python scripts/pdf2zh.py --input doc.pdf --target zh` | pdf2zh |
| `cctv-cad` | 摄像机覆盖范围 CAD 平面图生成 | 画覆盖图、CAD摄像机覆盖、cctv coverage、摄像机平面图、点位覆盖、生成覆盖范围图 | cctv-cad/sub-skills/draw_coverage.py | `python scripts/draw_coverage.py --focal 4 --pixels 4mp --sensor 1/2.8 --height 3.0 --direction 0 --output output.dxf` | ezdxf |

## 触发词匹配失败时

1. 先用 `LS cli-anything/sub-skills/` 列出所有子技能名
2. 看哪个目录名最像用户描述（如 "dwg" 比对"cad 转换"）
3. 仍无法定位 → 主动告知用户"无匹配子技能"，**不要强行匹配**

## 添加新 CLI 流程

1. 在 `cli-anything/sub-skills/<name>/` 下建 SKILL.md（+ 可选 scripts/）
2. 在本文件索引表加一行（工具名 + 触发词 + 一句话描述）

零代码。

## 与子技能的关系

- 子技能在 `sub-skills/` 内，**不会被 Claude 自动发现**（嵌套 SKILL.md 不在 skill 扫描根）
- 所有 CLI 工具调用都从本路由器入口走
- 子技能的 `description` 仅在本路由器引导 Read 后才有意义
