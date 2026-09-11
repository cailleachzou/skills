---
name: pdf2zh
description: "Translate PDFs with layout preserved (math formulas, two-column) via PDFMathTranslate. Default and preferred path is the LOCAL MiniCPM5-2B model over llama-server — 0 token, offline, nothing leaves the machine; cloud services (google free, deepseek, silicon, zhipu, deepl, any OpenAI-compatible) are the quality fallback. Also covers the Zotero plugin workflow (guaguastandup/zotero-pdf2zh). Use whenever a PDF needs translating: 论文 / 书籍 / 报告 PDF 翻译、保留公式与排版、双栏对照、不烧 token、离线或敏感文档、Zotero 里批量翻译附件。Installed on this machine via uv tool as v1.9.11; pin tencentcloud-sdk-python-tmt==3.1.70 or the CLI crashes on import. For Chinese with google use --lang-out zh-CN."
---

# pdf2zh —— PDF 翻译（保留公式与排版）

> ✅ 本机已装 **v1.9.11**（uv tool 隔离环境）。命令：`C:\Users\caill\.local\bin\pdf2zh.exe`
> PDFMathTranslate 解析 PDF 并保留布局（数学公式、双栏），翻译交给翻译引擎。
> 📄 Zotero 插件（在 Zotero 里直接翻附件）见 [`references/zotero-plugin.md`](references/zotero-plugin.md)。

## 默认路径：本地 MiniCPM5-2B 直连（0 token、不出本机）

```bash
# ① 起 2B llama-server（幂等：已在跑目标模型就复用）
"C:/Users/caill/.claude/skills/local-ai/scripts/start.sh" minicpm &
curl -s http://127.0.0.1:8080/health          # {"status":"ok"}

# ② 翻译（⚠️ -o 的目录必须已存在，1.9.11 不会自动创建，否则 FileNotFoundError）
mkdir -p out
OPENAILIKED_BASE_URL=http://127.0.0.1:8080/v1 \
  pdf2zh paper.pdf -s openailiked:minicpm5-2b \
    --lang-in en --lang-out zh-CN -t 4 -o out/

# ③ 用完释放显存（2B 占 6–7GB；不释放会挤占其它任务）
"C:/Users/caill/.claude/skills/local-ai/scripts/stop.sh"
```

产出 `out/<名字>-mono.pdf`（纯译文）与 `out/<名字>-dual.pdf`（双语对照）。

实测（2026-09-11，15 页 arXiv 双栏论文）：13 页翻译约 5 分钟，产物正常；
✅ **公式符号逐页保留，零缺失**（源 p4–p10 共 6 种符号，译文同页同种）；
`-t 4` 有并发但只吃满 2 槽（llama-server `n_slots=4`，实测仅 id 0/2 忙）。

**为什么是 `openailiked` 而不是 `openai`**：`openai` 服务要求 `OPENAI_API_KEY` 非空，否则 OpenAI SDK 构造直接抛错；`openailiked` 的 key 缺省**硬编码回落字符串 `"openailiked"`**，本地端点不用编 key。这也是上游对「本地自建 LLM」的官方答复（issue #792：llama-server 用 openai like 接入）。

**四条必踩的坑**：

