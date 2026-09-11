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
| **local-ai**          | 本地模型、离线、最简单任务、省电、隐私、本机、本地 agent、批量改写/分类/抽取 | 本机本地模型 — llama.cpp CUDA b10883 + RTX 5060 Laptop 8GB；**默认 2B**（MiniCPM5-2B，~85–107 tok/s / 128K，并发 4 ≈ 2× 串行；别名 `llama`），需要 pi agent / 代码 / 复杂推理时才切 **9B**（Qwen3.8-9B-Distill，~55 tok/s / 32K；别名 `llama9`）；批量跑完自动落 `<out>.report.md` 回执，主模型只读回执；读写文件/多步闭环交给 pi CLI 当本地 agent；`start.sh` 幂等切换、`stop.sh` 收工释放显存；视觉/OCR/音频默认走本地多模态（`vl4`/`vl8`/`asr`/`ocr`，0 token、不出本机），视频与高难度视觉推理回退 mimo；**mimo 兜底路径的完整调用参考**（凭据 / 端点 / curl 模式 / 模型表 / TTS 音色）见 [`local-ai/references/mimo-api.md`](local-ai/references/mimo-api.md) |
| **ncm-dump**          | ncm、网易云、加密音乐、mp3、flac | 解密网易云 .ncm 加密音乐 → 通用 mp3/flac（AES-128 + 自定义 RC4 变体） |

## 已安装插件（Plugins）

> 下表按 `claude plugin list` 实测结果同步，**全部为 user scope**（换目录也生效）。

| 插件                       | 源地址                     | 状态      | 说明                                    |
| ------------------------ | ----------------------- | ------- | ------------------------------------- |
| **claude-api**           | anthropic-agent-skills  | ⚠️ 已禁用  | Claude API 技能 — SDK 集成、Tool Use、Streaming、Batch 等（与内置 `claude-api` 技能重名，禁用以免打架） |
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

- [`learning/SKILL-MAP.md`](learning/SKILL-MAP.md) — **插件技能地图**（8 个插件 / 34 个技能，按使用场景分桶，附触发词速查）；⚠️ 只覆盖**插件**技能，**不含本仓库自建的 10 个技能**

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
> graphify 的真实包版本是 **0.9.57**，而仓库内 `graphify/` 技能目录仍是 **0.9.26** 的副本（`graphify --help` 会就此告警，用 `graphify install --platform claude` 刷新）。

---

## 更新日志

