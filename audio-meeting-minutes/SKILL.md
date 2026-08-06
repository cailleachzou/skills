---
name: audio-meeting-minutes
description: 录音转会议纪要工作流 — FFmpeg压缩音频→ASR语音识别→AI汇总会议纪要。当用户提到录音转文字、会议纪要、音频处理、录音转写、meeting minutes时自动触发。
---

# 录音转会议纪要工作流

将现场录音通过 FFmpeg 压缩、ASR 语音识别、AI 汇总，生成结构化会议纪要。

## 触发场景

- 用户提供了录音文件，需要转文字或生成会议纪要
- "帮我把录音转文字"
- "会议纪要汇总"
- "录音处理"
- "音频压缩然后转写"

## 工作流程

### Phase 1: 音频预处理

1. 扫描用户指定的音频文件（mp3, wav, m4a, aac, ogg）
2. 检查文件大小，必要时用 FFmpeg 压缩到 ASR 可处理的大小（<10MB）
3. 压缩参数：

```bash
# 压缩到 <10MB，保持语音清晰度
ffmpeg -i input.mp3 -ar 16000 -ac 1 -b:a 64k -y output_compressed.mp3

# 或仅在文件过大时压缩
# 小于 10MB 的文件直接使用原文件
```

**压缩策略**：
- 原文件 < 10MB → 直接使用
- 原文件 10-50MB → 降采样到 16kHz + 单声道 + 64kbps
- 原文件 > 50MB → 分段处理（每段 < 10MB）

### Phase 2: ASR 语音识别

使用 MiMo 2.5 ASR 或其他可用的语音识别工具：

```bash
# MiMo ASR（如果可用）
python mimo_asr.py output_compressed.mp3

# 或使用其他 ASR 工具
```

**输出**：带时间戳的逐句转写文本

### Phase 3: AI 汇总会议纪要

基于转写文本，AI 生成结构化会议纪要：

**输出格式**：

```markdown
# 会议纪要

**日期**: YYYY-MM-DD
**项目**: {Project Name}
**参会人**: {从录音中识别}

## 主要议题
1. {议题1}
2. {议题2}

## 讨论要点

### {议题1}
- {要点}
- {决定}

### {议题2}
- {要点}
- {决定}

## 行动项
- [ ] {Action Item 1} — 负责人: {Name}, 截止: {Date}
- [ ] {Action Item 2} — 负责人: {Name}, 截止: {Date}

## 待解决问题
- {Issue 1}
- {Issue 2}
```

### Phase 4: 输出与归档

1. 保存会议纪要到项目文件夹：
   ```
   {Project Dir}/Tendo - 03_资料 Technical Archive/会议纪要/
   ```
2. 文件名格式：`{YYYY-MM-DD} - {会议主题}.md`
3. 可选：通过 `md2pdf` 转换为 PDF

## 依赖工具

| 工具 | 用途 |
|------|------|
| FFmpeg (cli-anything-ffmpeg) | 音频压缩/分段 |
| MiMo ASR / 其他 ASR | 语音识别 |
| AI summarization | 会议纪要汇总 |
| md2pdf (tendo-brand) | 可选 PDF 输出 |

## 多文件批量处理

当用户提供多个录音文件时：

1. 按文件名排序（假设文件名含序号或时间）
2. 依次处理每个文件
3. 合并为一份综合会议纪要（如果属于同一会议）
4. 或分别生成独立纪要（如果属于不同会议）

## 示例对话

```
用户: /audio-meeting-minutes C:\path\to\标准录音 18.mp3
DUDU: 文件大小 25MB，需要压缩...
      压缩完成 (8.2MB)，开始 ASR 转写...
      转写完成，287 句。正在汇总会议纪要...
      
      会议纪要已生成: 2026-07-20 - Cooley项目进度会议.md
      需要转为 PDF 吗？

用户: 还有 标准录音 19.mp3 和 20.mp3
DUDU: 批量处理 3 个文件...
      录音 18: 项目进度讨论
      录音 19: 技术方案确认  
      录音 20: 材料清单核对
      合并生成综合会议纪要。
```