| 坑 | 说明 |
|----|------|
| `BASE_URL` 末尾必须有 `/v1` | 少了直接 404（上游 `docs/ADVANCED.md` 原文要求） |
| `-s openailiked:<名字>` 里的名字是**标签** | llama-server **忽略请求体里的 `model` 字段**：写 9B 实际仍跑 2B，**且不报错**。核对实际模型：`curl -s http://127.0.0.1:8080/v1/models` |
| 同一个服务名换端点会**命中旧缓存** | 缓存键 = `引擎名 + {lang_in, lang_out, model} + 参数`，**`base_url` 不在键内**。从 llama-server 切到云端端点（或服务端换了模型）会拿到旧译文。**强制重译的唯一实测有效办法是删 `%TEMP%\cache\`** —— `--ignore-cache` 实测无效（2026-09-11 复跑产出未翻译的原文，机理未查明） |
| pdf2zh 硬编码 `temperature: 0` | OpenAI 系 translator 都固定 0（为了不打乱公式标记），而 MiniCPM 官方推荐 1.0 —— 这是既定取舍，**不要改源码** |

**质量兜底**：2B 明显翻不动时，换 `-s deepseek` / `-s silicon` / `-s google`（见下方服务表）。

## 支持的服务（1.9.11 实测 22 个）

`-s <服务名>` 或 `-s <服务名>:<模型>`（按第一个 `:` 切分）。

| 类别 | 服务名 | 必需环境变量 |
|------|--------|--------------|
| 免费 | `google`、`bing` | 无。中文目标语言用 `--lang-out zh-CN`。两者都有**限流**，失败就把并发 `-t` 降到 2 以下重试 |
| 本地 / 自建 | `openailiked` | `OPENAILIKED_BASE_URL`（必填，带 `/v1`）、`OPENAILIKED_MODEL`（或写在 `-s openailiked:<模型>`）、`OPENAILIKED_API_KEY`（可省） |
| 本地 / 自建 | `ollama` | ⛔ 本机 ollama **已于 2026-09-10 卸载**，此路不通；用 `openailiked` 接 llama-server |
| 本地 / 自建 | `xinference`、`anythingllm`、`dify` | 各自的 `*_BASE_URL` 等 |
| OpenAI 兼容 | `openai` | `OPENAI_API_KEY`（**必填**）、`OPENAI_BASE_URL`、`OPENAI_MODEL` |
| OpenAI 兼容 | `azure-openai` | `AZURE_OPENAI_API_KEY`、`AZURE_OPENAI_ENDPOINT` 等 |
| 国内厂商 | `deepseek`、`silicon`、`zhipu`、`modelscope`、`tencent`、`qwen-mt` | 各自的 `*_API_KEY` |
| 国外厂商 | `deepl`、`deeplx`、`azure`、`gemini`、`grok`、`groq`、`argos` | 各自的 `*_KEY` |

**接其它 OpenAI 兼容服务（含 MiMo）**：用 `openailiked` 或 `openai` 都行 —— 设 `OPENAILIKED_BASE_URL` 或 `OPENAI_BASE_URL` + 对应 key，`-s openailiked:<模型>`。

> ⚠️ 上游 `main` 分支文档里还有 `302ai`、`minimax` 两个服务 —— **1.9.11 里不存在**（源码实测），别照抄。

## 安装与版本前提

```bash
uv tool install pdf2zh        # 本机实际装法：隔离环境，不污染系统 Python
```

**关于 Python 版本（重要，别在系统 Python 上装）**：

- pdf2zh **1.8.0+ 要求 Python `<3.13`**；本机系统 Python 是 **3.14**，所以 `py -3 -m pip install pdf2zh` 会**静默退回 1.7.9**（该版本无 Python 约束）。
- uv 用的是自己下载的 **3.12.14**，因此装到的是 **1.9.11**。
- **1.9.11 不依赖 torch**（版面走 onnxruntime）。

### ⚠️ 启动前提：腾讯 SDK 必须钉版本

**症状**：装好后任何命令都直接崩，连 `--help` 都跑不起来 ——

```
ImportError: cannot import name 'TextTranslateRequest' from 'tencentcloud.tmt.v20180321.models'
```

**根因**：`tencentcloud-sdk-python-tmt` 新版**移除了 `TextTranslateRequest`**，而 pdf2zh 在 `translator.py` **模块顶层**硬导入它 —— 与你是否用腾讯翻译**无关**，纯粹是导入期就炸。

**修法**：

```bash
uv pip install --python "C:/Users/caill/AppData/Roaming/uv/tools/pdf2zh/Scripts/python.exe" \
  "tencentcloud-sdk-python-tmt<3.1.100"