### 2026-09-11
- **pdf2zh 技能重构**：① 默认路径改为**本地 2B 直连** —— `openailiked` + llama-server（`local-ai` 技能）接 MiniCPM5-2B，0 token、不出本机，含「BASE_URL 必须带 `/v1`」「服务名后的模型名只是标签（llama-server 忽略请求里的 model 字段）」「缓存键不含 `base_url`，换端点会命中旧译文」「pdf2zh 硬编码 `temperature: 0` 与 MiniCPM 推荐值 1.0 冲突」四条实操坑；② **服务表由 1.7.9 时代的 6 个订正为 1.9.11 源码实测的 22 个**，并指出上游 main 文档里的 `302ai`/`minimax` 在 1.9.11 中不存在；③ **订正上游事实**：`Byaidu/PDFMathTranslate` 已改名 `PDFMathTranslate/PDFMathTranslate`（旧路径 301，未归档仍在维护），2.0 主线迁至 `PDFMathTranslate-next`（`pdf2zh-next` 2.9.0，无 `-s`、改 `config.toml` + `PDF2ZH_` 前缀、Bing/Google 已 deprecated），本机仍只装老版 1.9.11；④ **新增 `references/zotero-plugin.md`**（Zotero 插件 `guaguastandup/zotero-pdf2zh`，本机未装 Zotero，通篇标注上游口径未实测）；⑤ **删除 `agent_translator_patch.py`（393 行）与 `test_agent_translator.py`（122 行）** —— 为 1.7.9 写、本机从未打上、未复验，其目标已由本地 2B 直连覆盖，且上游两版均无插件机制。**实测**（15 页 arXiv 双栏论文走本地 2B）：公式符号逐页保留零缺失、13 页约 5 分钟、`-t 4` 只吃满 2 槽；**`--ignore-cache` 实测无效**（复跑产出未翻译原文），强制重译须删 `%TEMP%\cache\`。设计见 `docs/superpowers/specs/2026-09-11-pdf2zh-skill-overhaul-design.md`，实测台账见 `docs/superpowers/plans/2026-09-11-pdf2zh-verification.md`
- **CLAUDE.md 瘦身**（用户级 `~/.claude/CLAUDE.md`，8650 B → 4132 B，省 52%）：该文件**每次会话全文进上下文**，5 段低频内容合计占 56%，本次全部移出，**CLAUDE.md 内不留指针**。① 「插件坏了怎么自查」runbook **整段删除**（不建技能、不留指针）；② 「多模态任务处理（mimo API）」的 curl 调用参考 → 新建 [`local-ai/references/mimo-api.md`](local-ai/references/mimo-api.md)（「什么时候该回退」仍留在 `local-ai/SKILL.md`，不重复）；③ 删除「PDF 工具链」「密钥环境（2026-09）」「常用命令」三段。**注意**：`CLAUDE.md` 里的 `@import` 是启动时一并载入，省不了 token——真正省钱的出路只有「删掉」或「搬进按需加载的技能/reference」。改动前已备份至 `~/.claude/backups/CLAUDE.md.bak-20260911`
- **local-ai 新增多模态三路径**：Qwen3-VL-4B/8B（视觉，`vl4`/`vl8`）、
  Qwen3-ASR-1.7B（语音，`asr`）走 llama.cpp 主干；baidu/Unlimited-OCR（文档解析）
  走独立 venv（`D:/models/venvs/unlimited-ocr`）
- 显存账本：vl4 ~4.5GB / asr ~4.6GB / vl8 ~6.4GB（贴边，备用）/ ocr ~6.9GB（贴边）
- 边界改写：图像/音频/文档**默认走本地**（隐私、0 token），视频与高难度视觉推理回退 mimo
- docling 与 Unlimited-OCR 的分工：有字可选 → docling；扫描图 → Unlimited-OCR

- **2026/09/10** **local-ai 新增 [`README.md`](local-ai/README.md)** —— 技能本身有 `SKILL.md` 讲「怎么派活」，缺的是一份**面向 8GB 笔记本显卡的安装与选型说明**，本次补齐。主要内容：① **把 8GB 显存作为一切决策的起点**，给出实测显存账本（2B@128K → 整卡 6514 MiB；9B@32K → ~6900；9B@256K → 7561/8151 **近满且慢 35%**，因 KV 溢出挤层到 CPU）；② **依赖清单分三档** —— 必须装（NVIDIA 驱动 592.01、llama.cpp `b10883` CUDA 13.3 预编译包、两个 GGUF、Python 3.14.7、curl、nvidia-smi）、可选（Git Bash 别名、pi CLI 0.85.1）、**刻意不装**（ollama 已卸载、PyTorch/transformers、mmproj）；③ 强调 **Python 侧零第三方依赖**（两个脚本只用标准库，无需 venv/pip）；④ **Blackwell 硬门槛**：`sm_120` 需 CUDA 12.8+，混入 CUDA 12 版构建会**静默退回纯 CPU**（慢 10 倍不报错），且必须 `b10883`+ 才能加载 9B 的 `qwen35`/Gated DeltaNet 架构；⑤ 解释**量化与上下文为何这么定**（2B 装得下就用 Q8_0、9B 卡在 Q4_K_M、KV 一律 `q8_0`），并给出 8GB 可行区间 **7B–9B @ Q4_K_M 是上限**；⑥ 从零复现步骤、脚本内三处硬编码路径（`LLAMA_DIR`/`MODEL_MINICPM`/`MODEL_9B`）的替换说明；⑦ 笔记本特有的散热/功耗/续航注意事项与收工 `stop.sh`；⑧ 8GB 上高频三坑排查表（静默退 CPU、显存爆挤层、架构不认）+ `--model` 只是标签的误判澄清
- **2026/09/10** **补齐缺失依赖**（全部隔离安装，不污染系统 Python）——① **docling** 2.126.0 → `C:\Users\caill\.venv-docling`（Python 3.12.14，torch 2.14.0）；② **graphify** 经 `uv tool install graphifyy` 装成 **0.9.57**；③ **pdf2zh** 经 `uv tool install` 装成 **1.9.11**；④ **pycryptodome** 3.23.0 补入系统 Python（ncm-dump 依赖）。**排障记录**：`pdf2zh 1.9.11` 装好后**启动即崩** —— `ImportError: cannot import name 'TextTranslateRequest' from 'tencentcloud.tmt.v20180321.models'`。根因是**上游依赖漂移**：该 SDK 新版移除了 `TextTranslateRequest`，而 pdf2zh 在模块**顶层**硬导入它，与是否使用腾讯翻译无关，因而连 `--help` 都跑不起来。修法：把 `tencentcloud-sdk-python-tmt` 钉到 **3.1.70**（该类尚存的版本），实测 `pdf2zh --version` 恢复正常。**环境变更**：uv tool 的可执行文件落在 `C:\Users\caill\.local\bin`，原先**不在 PATH**，已用 `uv tool update-shell` 写入用户 PATH（⚠️ 只对新开终端生效）。**顺带纠正四条版本事实**：① pdf2zh **1.8.0+ 要求 Python `<3.13`**，系统 Python 为 3.14，故 pip 在 3.14 上会**自动退回 1.7.9**（无版本约束）——uv 用 3.12 才装到 1.9.11，这正是旧文档通篇按 1.7.9 写的原因；② 1.9.11 **已支持 `-o/--output`**，旧文档「旧版 CLI 无 `-o`」作废；③ 1.9.11 版面改走 **onnxruntime，不再需要 torch**，旧文档的 torch 依赖描述不再成立；④ docling 根级**没有 `--version`**，只有 `convert` / `convert-remote` 两个子命令
- **2026/09/10** 从 [88lin/computer-repair-skill](https://github.com/88lin/computer-repair-skill) 引入 **computer-repair-skill**（第三方技能，非本仓库自建）：跨平台（Windows/macOS/Linux）电脑维修助手，`SKILL.md` + `references/` 下 64 个按需加载 Playbook（诊断/清理/性能/网络/安全/备份/驱动/启动与 WinRE/BitLocker/分区/数据恢复/开发者工具/OpenClaw 配置），另含 `agents/openai.yaml`（Codex 侧适配）与 `references/tools-{windows,macos,linux}.md`；纯 Markdown、无可执行脚本，安装即被 Claude Code 自动发现。取 `skills/computer-repair-skill/` 整目录复制入本仓库，共 77 个文件
- **2026/09/10** **死链清理**（承接上条文档同步，补完遗漏项）：① **学习资料**小节 4 条链接的目标文件已随学习资料重构删除（`learning/` 下现仅存 `SKILL-MAP.md`），全部改指该文件并按实描述——8 插件 / 34 技能，且**不含本仓库自建的 9 个技能**（原描述「38 个技能按功能域分类」亦不实）；② **插件表**按 `claude plugin list` 实测重建：删去从未安装的 `cli-anything`、`obsidian-skills` 两行，补上一直漏记的 `example-skills`，`claude-api` 标注**已禁用**（与内置同名技能冲突），新增「状态」列并注明全部为 user scope；③ CLI 工具表 `pdf2zh.exe` 行与依赖表「本机未安装」自相矛盾，已统一标注；④ `pdf2zh/SKILL.md` 失实声明订正：原文称「本机已装 PyPI 最新版 1.7.9」「## 安装（已完成）」，实测 `Python314\Lib\site-packages\pdf2zh` 与 `pdf2zh` 命令**均不存在**，改为顶部醒目标注未安装；Ollama 服务行标注「本机已于 2026-09-10 卸载，此路不通」并从 frontmatter description 中移除该引擎名。**注**：历史更新日志中的旧机器路径（`C:\Users\59620\`、`pythoncore-3.14-64`）按"不改写历史"原则原样保留
- **2026/09/10** **文档同步**：README 环境依赖与清单对齐实机 —— ① 旧机器路径 `C:\Users\59620\` 订正为 `C:\Users\caill\`（Python 安装路径、hf 命令位置）；② 标注 **docling** 与 **pdf2zh** **本机未安装**（原文档称"已装"，实际既无 venv 也无 exe；PDF 文本链实走 `pymupdf`/`pdfplumber`/`pypdf`/`pypdfium2`）；③ 技能表删除已不存在的 **hf-cli**（于 77e87c9 随 volc-ark 一并删除，该次提交信息未提及）与 **diagram-skill**，"其他环境"小节随之清空；④ 补录 178b646 新增却遗漏至今的 **graphify**。历史更新日志中的旧机器路径按"不改写历史"原则原样保留
- **2026/09/10** **dwg** 技能修复（**dwg-translate** 重构后的首次维护）：① SKILL.md 全部命令路径由 `C:\Users\caill\.pi\agent\skills\dwg\` 改为实际的 `C:\Users\caill\.claude\skills\dwg\`（原路径不存在，照抄必失败）；② 脚本启动强制 stdout/stderr 走 UTF-8 —— 本机控制台代码页为 cp1252 而非 936，所有中文 print 会抛 `UnicodeEncodeError` 直接崩掉命令；③ 静音 ezdxf 首次导入时 fontTools 扫描 `mstmc.ttf` 的 stderr 噪音；④ MTEXT 回填增加归一化容错匹配（`\P` 等价真实换行、忽略空白差异），并把译文里的真实换行折算回 `\P`，避免静默失配与坏 DXF；⑤ `extract` 输出目录由随机 `dwg_extract_<时间>/` 改为固定 `<stem>_提取/`，可重复运行不留垃圾；⑥ 补齐 `translate`/`apply-back` 的文档（原 docstring 与实现不符）。依赖核实：ezdxf 1.4.4（原文档称已装，实际缺失，本次补装）、ODA File Converter 27.1.0（已装），`check` 自检通过
- **2026/09/10** **local-ai** 技能 v6.2：从「本地模型说明书」改成**主模型的派活规程**，主线一条 —— *批量同质小活 → 本机跑完（0 token）→ 结果回流本对话 → 主模型整体审阅 → 分级落地*；并围绕**本机只有一块 GPU** 这个硬约束重排选型。① **默认模型定为 2B**：`start.sh` 默认值保持 `minicpm`。中途一度改成 `9b`（想表达「量大才切 2B」），但 `~/.bashrc` 的别名 `llama='start.sh'`（**无参**）正是靠脚本默认值来区分两个模型的 —— 默认一变，`llama` 和 `llama9` 就都去起 9B 了，于是回退。**教训：脚本的默认值不是内部细节，它是别名 / 外部调用语义的一部分，改之前先搜谁在依赖它**（同一教训也适用于 `.bat`）。选型理由也一并修正：2B **不是「9B 的降级备用」** —— 它同样有 tool use（pi 拿它跑多步 agent 闭环成立）、还有 128K 上下文，整体覆盖面比 9B 更广；9B 只在代码 / 长链推理这类真正难的活上才值得切。② **选型提为「派发第 1 步」**：模型是派发指令的一部分，一轮只用一个，不为单条任务来回切 —— 切换代价是重启 + 丢前缀缓存。③ **`start.sh` 改成幂等切换**：先问在跑的是哪个模型，已是目标就 `[复用]` 不重启，是别的才先停后启；**新增 `scripts/stop.sh`**（+ `stop.bat`），杀进程后**轮询显存直到真的回落**才返回 —— 否则新模型会有部分层掉到 CPU（不报错、只慢十倍）。实测 6541 → 1009 MiB，重复调用幂等。④ **`llama_batch.py` 跑完自动落 `<out>.report.md` 回执**：条数/成功/失败、异常清单（失败、空结果、原样回显、带代码块围栏、JSON 解析失败、过短）、抽样 3–5 条、以及 **server 实际加载的模型名**；主模型只读回执，不再把全量 JSONL 灌进上下文（那等于把省下的 token 又花回去）。建议按故障类型分岔：全连接类失败提示查 `/health`，格式类异常才提示补 one-shot 示例。⑤ **定下一条硬规则：9B 不并发**，要并发就切 2B。依据是订正了一条被 `/slots` 误导的推断 —— `-c 32768` 时 `/slots` 显示每槽 `n_ctx = 32768`，看着像 4 路各 32K；但启动日志写的是 `n_slots = 4, n_ctx_slot = 32768, kv_unified = 'true'`，**KV 是一个共享池**，4 个 slot 从同一个 32K 池子里取，而整卡只剩不到 1GB 余量（实测 6891 MiB / 8151，模型权重本身已占 5502 MiB）。2B 没这个问题（池子 128K、每槽 32K，并发 4 实测约 2× 串行）。`llama_batch.py` 检测到 server 跑着 9B 且 `-j > 1` 时会直接警告。 ⑥ 顺带修掉 v6.1 里过时的「pi 须加 `--no-extensions`」表述（`packages` 已清空，默认即可跑）
- **2026/09/10** **local-ai** 技能 v6.1：补齐「大量任务」闭环，并接入 **pi 当本地 agent**。① 新增 `scripts/llama_batch.py`（批量并发：text/JSONL 输入自动探测、`-j` 并发默认 4 对齐 server `n_slots`、`--no-think`、`--resume` 断点续跑、`--retries` 单条重试、结果按输入顺序落 JSONL，单条失败记入 `error` 不中断整批）；实测并发 4 约 2× 串行吞吐（84 → 169 tok/s），并发 8 基本无增益。② SKILL.md 重写为「subagent / 主模型如何使用本技能」的视角，新增「裸模型是函数、套上 pi 才是 agent」的心智模型、派发模板、结果校验清单，以及两条实跑出来的 prompt 坑：JSON 示例里写字面说明会被 2B 照抄进答案（30 条里 24 条把公司名抽成 `null`）、纯指令约束不住它须给 one-shot 示例（60 条里 26 条原样回显，加示例 + `-t 0.2` 后 60/60 合格）。③ **pi CLI 本地 agent**（provider `llamacpp` 已在 `~/.pi/agent/models.json` 配好）实测可用：`pi -p --no-skills --no-context-files …` 让本地 9B 自己读文件、改写、写盘，**10 条 11s、0 token**。关键发现是**编排类扩展会把小模型拖死** —— 原装的 `pi-subagents` 往 system prompt 塞约 7K tokens 编排说明（`workflowScript`/`runs.run`/lanes），9B 会去套那套 JavaScript 语法并反复重试陷入死循环（同一条任务 **400s+ 超时零产出 vs 关掉后 7s**，且不报错只表现为「慢」）；`~/.pi/agent/settings.json` 的 `packages` 已清空，**默认参数即可**，若重装此类扩展须加 `--no-extensions`。另发现 pi 的 `--model` 会被 llama-server **忽略**（单模型、忽略请求 model 字段），须与 server 实际加载的模型一致，否则静默用错模型
- **2026/09/10** **local-ai** 技能 v5.0 重写，对齐实机现状：模型换成 `D:\models\gguf` 现存的两个 —— **MiniCPM5-2B Q8_0**（轻量任务，纯文本 2.6B，实测 ~85–107 tok/s，随已生成长度衰减）与 **Qwen3.8-9B-Distill Q4_K_M**（代码/推理主力，`-c 32768` 实测 **~55 tok/s**；256K 时 ~37 tok/s，长上下文（~15K）约 43 tok/s）；llama.cpp 收敛到唯一构建 **cuda-b10883**（b10883 / CUDA 13.3，自带 cudart/cublas 13，旧 `cuda`/`cuda-new`/`cuda-b10872` 目录已删，须用 b10883 才能加载 9B 的 qwen35/Gated DeltaNet 架构）；**移除全部 CPU 路径**（不再静默降级，server 连不上直接报错提示）；两模型均为 thinking 模型，**默认开思考**（本机主要用途是跑 pi coding agent），关闭思考**必须走请求级** `chat_template_kwargs:{"enable_thinking":false}`（唯一有效机制，`llama_chat.py --no-think` 已内置；第三方 agent 不发该参数故天然开思考；server 端 `--reasoning off`/`--reasoning-budget 0`/`--chat-template-kwargs` 及 `--chat-template[-file]` 模板覆盖**实测全部失效**——上游 llama.cpp bug，PR #22336 至今未合并），实测同一改写请求 **8 tokens vs 300 tokens**；`chat.sh`/`chat.bat` 改为 `llama_chat.py` 薄封装（单轮逻辑只保留一份）；Qwen2.5 7B/14B、Qwen3.8-9B-Coder（输出塌缩不可用）均已删除
- **2026/09/10** 移除 **docs-translate** 技能（离线 Word/PPT/PDF 翻译）——其模型全部指向本机 GGUF；同时**卸载 Ollama**（程序、`~/.ollama` 15G 模型、`OLLAMA_*` 环境变量、PATH 条目）。本机翻译能力调整：PDF 翻译改走 **pdf2zh**（保留 layout），纯文本翻译用主模型/mimo。注：卸载时该技能脚本的 `MODELS` 已全部失效（1 个指向 `.ollama`、2 个指向不存在的 `C:\Users\caill\models`），本机可用 GGUF 实际位于 `D:\models\gguf`
- **2026/09/08** **local-ai** 技能换机重写（联想 83LT / Ryzen 9 8945HX + RTX 5060 Laptop 8GB / Blackwell sm_120）：从零搭建 llama.cpp CUDA b10864（`C:\Users\caill\tools\llama-cpp\cuda`，CUDA 13.3 runtime 须另配 cudart zip），模型官方 HF 直连下载至 `D:\models\gguf`（Qwen2.5 7B/14B Q4_K_M 分片 GGUF）；后端 **Vulkan → CUDA**（解除旧 CC6.1 限制）；实测 7B 整卡 decode ~39 tok/s / prefill ~1687、14B `-ngl 36` ~14 tok/s、7B 纯 CPU ~11 tok/s；删除 vision.py/ocr.py（新机无 Intel NPU，视觉/OCR 归 mimo/docling）；llama_chat.py 去除 ollama blob 引用、改 chatml 模板与新路径
- **2026/08/11** 新增 **hf-cli** 技能（Hugging Face Hub CLI）：`hf download/upload/models/datasets/spaces/jobs` 等，替代已废弃的 `huggingface-cli`；依赖 `hf`（pip `huggingface_hub` 1.27.0，命令在 `pythoncore-3.14-64\Scripts`，已加入用户 PATH）。同步新增 **ncm-dump** 技能（网易云 .ncm 加密音乐 → 通用 mp3/flac，AES-128 + 自定义 RC4，依赖 `pycryptodome`）
- **2026/08/11** **local-ai** 技能：文本主力由 `qwen3:4b` 替换为 `qwen2.5:3b`（Qwen2.5-3B-Instruct，Hugging Face 官方 GGUF 经魔搭镜像下载，Q4_K_M）——去除默认深度思考；已删除 qwen3:4b 模型。当前通道：qwen2.5:3b（iGPU 文本）、qwen2.5vl:3b（iGPU 视觉）、docling+rapidocr（NPU OCR）、bge-m3（嵌入）、whisper-small（转写）
- **2026/08/11** **local-ai** 技能：移除 **DeepSeek-R1-1.5B**（llama.cpp NPU 文本通道，生成文本不打印终端、无实用价值）——删除 `tools/llama-npu/`（2.3G）、`run-npu.bat` 及安装包；NPU 现仅用于 OCR（docling+rapidocr，约 5 倍加速）。当前通道：qwen3:4b（iGPU 文本）、qwen2.5vl:3b（iGPU 视觉）、docling+rapidocr（NPU OCR）、bge-m3（嵌入）、whisper-small（转写）
- **2026/08/11** 新增 **local-ai** 技能（本地模型处理最简单任务）：qwen3:4b（iGPU 文本）、qwen2.5vl:3b（iGPU 视觉，IPEX-LLM 版 ollama run 不支持 --images → 走 API 脚本 `scripts/vision.py`）、bge-m3（1024 维嵌入）、whisper-small（转写）；工具位于 `C:\Users\59620\tools\`
- **2026/08/08** 移除 **dxf-review** 技能（DXF 渲染预览/多模态对比/自动验证，已不再需要）；同步清理 CLAUDE.md 技能列表及 README 技能表
- **2026/08/08** 移除 **dwg** 技能（LibreDWG 工具链，dxf2dwg 大文件卡死 / dwg2dxf 丢失 AEC 对象）；新增 **dwg-translate** 技能（AutoCAD COM 直连 DWG + ezdxf + MIMO 批量翻译，输出 `*_ZH.dwg`）；依赖表新增独立 venv 与 AutoCAD 2027 说明；CLI 工具表以 AutoCAD 2027 (COM) 替换 LibreDWG
- **2026/08/07** 移除 **tendo-brand** 技能（目录已删）；README 技能列表及「其他环境」表中 Montserrat 字体依赖行一并清理
- **2026/08/07** 移除 **ocr** 技能（marker-pdf + Umi-OCR 双引擎），全面转用 **docling**；卸载全局依赖（marker-pdf venv、surya 模型、llama-server、Umi-OCR 程序+数据目录）
- **2026/08/07** 新增 **docling** 技能（IBM Docling 文档解析）：PDF/DOCX/PPTX/XLSX/HTML/图片/音频 → Markdown/JSON，含表格提取、OCR、RAG 分块；独立 venv（`~/.venv-docling`，Python 3.12）；wrapper 脚本固化 `TORCH_COMPILE_DISABLE/TORCHINDUCTOR_DISABLE`（torch 2.13 无 MSVC 报错）与 16GB 内存友好参数（`--page-batch-size`）
- **2026/08/07** mimo 全面切换计量计费：CLAUDE.md 新增「多模态任务处理」章节（图像/视频/音频理解、TTS、小任务备用，curl 直连 `api.xiaomimimo.com`）；pdf2zh 的 mimo 引擎、dxf-review 的 `compare`/`read-image` 均改为读环境变量 `MIMO_API_KEY`（sk- 开头），删除 tokenplan 引用；`mimo_multimodal` 模块依赖改为标准库 urllib 直连
- **2026/08/06** 拆除 cli-anything 路由器：将 5 个 CLI 子技能（ocr / dwg / dxf-review / ffmpeg / pdf2zh）提升为顶层独立技能（自动发现）；删除 cli-anything 包及 cctv-cad、web-search-fast、mimo 子技能
- **2026/07/22** 新增 survey-photo-workflow（勘察照片整理+归档+报告）、audio-meeting-minutes（录音转会议纪要）；tendo-brand 新增 delivery-order agent（出库单生成）
- **2026/06/12** 删除本地 docx/pdf/pptx/xlsx/skill-creator/theme-factory/markitdown 七个技能，改用 Plugin 或移除；卸载 claude-hud、ecc 插件；新增 claude-api、claude-md-management、code-review、document-skills、playground 插件
- **2026/06/10** 新增「已安装插件」章节，列出 4 个第三方插件 + 3 个官方插件的源地址和说明
- **2026/06/08** 移除 bailian-cli、mmx-cli；新增 cli-anything-pdf2zh（PDF 翻译，内置 MiMo 补丁）、cli-anything-web-search-fast（联网搜索）、mimo-multimodal（小米多模态理解）；同步更新 CLAUDE.md 与 README.md
- **2026/06/03** diagram-skill 升级为 subagent 架构：新增 `agents/mermaid-agent.md` 路由 15 种语法、`agents/examples-agent.md` 维护范本、`examples/` 6 个范本文件；新增 `.gitignore` 屏蔽 Slidev 符号链接、Python/Node 缓存
- **2026/05/27** 合并 dxf-text-translate 至 dxf-dwg-converter；新增环境依赖说明；bailian-cli 限制为 ASR only
- **2026/05/26** 新增 bailian-cli、cli-anything-ffmpeg、dxf-text-translate、mmx-cli；同步 SKILLS.md 与 README.md
- **2026/05/18** 初始导入：14 个技能 + SKILLS.md 清单