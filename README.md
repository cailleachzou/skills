# Claude Code Skills

> 本仓库存储所有自定义 Claude Code 技能

## 技能列表

| 技能                      | 触发关键词                | 功能                                |
| ----------------------- | -------------------- | --------------------------------- |
| **computer-repair-skill** | 电脑维修、C盘爆满、卡顿、流氓软件、断网、蓝屏、数据恢复、打印机、应用迁移、OpenClaw | 跨平台电脑维修助手 — 64 个按需加载 Playbook，覆盖诊断/清理/性能/网络/安全/开发者工具（先取证、再计划，确认后修改）；来源 [88lin/computer-repair-skill](https://github.com/88lin/computer-repair-skill) |
| **docling**           | Docling、文档解析、PDF解析、转Markdown、提取表格 | 文档解析与转换（IBM Docling）— PDF/DOCX/PPTX/XLSX/HTML/图片/音频 → Markdown/JSON（含 OCR） |
| **dwg**               | DWG、DXF、CAD、图纸、翻译、转换、提取文字、_ZH | DWG 图纸操作 — ODA File Converter 转换（DWG↔DXF）+ ezdxf 提取/回填 + 对话翻译 → 输出 *_ZH.dwg |
| **ffmpeg**            | FFmpeg、转码、视频、音频    | 音视频转码、批量处理、预设管理、会话管理 |
| **pdf2zh**            | PDF 翻译、pdf2zh       | **默认走本地 2B**（MiniCPM5-2B + llama-server，0 token、不出本机）—— `-s openailiked:<模型>`；云端服务为质量兜底（1.9.11 实测 22 引擎）。v1.9.11（uv tool 隔离安装）；⚠️ 需把 `tencentcloud-sdk-python-tmt` 钉在 3.1.70，否则启动即 ImportError。Zotero 插件见技能内 `references/zotero-plugin.md` |
| **officecli**         | Office、docx、xlsx、pptx | 创建/检查/修改 Office 文档（.docx/.xlsx/.pptx） |
| **tyc-it**            | 天眼查、企业查询、尽调、股权、风险 | 天眼查 CLI「天眼一下」— 商业查询、尽调、主体核验、关联关系、司法风险等 |
| **graphify**          | 代码库、架构、知识图谱、文件关系、god nodes、graphify-out | 把任意目录（代码/文档/论文/图片/视频）转成持久知识图谱 — 社区检测、god nodes、query/path/explain；输出交互式 HTML + GraphRAG JSON + GRAPH_REPORT.md |
| **local-ai**          | 本地模型、离线、最简单任务、省电、隐私、本机、本地 agent、批量改写/分类/抽取 | 本机本地模型 — llama.cpp CUDA b10883 + RTX 5060 Laptop 8GB；**默认 2B**（MiniCPM5-2B，~85–107 tok/s / 128K，并发 4 ≈ 2× 串行；别名 `llama`），需要 pi agent / 代码 / 复杂推理时才切 **9B**（Qwen3.8-9B-Distill，~55 tok/s / 32K；别名 `llama9`）；批量跑完自动落 `<out>.report.md` 回执，主模型只读回执；读写文件/多步闭环交给 pi CLI 当本地 agent；`start.sh` 幂等切换、`stop.sh` 收工释放显存；视觉/OCR/音频默认走本地多模态（`vl4`/`vl8`/`asr`/`ocr`，0 token、不出本机），视频与高难度视觉推理回退 mimo；**单张图要跟对话上下文一起推理、且不敏感时，主模型自己就能看**（2026-09-12 起，免起本地模型）；**mimo 兜底路径的完整调用参考**（凭据 / 端点 / curl 模式 / 模型表 / TTS 音色）见 [`local-ai/references/mimo-api.md`](local-ai/references/mimo-api.md) |
| **ncm-dump**          | ncm、网易云、加密音乐、mp3、flac | 解密网易云 .ncm 加密音乐 → 通用 mp3/flac（AES-128 + 自定义 RC4 变体） |

## 已安装插件（Plugins）

> 下表按 `claude plugin list` 实测结果同步，**全部为 user scope**（换目录也生效）。

| 插件                       | 源地址                     | 状态      | 说明                                    |
| ------------------------ | ----------------------- | ------- | ------------------------------------- |
| **claude-api**           | anthropic-agent-skills  | ✅ 启用    | Claude API 技能 — SDK 集成、Tool Use、Streaming、Batch 等（2026-09-12 启用；此前因疑似与内置 `claude-api` 技能重名而禁用，**该理由未证实**） |
| **claude-md-management** | claude-plugins-official | ✅ 启用    | CLAUDE.md 管理工具 — 项目/用户级指令文件管理           |
| **code-review**          | claude-plugins-official | ✅ 启用    | 代码审查工具 — 多维度代码质量检查                    |
| **document-skills**      | anthropic-agent-skills  | ✅ 启用    | 文档处理技能 — docx/pdf/pptx/xlsx 创建编辑     |
| **example-skills**       | anthropic-agent-skills  | ✅ 启用    | 官方示例技能集（12 个）— algorithmic-art / canvas-design / doc-coauthoring / internal-comms / mcp-builder / slack-gif-creator / theme-factory / web-artifacts-builder / webapp-testing 等 |
| **frontend-design**      | claude-plugins-official | ✅ 启用    | 前端设计辅助工具                              |
| **playground**           | claude-plugins-official | ✅ 启用    | Playground 实验工具 — 交互式测试环境            |
| **skill-creator**        | claude-plugins-official | ✅ 启用    | 官方技能创建工具                              |
| **superpowers**          | claude-plugins-official | ✅ 启用    | Claude Code 超级能力增强（14 个流程技能）          |

## 目录结构

```
skill-name/
├── SKILL.md          # 技能定义（YAML frontmatter + 说明）
├── scripts/          # 可执行脚本
├── references/       # 参考文档
├── assets/           # 模板、图标、字体
└── evals/            # 测试用例
```

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/cailleachzou/skills.git

# 查看所有技能 — 直接看本文件即可
```

## 学习资料

- [`docs/notes/SKILL-MAP.md`](docs/notes/SKILL-MAP.md) — **插件技能地图**（8 个插件 / 34 个技能，按使用场景分桶，附触发词速查）；⚠️ 只覆盖**插件**技能，**不含本仓库自建的 10 个技能**

## 环境依赖

### Python 环境

**Python 路径**（Windows）：`C:\Users\caill\AppData\Local\Programs\Python\Python314\python.exe`
> 所有 Python 技能统一用 `py -3` 调用（唯一安装的 3.14.7）。勿用 `python3`——那是 Microsoft Store 的占位程序；裸 `python` 虽可用但不如 `py -3` 明确。

| 技能            | Python 包          | 其他依赖                                                              |
| --------------- | ----------------- | --------------------------------------------------------------------- |
| **docling**     | 独立 venv（见下）  | ✅ 已装 **2.126.0**（torch 2.14.0），venv 在 `C:\Users\caill\.venv-docling`（Python 3.12）|
| **dwg** | `ezdxf` | ODA File Converter（`C:\Program Files\ODA\ODAFileConverter 27.1.0\`）；系统 Python `py -3`（ezdxf 1.4.4，无独立 venv、无 AutoCAD、无 MIMO） |
| **ffmpeg**     | `click >= 8.0`    | ffmpeg, ffprobe（PATH 中）                                            |
| **pdf2zh**     | 无（uv tool 自带）  | ✅ 已装 **1.9.11**（uv tool 隔离环境）；版面走 onnxruntime，**不依赖 torch**；翻译引擎默认走本地 2B（`-s openailiked` + llama-server），云端为兜底 |
| **local-ai**   | 无（脚本只用标准库） | 文本/多模态 GGUF 见下；文档 OCR 另用独立 venv（见下） |

> **docling 用独立 venv**（勿用系统 Python）—— ✅ 已装于 `C:\Users\caill\.venv-docling`（Python 3.12.14；docling 2.126.0 + torch 2.14.0）
> 调用：`C:\Users\caill\.venv-docling\Scripts\docling.exe convert <source> --to md --output <dir>`
> 子命令只有 `convert` 与 `convert-remote`，**根级没有 `--version`**（`docling --version` 会转去加载流程并长时间无响应）
> ⚠️ 需设 `TORCH_COMPILE_DISABLE=1 TORCHINDUCTOR_DISABLE=1`（torch 在无 MSVC 环境下报错）
> 模型缓存 `~/.cache/huggingface/`，**首次运行才下载**（约 2GB）
> 重建：`uv venv ~/.venv-docling --python 3.12 && uv pip install --python ~/.venv-docling docling`

> **local-ai 多模态另需**（GGUF 落在 `D:\models\gguf\`，每个模型 = 权重 + 配套 mmproj，均由 `hf download` 取得）：
> - 视觉 `vl4` / `vl8`：`Qwen/Qwen3-VL-4B-Instruct-GGUF`（Q4_K_M **2497 MB** + mmproj F16 836 MB）、`Qwen/Qwen3-VL-8B-Instruct-GGUF`（Q4_K_M **5028 MB** + mmproj Q8_0 752 MB）
> - 语音 `asr`：**社区仓库** `JamePeng2023/Qwen3-ASR-1.7B-GGUF`（Q8_0 **2165 MB** + mmproj BF16 642 MB；官方 Qwen 组织无此 GGUF）
> - 文本：`MiniCPM5-2B-Q8_0.gguf` 2.68 GB、`Qwen3.8-9B-Q4_K_M.gguf` 5.78 GB（见 `local-ai/SKILL.md`）
> - 文档 OCR：`baidu/Unlimited-OCR` 全仓库 → `D:/models/unlimited-ocr/`（约 6.8 GB），另建 venv `D:/models/venvs/unlimited-ocr`（`uv venv --python 3.12`；`torch==2.10.0` + `torchvision==0.25.0` 走 **cu130** 索引，官方测试组合为 Python 3.12.3 + CUDA 12.9）
>   - ⚠️ **索引必须是 cu130，不是 cu129**：`ocr/requirements.txt` 已把本地版本号钉成 `+cu130`（`torch==2.10.0+cu130` / `torchvision==0.25.0+cu130`），索引不匹配会**直接报错**，不会静默回落 CPU 版（CPU 版会让 OCR 慢到不可用且不报错）
> - ✅ **权重与 venv 均已到位**：6 个多模态 GGUF（`vl4`/`vl8`/`asr` 各一份权重 + 一份 mmproj，见上）+ OCR 全仓库 + venv `D:/models/venvs/unlimited-ocr`，`start.sh vl4/vl8/asr` 与 `ocr/run.sh` 均可直接用；实测显存账本见 [`local-ai/README.md`](local-ai/README.md) §1.1

### CLI 工具

| 工具                                                       | 技能路径            | 说明                       |
| -------------------------------------------------------- | ----------------- | ------------------------ |
| **ODA File Converter 27.1.0**                            | `dwg/`             | DWG ↔ DXF 无损双向转换（严格校验，失败产出 `*.err` 含报错行号）|
| **ffmpeg / ffprobe**                                     | `ffmpeg/`         | 音视频转码                    |
| **pdf2zh.exe**                                           | `pdf2zh/`         | ✅ 已装 v1.9.11 — `C:\Users\caill\.local\bin\pdf2zh.exe`（PDFMathTranslate 引擎）|
| **docling.exe**                                          | `docling/`        | ✅ 已装 v2.126.0 — `C:\Users\caill\.venv-docling\Scripts\docling.exe`（独立 venv）|
| **hf**                                                   | —（无配套技能）    | Hugging Face Hub CLI（`huggingface_hub`，pip 安装，命令在 `Python314\Scripts\hf.exe`，已入用户 PATH；直接用 CLI 即可）|

> **uv tool 装的命令**（`pdf2zh`、`graphify`、`graphify-mcp`）位于 `C:\Users\caill\.local\bin\`，已用 `uv tool update-shell` 写入**用户 PATH**——⚠️ **只对之后新开的终端生效**，已开的窗口读不到。
> graphify 的真实包版本是 **0.9.58**，仓库内 `graphify/` 技能目录已于 2026-09-12 用 `graphify install --platform claude` 同步到 **0.9.58**（`graphify/.graphify_version` 可查）。⚠️ **0.9.57 → 0.9.58 的 SKILL.md 内容逐字节相同**（md5 一致），只有版本戳变化 —— 该版本号的告警是纯版本比较，不代表技能内容有更新。

### 浏览器自动化（webapp-testing / Playwright）

插件 `example-skills:webapp-testing` 走 **Python Playwright**（非 Node），本机已于 2026-09-13 配好：

- `playwright` **1.62.0**（系统 Python 3.14.7；`py -3 -m pip install playwright`，有 cp314 wheel）
- 浏览器内核在 `C:\Users\caill\AppData\Local\ms-playwright\`：`chromium-1234`（Chrome for Testing **151.0.7922.34**）、`chromium_headless_shell-1234`、`ffmpeg-1011`、`winldd-1007`
- ⚠️ **下载源已切国内镜像**：官方 `cdn.playwright.dev` 实测在下到 **10%（191.8 MiB 的 `chrome-win64.zip`）时被掐断**，重试时好时坏。已执行 `setx PLAYWRIGHT_DOWNLOAD_HOST "https://cdn.npmmirror.com/binaries/playwright"`（**只对之后新开的终端生效**）。装/重装内核：`py -3 -m playwright install chromium`。镜像路径实测 `.../binaries/playwright/builds/cft/<版本>/win64/<文件>` 返回 200
- ⚠️ **`with_server.py` 已打本地补丁** —— 重打脚本：[`docs/patches/reapply-webapp-testing-win-patch.py`](docs/patches/reapply-webapp-testing-win-patch.py)。原版在 `finally` 里用 `process.terminate()` 收服务器，而 Windows 上 `shell=True` 起的 `cmd.exe` 被杀死后，真正干活的 `python.exe` 会**变成孤儿进程继续占着端口**（脚本仍打印 "All servers stopped"，具有误导性）。补丁改为 `os.name == "nt"` 时走 `taskkill /F /T /PID` 杀整棵进程树。**`claude plugin update` 会覆盖该文件，更新后需跑一次重打脚本**（幂等、行尾无关，已往返验证与当前文件字节一致）
- 实测全链路（含补丁后复测）：`with_server.py` 起静态服务 → 无头 Chromium 访问 → `wait_for_load_state('networkidle')` → 点击按钮 → 截图 → 收服务；端口释放、无残留进程
- ⚠️ 技能自带的 examples 里写死了 `/tmp/xxx.png` 这类 Unix 路径，Windows 下需换成 `C:\Users\caill\AppData\Local\Temp\...`

#### 未采用：ego lite（`citrolabs/ego-lite`）

2026-09-13 评估后**不装**。它是合法的 Claude Code 插件市场（市场名 `ego-agent-skills`，插件 `browser-skills`，技能 `ego-browser` v2.0.0），但 **ego lite 目前只有 macOS 版**（README 明载 Windows/Linux 在 roadmap；下载只有 arm64/x64 两个 DMG），`ego-browser` 命令由该桌面应用提供，仓库里的 npm 包 `ego-browser-v2` 只是跑在 ego 浏览器**内部**的 helper 运行时，不能独立使用。装到 Windows 上只有技能文件、命令不存在。想在 Mac 上用：`claude plugin marketplace add citrolabs/ego-lite && claude plugin install browser-skills@ego-agent-skills`。