# 实测落在 3.1.70，该类尚存 → pdf2zh v1.9.11 恢复正常
```

> ⚠️ `uv tool upgrade pdf2zh` 会把这个钉子冲掉，升级后需**重新钉一遍**。

## 上游现状与引擎选型

- **仓库已改名**：`Byaidu/PDFMathTranslate` → **`PDFMathTranslate/PDFMathTranslate`**（旧路径 301 重定向）。**未归档，仍在维护。**
- **2.0 主线已迁走**：新版是 `PDFMathTranslate/PDFMathTranslate-next`，PyPI 包名 **`pdf2zh-next`**（最新 2.9.0）。两者是**两套独立安装**。
- PyPI 上 `pdf2zh` 最新就是 **1.9.11**（1.9.12 已在仓库 main 但**未发布**）。

**新版差异对照**（本机**未安装**，仅供判断，未实测）：

| | pdf2zh（1.9.11，本机已装） | pdf2zh_next（2.9.0，未装） |
|---|---|---|
| 选服务 | `-s <服务名>[:模型]` | 无 `-s`；改成每个引擎一个 flag，如 `--openai` / `--openai-compatible` |
| 配置 | 环境变量 | `--config-file` + 默认 `~/.config/pdf2zh/config.v3.toml`；env 前缀 `PDF2ZH_` |
| 免费通道 | `google` / `bing` 可用 | **Bing 与 Google 已 deprecated**，改用 `SiliconFlowFree` 等 |
| 扩展 | 无插件机制；有 MCP server（`pdf2zh --mcp`） | 有 `CLITranslator`（`--clitranslator-command`）与 Python API |

需要时：`uv tool install pdf2zh-next`（Python 约束 `<3.14,>=3.10`）。

> ⚠️ **两个版本都没有 `--plugin` 机制**。老版想加服务只能改 `pdf2zh/translator.py` 源码 —— 这正是本技能**不再维护任何改源码补丁**的原因。

## 其它行为

- **输出**：`<名字>-mono.pdf`（纯译文）、`<名字>-dual.pdf`（双语对照）。
- **公式占位符**：pdf2zh 把公式替换成 `{{v0}} {{v1}}` 再翻译，译文必须原样保留这些标记，管道再回填成真实公式。
- **缓存**：`%TEMP%\cache\`。想强制重译，删该目录（`--ignore-cache` 实测无效，见上）。
- **多线程**：`-t`，并发调翻译服务。
- **命令会先打印一行 `not in git repo`** —— 探测当前目录是否 git 仓库，**无害**。
- **指定页**：`--pages 1-3`；**指定输出目录**：`-o out/`（**目录必须已存在**，1.9.11 不自动创建，实测 `FileNotFoundError`）。

## 排错

| 现象 | 处理 |
|------|------|
| `ImportError: cannot import name 'TextTranslateRequest'` | 腾讯 SDK 漂移，见上文「启动前提」，钉回 3.1.70 |
| `404` / 连接失败（本地端点） | `OPENAILIKED_BASE_URL` 末尾少了 `/v1` |
| `ValueError: The OPENAILIKED_BASE_URL is missing.` | 没设环境变量；`OPENAILIKED_MODEL` 同理，或改用 `-s openailiked:<模型>` |
| 译文和上次**一模一样** | 命中了缓存而换了端点 —— 缓存键不含 `base_url`。删 `%TEMP%\cache\` |
| 译文和原文一样 | 检查语言码（google 中文用 `zh-CN`）；网络/代理可达性 |
| `Empty translation result` | google 页面结构变化或网络问题，换 `-s openailiked` 等 |
| `Unsupported translation service` | 服务名拼错，或该服务不在 1.9.11 的 22 个里 |
| **本地翻译慢十倍但不报错** | 静默退回纯 CPU（CUDA 不匹配 / 显存没释放 / `-ngl` 没生效）。`llama-server.exe --list-devices` 必须看到 `CUDA0:`。详见 `local-ai` 技能 |

## 文件位置

| 内容 | 位置 |
|------|------|
| 命令 | `C:\Users\caill\.local\bin\pdf2zh.exe` |
| 工具环境 | `C:\Users\caill\AppData\Roaming\uv\tools\pdf2zh\`（`Lib\site-packages\pdf2zh\`） |
| 翻译缓存 | `%TEMP%\cache\` |
| 布局模型 | `~/.cache/huggingface/`（首次运行自动下载） |
| Zotero 插件说明 | 本技能 `references/zotero-plugin.md` |
