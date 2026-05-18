---
name: minimax-mmx
description: MiniMax 多模态 AI CLI 工具。调用 mmx CLI 进行文本对话、图片生成、视频生成、语音合成、音乐创作、网页搜索、图像理解、批量图片分析。当用户提到「MiniMax」「mmx」「生成图片」「生成视频」「文字转语音」「TTS」「合成语音」「生成音乐」「搜索信息」「图生图」「视频生成」「批量图片分析」「批量识别」「跑图」时使用此技能。不需要安装——mmx CLI 已全局安装，直接调用即可。
allowed-tools: Bash, Read, Write, Glob, Grep, Agent, AskUserQuestion
compatibility: { "requires": ["mmx CLI 已通过 npm install -g mmx-cli 安装"] }
---

# MiniMax mmx CLI Skill

调用 MiniMax mmx CLI 完成各类生成任务。mmx 已全局安装，无需额外设置。

## 调用原则

每次操作只调用一个 mmx 子命令，尽量保持简单。除非任务本身需要多步骤（如先生成视频再下载），否则不要链式调用。

## 工具选择指引

| 需求 | 命令 |
|------|------|
| 智能问答 / 对话 / 写作 | `mmx text chat` |
| 文生图 | `mmx image generate` |
| 图生视频（I2V）/ 文生视频（T2V） | `mmx video generate` |
| 文字转语音（TTS） | `mmx speech synthesize` |
| 生成歌曲 / 背景音乐 | `mmx music generate` |
| 网页搜索 | `mmx search query` |
| 图片内容理解 / 描述 | `mmx vision describe` |
| 查看配额 | `mmx quota show` |

## text chat — 文本对话

**基础用法：**
```bash
mmx text chat --message "你的问题"
```

**流式输出（默认 TTY）**：直接返回，无需额外 flag。

**非流式 / JSON 输出：**
```bash
mmx text chat --message "你的问题" --output json
```

**多轮对话**（每条 `--message` 可带角色前缀）：
```bash
mmx text chat --message "用户：你好" --message "assistant:你好，有什么可以帮你？" --message "用户：帮我写首诗"
```

**系统提示词 + 模型选择：**
```bash
mmx text chat --system "你是一个专业的建筑设计师" --model MiniMax-M2.7-highspeed --message "住宅楼的消防规范有哪些？"
```

**其他参数：**
- `--max-tokens <n>`：最大生成 token 数（默认 4096）
- `--temperature <n>`：采样温度（0.0 - 1.0）
- `--top-p <n>`：核采样阈值

**适用场景**：技术问答、内容创作、代码生成、文件转换、摘要总结。

## image generate — 图片生成

**基础用法：**
```bash
mmx image generate --prompt "画面描述"
```

**保存到指定路径：**
```bash
mmx image generate --prompt "现代简约风格办公室" --out "./output/office.png"
```

**保存到目录（自动命名）：**
```bash
mmx image generate --prompt "海边日落" --out-dir ./generated/
```

**生成多张：**
```bash
mmx image generate --prompt "科技感建筑" --n 4
```

**指定尺寸：**
```bash
mmx image generate --prompt "宽幅风景" --width 1920 --height 1080
```

**指定宽高比：**
```bash
mmx image generate --prompt "猫" --aspect-ratio 16:9
```

**优化提示词（自动改写提升质量）：**
```bash
mmx image generate --prompt "海边城堡" --prompt-optimizer
```

**主题一致性（角色参考）：**
```bash
mmx image generate --prompt "同一角色在不同场景" --subject-ref "type=character,image=character_ref.png"
```

**其他参数：**
- `--seed <n>`：随机种子，相同 seed + 相同 prompt = 相同图片
- `--response-format url|base64`：默认 url（下载），base64 可绕过 CDN

## video generate — 视频生成

### T2V（文生视频）
```bash
mmx video generate --prompt "Ocean waves at sunset, cinematic" --download ocean.mp4
```

### I2V（图生视频）
```bash
mmx video generate --prompt "人物转身" --first-frame person.jpg --download result.mp4
```

### 快速模式（需首帧）
```bash
mmx video generate --prompt "风吹过画面" --first-frame scene.jpg --download fast.mp4
# 实际使用 MiniMax-Hailuo-2.3-Fast 模型
```

### SEF（首尾帧插值）
```bash
mmx video generate --prompt "行走" --first-frame walk_start.jpg --last-frame walk_end.jpg --download interpolation.mp4
# 使用 Hailuo-02 模型
```

### S2V（主体一致性视频）
```bash
mmx video generate --prompt "侦探在街头行走" --subject-image detective.jpg --download s2v.mp4
# 使用 S2V-01 模型
```

**非阻塞模式**（立即返回 task ID，适合 CI/agent）：
```bash
mmx video generate --prompt "机器人画画" --async --quiet
```

**查询任务状态：**
```bash
mmx video task get --task-id <ID>
```

**按 file-id 下载：**
```bash
mmx video download --file-id <ID> --out video.mp4
```

## speech synthesize — 语音合成

**默认音色：Chinese (Mandarin)_Southern_Young_Man（中文男声，南方年轻音色）**

**基础用法：**
```bash
mmx speech synthesize --text "你好，欢迎使用 MiniMax" --out hello.mp3
# 默认使用 Chinese (Mandarin)_Southern_Young_Man 音色，无需单独指定
```

**指定音色（先列出可用音色）：**
```bash
mmx speech voices
mmx speech synthesize --text "新闻播报内容" --voice Chinese_news_anchor --out news.mp3
```

**调节语速：**
```bash
mmx speech synthesize --text "正常语速" --speed 1.0 --out normal.mp3
mmx speech synthesize --text "慢速朗读" --speed 0.7 --out slow.mp3
```

**包含字幕时间轴：**
```bash
mmx speech synthesize --text "对话内容" --subtitles --out dialogue.mp3
```

**其他参数：**
- `--format mp3|wav`：音频格式（默认 mp3）
- `--sample-rate <hz>`：采样率（默认 32000）
- `--pitch <n>`：音调调整
- `--volume <n>`：音量

## music generate — 音乐生成

**自动生成歌词（从 prompt 推断）：**
```bash
mmx music generate --prompt "欢快的夏日流行歌曲" --lyrics-optimizer --out summer.mp3
```

**指定歌词：**
```bash
mmx music generate --prompt "温暖的民谣" --lyrics "[Verse]
月光洒在窗台上
夜风轻轻吹过" --out folk.mp3
```

**纯器乐（无人声）：**
```bash
mmx music generate --prompt "史诗电影配乐，渐进的弦乐" --instrumental --out epic_bgm.mp3
```

**指定曲风、节奏、人声：**
```bash
mmx music generate --prompt "独立流行" --vocals "温柔的男声" --genre pop --bpm 120 --out indie.mp3
```

**从文件读取歌词：**
```bash
mmx music generate --prompt "电子音乐" --lyrics-file song.txt --out electronic.mp3
```

**其他参数：**
- `--model music-2.6`：推荐模型；`music-2.6-free` 免费无限制；`music-2.5+`；`music-2.5`
- `--format mp3`：音频格式（默认 mp3）
- `--aigc-watermark`：嵌入 AI 内容水印

## music cover — 歌曲翻唱

**基于原始音频生成翻唱版本：**
```bash
mmx music cover --prompt "Jazzy version of this song" --audio-file original.mp3 --out cover.mp3
```

**从 URL 获取音频：**
```bash
mmx music cover --prompt "Acoustic version" --audio https://example.com/song.mp3 --out acoustic.mp3
```

## search query — 网页搜索

```bash
mmx search query --q "MiniMax 最新模型发布"
mmx search query --q "2025年建筑设计趋势" --output json
```

## vision describe — 图片理解

**本地图片：**
```bash
mmx vision describe --image photo.jpg
mmx vision describe --image screenshot.png --prompt "这张截图里有哪些 UI 元素？"
```

**在线图片：**
```bash
mmx vision describe --image https://example.com/diagram.png --prompt "描述这个系统架构图"
```

**指定描述问题：**
```bash
mmx vision describe --image data_chart.png --prompt "这张图表展示的主要数据趋势是什么？"
```

## quota show — 查看配额

```bash
mmx quota show
```

显示当前周期的 Token Plan 配额余量。

## 批量图片分析（batch vision）

扫描文件夹内所有图片，使用 **subagent 并行** 分析，汇总 Markdown 报告。支持 50+ 图片规模。

**触发词**：「批量图片分析」「批量识别」「扫描图片」「跑图」「图片批量处理」

**执行流程：**

1. **扫描图片** — 用 `Glob` 遍历文件夹（支持 .jpg/.jpeg/.png/.webp），获取完整路径列表
2. **分批分组** — 每批最多 10 张图片，将图片列表均匀分成 N 个批次
3. **并发 spawn subagent** — 每批图片 spawn 一个 subagent（general-purpose），传入该批图片路径列表
4. **subagent 执行** — 对批次内每张图片顺序调用 `mmx vision describe`，收集结果
5. **汇总报告** — 主 agent 收集所有 subagent 的输出，合并写入 `batch_vision_report_YYYYMMDD_HHMMSS.md`

**subagent 指令模板（每批）：**
```
对以下图片路径逐一调用 mmx vision describe，将结果按顺序输出：

图片路径列表：
- /path/to/img01.jpg
- /path/to/img02.jpg
...

prompt 固定使用：详细描述这张图片，包括物品名称、材质、工艺细节、纹饰特征、色彩、风格年代判断。如有限定词或专业术语请保留原文。

输出格式（每张图片）：
## img01.jpg
**路径：** /path/to/img01.jpg
**分析结果：**
（mmx 输出）

---
```

**分批策略：**
- 图片总数 ≤ 10：张图片 → 1 个 subagent
- 10 < 图片总数 ≤ 50：每 10 张一批 → 最多 5 个 subagent 并发
- 50 < 图片总数 ≤ 100：每 10 张一批 → 最多 5 个 subagent 并发，其余排队等
- 图片总数 > 100：每 10 张一批 → 最多 5 个 subagent 并发，分批处理

**报告格式：**
```markdown
# 批量图片分析报告

**扫描文件夹：** `xxx`
**图片数量：** N
**成功：** X | **失败：** Y
**生成时间：** YYYY-MM-DD HH:mm

---

## 图片 1：文件名.jpg
**路径：** xxx
**分析结果：**
（mmx vision describe 输出）

---
```

**错误处理：**
- 单张图片失败不影响其他图片，继续执行
- 失败的图片在报告中标注 `❌ 识别失败` 及错误原因
- 报告中显示成功/失败计数

## 全局参数

- `--api-key <key>`：临时覆盖 API key
- `--region cn|global`：切换区域（默认 cn）
- `--output json|text`：输出格式
- `--quiet`：静默模式，抑制非必要输出
- `--verbose`：打印完整 HTTP 请求/响应（调试用）
- `--timeout <seconds>`：请求超时（默认 300s）
- `--no-color`：禁用 ANSI 颜色

## 典型工作流

### 1. 快速问答
```
mmx text chat --message "解释一下什么是微服务架构"
```

### 2. 生成配图
```bash
# 直接保存到项目文件夹
mmx image generate --prompt "智慧楼宇 IoT 架构图，扁平风格" --out-dir ./assets/ --out-prefix concept
```

### 3. 生成演示视频（I2V）
```bash
# 等待完成并下载
mmx video generate --prompt "镜头缓慢推进，展示室内空间" --first-frame ./keyframes/scene1.jpg --download ./video/scene1.mp4
```

### 4. 语音播报
```bash
# 默认使用 Chinese (Mandarin)_Southern_Young_Man 音色
mmx speech synthesize --text "以下是今日项目进度报告..." --out daily_report.mp3
```

### 5. 背景音乐
```bash
mmx music generate --prompt "科技感演示片配乐，中等节奏" --instrumental --out intro_bgm.mp3
```

### 6. 图片内容提取
```bash
mmx vision describe --image ./diagram.png --prompt "提取图中所有技术术语和它们的关系"
```

## 注意事项

- mmx 已全局安装，直接调用即可，无需额外设置
- 视频生成默认等待完成（--download），如果任务时间较长可能需要耐心
- 使用 `--async` 或 `--no-wait` 可立即返回 task ID，单独查询状态
- 输出路径使用相对路径时，相对于当前工作目录
- Windows 系统上路径分隔符用 `/` 或 `\` 均可
- 涉及中文字符的输出注意控制台编码（mmx 默认已支持 UTF-8）