# pdf2zh 技能重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `skills/pdf2zh/SKILL.md` 从「1.7.9 时代的外部服务说明」重写为「本地 2B 直连为默认路径 + 1.9.11 实测服务表 + 上游订正 + Zotero 插件指引」，并清掉 515 行未复验的补丁脚本。

**Architecture:** 先跑真实验证拿到事实（Task 1），再据事实写文档（Task 2–3），最后清理与同步（Task 4–5）。**文档里的每一条事实要么是实测得出的，要么标注了来源和未实测 —— 禁止凭印象落笔。**

**Tech Stack:** pdf2zh 1.9.11（uv tool）、llama.cpp llama-server（CUDA b10883）、PyMuPDF（校验脚本）、Git Bash。

**Spec:** `docs/superpowers/specs/2026-09-11-pdf2zh-skill-overhaul-design.md`

## Global Constraints

- 目标技能目录：`C:\Users\caill\.claude\skills\pdf2zh\`；仓库根：`C:\Users\caill\.claude\skills\`（git，分支 `master`，**直接提交到 master**，与既有历史一致）。
- 引擎：**只主推 pdf2zh 1.9.11**。`pdf2zh_next` 仅写对照节，**不安装**、不主推。
- **不改 `pdf2zh` 源码**，不再维护任何补丁脚本。
- 本地模型：**MiniCPM5-2B-Q8_0**，`D:/models/gguf/minicpm5-2b/MiniCPM5-2B-Q8_0.gguf`，默认端口 **8080**。
- 本地端点必须走 **`openailiked`** 服务，**不是 `openai`**。
- `OPENAILIKED_BASE_URL` **必须以 `/v1` 结尾**。
- 不确定的事实**必须标注来源 + 「未实测」**，不得写成结论。
- **Bash 工具注意**：长 heredoc 命令易被分类器拦。凡超过 3 行的脚本，**先 Write 成文件再跑短命令**。
- 仓库里 `local-ai/README.md`、`local-ai/SKILL.md` 有他人未提交的改动，`.obsidian/` 未跟踪 —— **任何提交都只 `git add` 本任务自己的文件**，绝不 `git add -A`。

## File Structure

| 文件 | 动作 | 职责 |
|------|------|------|
| `docs/superpowers/plans/2026-09-11-pdf2zh-verification.md` | 创建 | Task 1 的实测台账（证据存档） |
| `skills/pdf2zh/SKILL.md` | 重写 | 技能主干：本地 2B 默认路径 + 服务表 + 引擎对照 + 排错 |
| `skills/pdf2zh/references/zotero-plugin.md` | 创建 | Zotero 插件可执行安装/配置节（通篇标未实测） |
| `skills/pdf2zh/agent_translator_patch.py` | 删除 | 515 行补丁脚本之一 |
| `skills/pdf2zh/test_agent_translator.py` | 删除 | 515 行补丁脚本之二 |
| `skills/README.md` | 修改 | 技能表 pdf2zh 行 + 环境依赖表 + 更新日志 |

---

## Task 1: 实测验证（V1–V6）并产出事实台账

**这是所有文档内容的事实来源。此任务不产出技能文件，只产出证据。**

**Files:**
- Create: `C:\Users\caill\.claude\skills\docs\superpowers\plans\2026-09-11-pdf2zh-verification.md`
- Create（临时，跑完可留可删）: `C:/Users/caill/AppData/Local/Temp/pdf2zh-v/check_formula.py`

**Interfaces:**
- Consumes: 无
- Produces: 事实台账中的 **V3 结论**（`FORMULA_OK` 或 `FORMULA_LOST`），Task 2 依赖它决定 SKILL.md 里本地 2B 要不要加限定语。

- [ ] **Step 1: 准备样本 PDF**

```bash
mkdir -p /c/Users/caill/AppData/Local/Temp/pdf2zh-v
cd /c/Users/caill/AppData/Local/Temp/pdf2zh-v
curl -sL -m 60 -o attention.pdf https://arxiv.org/pdf/1706.03762
ls -la attention.pdf
```

预期：文件存在且 **> 1MB**（`Attention Is All You Need`，15 页、双栏、含大量公式）。

若 arXiv 取不到，改用本机生成的替代样本（仍须含公式）：

```bash
py -3 -c "import reportlab; print('reportlab ok', reportlab.Version)"
```

并在台账中如实记录「样本非 arXiv，公式密度较低」。

- [ ] **Step 2: 启动本地 2B（V1）**

`start.sh` 内部 `exec llama-server`，是**前台阻塞**进程 —— 必须后台起：

```bash
"C:/Users/caill/.claude/skills/local-ai/scripts/start.sh" minicpm > /c/Users/caill/AppData/Local/Temp/pdf2zh-v/server.log 2>&1 &
sleep 12
curl -s -m 5 http://127.0.0.1:8080/health
```

预期输出：`{"status":"ok"}`

若 12 秒不够（首次加载），再等并重试一次。**仍失败则停止本任务，先排查 `local-ai`。**

- [ ] **Step 3: 确认没有静默退回 CPU**

```bash
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
```

预期：**≥ 5000**（2B 占 6–7GB）。若只有几百 MiB，说明掉到 CPU 了 —— 先跑 `stop.sh` 再重起，不要带着这个状态往下测（会得到错误的速度结论）。

- [ ] **Step 4: V2 —— 本地 2B 翻译**

```bash
cd /c/Users/caill/AppData/Local/Temp/pdf2zh-v
OPENAILIKED_BASE_URL=http://127.0.0.1:8080/v1 \
  "C:/Users/caill/.local/bin/pdf2zh.exe" attention.pdf \
    -s openailiked:minicpm5-2b \
    --lang-in en --lang-out zh-CN --pages 1-2 -t 4 -o out/
ls -la out/
```

预期：`out/attention-mono.pdf` 与 `out/attention-dual.pdf` **都存在且 > 0 字节**。

记录耗时（可用 `time` 前缀重跑，或用 `date` 前后夹）。

- [ ] **Step 5: V3 —— 检查公式是否被 2B 丢掉**

**用 Write 工具**（不是 heredoc —— 见 Global Constraints）创建 `C:/Users/caill/AppData/Local/Temp/pdf2zh-v/check_formula.py`：

```python
import re, sys
import pymupdf

PAT = re.compile(r"[√∑∫∈≤≥αβγθλμπσω∂∇±×÷≈≠]")

def syms(path, maxpages=None):
    doc = pymupdf.open(path)
    n = doc.page_count if maxpages is None else min(maxpages, doc.page_count)
    text = "".join(doc[i].get_text() for i in range(n))
    return set(PAT.findall(text)), n

src_s, sn = syms(sys.argv[1], 2)
out_s, on = syms(sys.argv[2])
print(f"原文(前2页,{sn}p) 符号 {len(src_s)} 种: {''.join(sorted(src_s))}")
print(f"译文({on}p) 符号 {len(out_s)} 种: {''.join(sorted(out_s))}")
missing = src_s - out_s
print(f"缺失: {''.join(sorted(missing)) if missing else '（无）'}")
print("VERDICT:", "FORMULA_LOST" if len(missing) >= max(2, len(src_s) // 2) else "FORMULA_OK")
```

然后跑：

```bash
py -3 /c/Users/caill/AppData/Local/Temp/pdf2zh-v/check_formula.py \
  /c/Users/caill/AppData/Local/Temp/pdf2zh-v/attention.pdf \
  /c/Users/caill/AppData/Local/Temp/pdf2zh-v/out/attention-mono.pdf
```

**判读：**
- `VERDICT: FORMULA_OK` → 2B 保住了公式 → SKILL.md 用「默认路径」写法（Task 2 Step 3 的分支 A）。
- `VERDICT: FORMULA_LOST` → 2B 系统性丢公式 → SKILL.md **必须**加「公式密集的论文慎用」限定语（分支 B）。
- 若 `原文符号 0 种`：样本本身没公式，**本项无结论**，台账如实记「样本无公式，V3 未得出结论」，并在 Task 2 采用分支 B 的保守写法。

- [ ] **Step 6: V4 —— 确认 `-t 4` 真并发**

```bash
grep -c "slot" /c/Users/caill/AppData/Local/Temp/pdf2zh-v/server.log
tail -30 /c/Users/caill/AppData/Local/Temp/pdf2zh-v/server.log
```

判读：日志里出现**多个不同 slot id 的请求**（或启动横幅里有 `n_slots = 4`）→ 记 `CONCURRENCY_OK`；若全程只有一条槽 → 记 `CONCURRENCY_SERIAL`，SKILL.md 里就不写「`-t 4` 对齐 n_slots」。

- [ ] **Step 7: V5 —— 验证「换 base_url 仍命中旧缓存」**

把端点改成一个**必然不可达**的端口，重跑同一条命令：

```bash
cd /c/Users/caill/AppData/Local/Temp/pdf2zh-v
OPENAILIKED_BASE_URL=http://127.0.0.1:9/v1 \
  "C:/Users/caill/.local/bin/pdf2zh.exe" attention.pdf \
    -s openailiked:minicpm5-2b \
    --lang-in en --lang-out zh-CN --pages 1-2 -t 4 -o out2/
ls -la out2/
```

判读：
- **产出成功且译文与 `out/` 一致** → 命中缓存，证实 spec §5.2-⑤ 的坑（`base_url` 不入缓存键），记 `CACHE_BASEURL_HIT`。
- **报连接错误 / 空译文** → 未命中，记 `CACHE_BASEURL_MISS`，SKILL.md 里**不写**这条坑。

再补验证「换引擎不会串味」：

```bash
rm -rf /c/Users/caill/AppData/Local/Temp/pdf2zh-v/out3
"C:/Users/caill/.local/bin/pdf2zh.exe" attention.pdf \
  -s google --lang-in en --lang-out zh-CN --pages 1 -o out3/
```

预期：不会复用 2B 的译文（引擎名在缓存键里）。记 `CACHE_ENGINE_ISOLATED` 或反例。

- [ ] **Step 8: V6 —— 释放显存**

```bash
"C:/Users/caill/.claude/skills/local-ai/scripts/stop.sh"
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
```

预期：脚本打印「已退出，显存 X → Y MiB」，且 Y 明显小于 X。

- [ ] **Step 9: 写台账并提交**

新建 `C:\Users\caill\.claude\skills\docs\superpowers\plans\2026-09-11-pdf2zh-verification.md`，**逐项照抄实际输出**（不要写「正常」这种无信息量的词），格式：

```markdown
# pdf2zh 重构 —— 实测台账（2026-09-11）

| 项 | 结论 | 实际证据（原样粘贴） |
|----|------|---------------------|
| V1 health | ok/失败 | `{"status":"ok"}` |
| V2 本地2B翻译 | 产物路径 + 耗时 | `out/attention-mono.pdf` 大小 X KB，耗时 Ys |
| V3 公式 | FORMULA_OK / FORMULA_LOST / 无结论 | 原文 N 种符号，译文 M 种，缺失「…」 |
| V4 并发 | CONCURRENCY_OK / SERIAL | 日志片段 |
| V5 缓存 | CACHE_BASEURL_HIT/MISS、CACHE_ENGINE_ISOLATED | 观察描述 |
| V6 释放 | 显存 X → Y MiB | nvidia-smi 数字 |

## 附：未取到 / 存疑的项
（如实列出）
```

```bash
cd "C:/Users/caill/.claude/skills"
git add docs/superpowers/plans/2026-09-11-pdf2zh-verification.md
git commit -m "skills: pdf2zh 重构实测台账（V1–V6）"
```

---

## Task 2: 重写 `skills/pdf2zh/SKILL.md`

**Files:**
- Modify（整文件替换）: `C:\Users\caill\.claude\skills\pdf2zh\SKILL.md`
- Test: Task 1 产出的台账 `docs/superpowers/plans/2026-09-11-pdf2zh-verification.md`

**Interfaces:**
- Consumes: Task 1 的 `V3`（`FORMULA_OK` / `FORMULA_LOST`）、`V4`（`CONCURRENCY_OK` / `SERIAL`）、V5 结论
- Produces: 引用文件 `references/zotero-plugin.md`（Task 3 创建）；技能不再提及补丁脚本（Task 4 删除）

- [ ] **Step 1: 打开台账，确认三个开关的值**

读 `docs/superpowers/plans/2026-09-11-pdf2zh-verification.md`，确定：
- `V3_VALUE` = `FORMULA_OK` 或 `FORMULA_LOST`
- `V4_VALUE` = `CONCURRENCY_OK` 或 `CONCURRENCY_SERIAL`
- `V5_VALUE` = `CACHE_BASEURL_HIT` 或 `CACHE_BASEURL_MISS`

- [ ] **Step 2: 整文件写入下面的骨架**

用 Write 工具整体覆盖 `C:\Users\caill\.claude\skills\pdf2zh\SKILL.md`：

````markdown
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
# ① 起 2B llama-server
"C:/Users/caill/.claude/skills/local-ai/scripts/start.sh" minicpm &
curl -s http://127.0.0.1:8080/health          # {"status":"ok"}

# ② 翻译
OPENAILIKED_BASE_URL=http://127.0.0.1:8080/v1 \
  pdf2zh paper.pdf -s openailiked:minicpm5-2b \
    --lang-in en --lang-out zh-CN -t 4 -o out/

# ③ 用完释放显存（2B 占 6–7GB）
"C:/Users/caill/.claude/skills/local-ai/scripts/stop.sh"
```

产出 `out/<名字>-mono.pdf`（纯译文）与 `out/<名字>-dual.pdf`（双语对照）。

**为什么是 `openailiked` 而不是 `openai`**：`openai` 服务要求 `OPENAI_API_KEY` 非空，否则 OpenAI SDK 构造直接抛错；`openailiked` 的 key 缺省**硬编码回落字符串 `"openailiked"`**，本地端点不用编 key。这也是上游对「本地自建 LLM」的官方答复（issue #792：llama-server 用 openai like 接入）。

**四条必踩的坑**：

| 坑 | 说明 |
|----|------|
| `BASE_URL` 末尾必须有 `/v1` | 少了直接 404（上游 `docs/ADVANCED.md` 原文要求） |
| `-s openailiked:<名字>` 里的名字是**标签** | llama-server **忽略请求体里的 `model` 字段**：写 9B 实际仍跑 2B，**且不报错**。核对实际模型看 `curl -s http://127.0.0.1:8080/v1/models` |
| 同一个服务名换端点会**命中旧缓存** | 缓存键 = `引擎名 + {lang_in, lang_out, model} + 参数`，**`base_url` 不在键内**。从 llama-server 切到云端端点（或服务端换了模型）会拿到旧译文。强制重译：删 `%TEMP%\cache\` 或加 `--ignore-cache` |
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
- **缓存**：`%TEMP%\cache\`。想强制重译删该目录，或加 `--ignore-cache`。
- **多线程**：`-t`，并发调翻译服务。
- **命令会先打印一行 `not in git repo`** —— 探测当前目录是否 git 仓库，**无害**。
- **指定页**：`--pages 1-3`；**指定输出目录**：`-o out/`。

## 排错

| 现象 | 处理 |
|------|------|
| `ImportError: cannot import name 'TextTranslateRequest'` | 腾讯 SDK 漂移，见上文「启动前提」，钉回 3.1.70 |
| `404` / 连接失败（本地端点） | `OPENAILIKED_BASE_URL` 末尾少了 `/v1` |
| `ValueError: The OPENAILIKED_BASE_URL is missing.` | 没设环境变量；`OPENAILIKED_MODEL` 同理，或改用 `-s openailiked:<模型>` |
| 译文和上次**一模一样** | 命中了缓存而换了端点 —— 缓存键不含 `base_url`。删 `%TEMP%\cache\` 或 `--ignore-cache` |
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
````

- [ ] **Step 3: 按台账替换两处开关**

**3a. 公式（依 `V3_VALUE`）** —— 在「默认路径」小节的**结尾**追加一行：

- 若 `V3_VALUE = FORMULA_OK`，追加：
  > ✅ 实测（2026-09-11）：2B 翻译后公式符号保留完好。

- 若 `V3_VALUE = FORMULA_LOST`，追加：
  > ⚠️ 实测（2026-09-11）：**2B 会丢公式占位符**，公式密集的论文（数学/物理论文）建议改用 `-s deepseek` 等云端服务；正文为主的文档可放心用本地。

- 若 V3 无结论（样本没公式），追加：
  > ⚠️ **公式保留情况未实测**：本地 2B 对含大量公式的论文效果未经验证，公式密集时建议改用云端服务。

**3b. 并发（依 `V4_VALUE`）** —— 在「四条必踩的坑」表**之后**：

- 若 `V4_VALUE = CONCURRENCY_OK`，追加：
  > **并发**：`-t 4` 对齐 2B 的 `n_slots=4`，实测能真正并发。

- 若 `V4_VALUE = CONCURRENCY_SERIAL`，追加：
  > **并发**：实测 `-t 4` 未见并行，本地场景按 `-t 1` 用即可。

**3c. 缓存（依 `V5_VALUE`）** —— 「四条必踩的坑」表里的「同一个服务名换端点会**命中旧缓存**」一行：

- 若 `V5_VALUE = CACHE_BASEURL_HIT`，**保留**该行。
- 若 `V5_VALUE = CACHE_BASEURL_MISS`，**删掉**该行，改成三行的表并把表格标题「四条必踩的坑」改为「三条必踩的坑」。

- [ ] **Step 4: 校验 frontmatter 与链接**

```bash
cd "C:/Users/caill/.claude/skills/pdf2zh"
wc -l SKILL.md
head -6 SKILL.md
grep -n "agent_translator_patch\|AgentTranslator\|-s agent" SKILL.md
grep -n "references/zotero-plugin.md" SKILL.md
```

预期：
- `wc -l` **≤ 150**（spec §4 的目标篇幅）。超了就压缩服务表的分组说明。
- `head -6` 能看出合法 YAML frontmatter（`name:` + `description:` 各一行）。
- 第 2 条 grep **无输出**（正文里已无补丁脚本的任何引用）。
- 第 3 条 grep **有输出**（指路链接在）。

- [ ] **Step 5: 提交**

```bash
cd "C:/Users/caill/.claude/skills"
git add pdf2zh/SKILL.md
git commit -m "skills: pdf2zh 重写 —— 默认路径改为本地 2B 直连，订正上游事实

- 服务表由 1.7.9 时代的 6 个改为 1.9.11 实测的 22 个，并指出上游
  main 文档里的 302ai/minimax 在 1.9.11 中并不存在
- 新增默认路径：openailiked + llama-server 接本地 MiniCPM5-2B
  （0 token、不出本机），含 /v1 后缀、模型名仅为标签、缓存键不含
  base_url、temperature 硬编码为 0 四条坑
- 订正仓库改名（Byaidu → PDFMathTranslate）与 2.0 主线迁至 -next，
  新增新旧引擎对照表
- 删除全部改源码补丁的引用（上游无插件机制）

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: 新增 `skills/pdf2zh/references/zotero-plugin.md`

**Files:**
- Create: `C:\Users\caill\.claude\skills\pdf2zh\references\zotero-plugin.md`

**Interfaces:**
- Consumes: 无（内容全部来自上游 README，来源 URL 已列在 spec §3.3）
- Produces: Task 2 生成的 SKILL.md 中 `references/zotero-plugin.md` 链接的目标文件

- [ ] **Step 1: 建目录并写文件**

```bash
mkdir -p "C:/Users/caill/.claude/skills/pdf2zh/references"
```

用 Write 工具创建 `C:\Users\caill\.claude\skills\pdf2zh\references\zotero-plugin.md`：

````markdown
# Zotero PDF2zh 插件

> ⚠️ **本节全部是上游口径，本机未实测。**
> 本机**没有**安装 Zotero，也没有装本插件的服务端。以下内容摘自
> `https://github.com/guaguastandup/zotero-pdf2zh`（v4.1.7，2026-08-27 快照）
> 与官方文档站 `https://zotero-pdf2zh.github.io`。**装之前请以官方文档为准。**
> 官方文档更新很快，本文件可能已过时。

## 是什么

在 Zotero 里直接调用 **pdf2zh** 或 **pdf2zh_next** 翻译 PDF 附件，保留公式与排版，并提供双语对照、裁剪阅读、批量翻译。

仓库：`guaguastandup/zotero-pdf2zh`（v4.1.7，6.2k star，支持 Zotero 7/8/9/10）。

**与本技能 CLI 部分的关系**：同一个翻译引擎的两个入口。插件的服务端是**另一套独立安装**，和本机的 `C:\Users\caill\.local\bin\pdf2zh.exe` 互不影响、互不依赖。

## 安装（上游步骤）

1. **服务端**：克隆/下载仓库后启动，默认端口 **8890**：

   ```bash
   # 上游 README 的启动方式（Windows）
   python server.py --port 8890 --config config.json
   ```

2. **插件**：从 Releases 下载 `.xpi`，在 Zotero 里「工具 → 插件 → 从文件安装」。

3. 在插件设置页把 **Python Server IP** 指向服务端，点旁边的「检查连接」验证连通性。

> 上游 README 明确提示：**插件和服务端要同时更新**，版本不匹配会出问题。

## 配置翻译服务（关键：两步，缺一不可）

1. **「LLM API 配置管理」** 区域点「新增」，填服务配置。同一服务可加多个配置，但**只能激活其中一个**。
2. 在页面顶部的 **「翻译服务」下拉菜单里选中**你要用的服务。

> ⚠️ 上游原话：**仅添加 API 配置不会生效，必须完成第二步选择服务。**

反过来，**免费服务**（如 `bing` / `google` / `siliconflowfree`）不需要自己配 API key。

## 接本地 2B 模型

插件里的 **`openaliked`** 就是「OpenAI 兼容端点」选项（注意拼写：插件 UI 写 `openaliked`，**少一个 `i`**；CLI 的服务名是 `openailiked`）。

在本机已有的 llama-server（`local-ai` 技能启动，默认 `127.0.0.1:8080`）基础上填：

| 字段 | 值 |
|------|-----|
| URL | `http://127.0.0.1:8080/v1` |
| API Key | 随意填（本地端点不校验） |
| Model | 任意标签，如 `minicpm5-2b` |

> ⚠️ 同 CLI 的坑：llama-server **忽略请求体里的 `model` 字段**，这个 Model 名只是标签；URL **必须带 `/v1`**。

## 插件自带的服务名（UI 口径）

| 插件 UI 服务名 | 说明 |
|----------------|------|
| `siliconflowfree` | 免费，**仅支持 pdf2zh_next 引擎**；限流，可能漏译 |
| `bing` / `google` | 免费机器翻译；**有限流**，失败就把并发数降到 2 及以下重试 |
| `openaliked` | **任意 OpenAI 兼容端点**（含本地 llama.cpp / vLLM / LM Studio） |
| `silicon` | 硅基流动；URL 填 `https://api.siliconflow.cn/v1`（**删掉后缀** `completions` 之类） |
| `zhipu` | 智谱；免费额度并发建议 ≤ 6 |
| `aliyunDashScope` | 通义；用「LLM API 配置管理」里的默认模型选项 |
| `deepseek` | 推荐 `deepseek-v4-flash`；默认关闭思考 |

## 两个引擎的配置差异

| | pdf2zh（老） | pdf2zh_next（新） |
|---|---|---|
| 配置文件 | `config.json` | `config.toml` |
| 服务数 | 多 | 多，且独有 `siliconflowfree` |

## 排错（上游口径）

| 现象 | 处理 |
|------|------|
| 检查连接失败 | 服务端没起 / 端口不对 / 防火墙 |
| 翻译失败或漏译 | 先看 API 是否超限（终端报错或服务商后台）；免费服务（bing/google）多为限流，切等更稳定的服务 |
| 段落缺失 | 翻译失败时程序会用原文替代。先排查 API 是否正常；pdf2zh_next 可在 LLM 配置的**额外参数**里开对应服务的 `*_enable_json_mode`（如 `openai_enable_json_mode`，**默认关闭**） |
| 生成文件过大 / 某次失败 | 尝试开启「兼容模式」（非必要不开） |

> 额外参数名需与 config 文件字段一致；v4.1.7 起可在「LLM API 配置管理」点「添加参数」从下拉选择。
````

- [ ] **Step 2: 校验文件存在且未实测声明在最前**

```bash
cd "C:/Users/caill/.claude/skills/pdf2zh"
wc -l references/zotero-plugin.md
head -8 references/zotero-plugin.md
grep -c "未实测" references/zotero-plugin.md
```

预期：行数 > 80；`head` 第 3 行起能看到「本节全部是上游口径，本机未实测」的警告块；`未实测` 出现 ≥ 1 次。

- [ ] **Step 3: 提交**

```bash
cd "C:/Users/caill/.claude/skills"
git add pdf2zh/references/zotero-plugin.md
git commit -m "skills: pdf2zh 新增 Zotero 插件说明（通篇标注本机未实测）

来源为 guaguastandup/zotero-pdf2zh v4.1.7 README 与官方文档站。
记录插件 UI 的 openaliked 与 CLI 的 openailiked 拼写差异、两步配置
（只加 API 配置不选服务不生效）、以及用本地 llama-server 的做法。

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: 删除两个补丁脚本

**Files:**
- Delete: `C:\Users\caill\.claude\skills\pdf2zh\agent_translator_patch.py`
- Delete: `C:\Users\caill\.claude\skills\pdf2zh\test_agent_translator.py`

**Interfaces:**
- Consumes: Task 2 已确认 SKILL.md 正文不再引用它们（Task 2 Step 4 的第 2 条 grep 无输出）
- Produces: 无

- [ ] **Step 1: 先确认没有任何地方还引用它们**

```bash
cd "C:/Users/caill/.claude/skills"
grep -rn "agent_translator_patch\|AgentTranslator\|-s agent" --include="*.md" --include="*.py" --include="*.json" . | grep -v "^./docs/superpowers/"
```

预期：**无输出**。若有输出，先修掉引用再删。

- [ ] **Step 2: 删除**

```bash
cd "C:/Users/caill/.claude/skills"
git rm pdf2zh/agent_translator_patch.py pdf2zh/test_agent_translator.py
```

- [ ] **Step 3: 确认目录只剩该留的**

```bash
cd "C:/Users/caill/.claude/skills/pdf2zh"
find . -type f | sort
```

预期（恰好 2 个文件）：

```
./SKILL.md
./references/zotero-plugin.md
```

- [ ] **Step 4: 提交**

```bash
cd "C:/Users/caill/.claude/skills"
git commit -m "skills: pdf2zh 删除 agent 两趟桥补丁脚本

agent_translator_patch.py（393 行）与 test_agent_translator.py（122 行）
为 pdf2zh 1.7.9 编写，本机从未打上，且未在 1.9.11 上复验过。
其目标（不烧 token 的本地翻译）已由本地 2B 直连覆盖，且更简单。
另：上游两版均无插件机制，该补丁靠改源码，随上游漂移即失效。

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: 同步 `skills/README.md`

**Files:**
- Modify: `C:\Users\caill\.claude\skills\README.md`（技能表 `pdf2zh` 行；环境依赖表 `pdf2zh.exe` 行；文末更新日志追加一条）

**Interfaces:**
- Consumes: Task 2 / 3 的实际产物
- Produces: 无

- [ ] **Step 1: 定位要改的三处**

```bash
cd "C:/Users/caill/.claude/skills"
grep -n "pdf2zh" README.md | head -20
```

预期能看到至少：技能表一行（含「23+ 引擎」字样）、环境依赖表一行（`pdf2zh.exe`）、文末更新日志末尾。**先看清行号再改**，不要凭记忆。

- [ ] **Step 2: 改技能表那一行**

把 `23+ 引擎` 改为实测的 **22 个**，并补上默认路径。改完应形如：

```markdown
| **pdf2zh**            | PDF 翻译、保留公式排版 | **默认走本地 2B**（MiniCPM5-2B + llama-server，0 token、不出本机）——`-s openailiked:<模型>`；云端服务为质量兜底。v1.9.11（uv tool 隔离安装）；⚠️ 需把 `tencentcloud-sdk-python-tmt` 钉在 3.1.70，否则启动即 ImportError。Zotero 插件见 `references/zotero-plugin.md` |
```

（保持表格其余列的格式与相邻行一致；若相邻行的列数不同，以**相邻行**的列数为准。）

- [ ] **Step 3: 改环境依赖表那一行**

把该行的描述改为反映「默认走本地 2B」，与 Step 2 口径一致；版本号 1.9.11 保持不变。

- [ ] **Step 4: 文末追加更新日志**

在更新日志**最前面**（与既有「最新在上」的顺序一致；Step 1 时确认方向）追加：

```markdown
- **2026/09/11** **pdf2zh 技能重构**：① 默认路径改为**本地 2B 直连** —— `openailiked` + llama-server（`local-ai` 技能）接 MiniCPM5-2B，0 token、不出本机，含「BASE_URL 必须带 `/v1`」「服务名后的模型名只是标签（llama-server 忽略请求里的 model 字段）」「缓存键不含 `base_url`，换端点会命中旧译文」「pdf2zh 硬编码 `temperature: 0` 与 MiniCPM 推荐值 1.0 冲突」四条实操坑；② **服务表由 1.7.9 时代的 6 个订正为 1.9.11 源码实测的 22 个**，并指出上游 main 文档里的 `302ai`/`minimax` 在 1.9.11 中不存在；③ **订正上游事实**：`Byaidu/PDFMathTranslate` 已改名 `PDFMathTranslate/PDFMathTranslate`（旧路径 301，未归档仍在维护），2.0 主线迁至 `PDFMathTranslate-next`（`pdf2zh-next` 2.9.0，无 `-s`、改 `config.toml` + `PDF2ZH_` 前缀、Bing/Google 已 deprecated），本机仍只装老版 1.9.11；④ **新增 `references/zotero-plugin.md`**（Zotero 插件 `guaguastandup/zotero-pdf2zh`，本机未装 Zotero，通篇标注上游口径未实测）；⑤ **删除 `agent_translator_patch.py`（393 行）与 `test_agent_translator.py`（122 行）** —— 为 1.7.9 写、本机从未打上、未复验，其目标已由本地 2B 直连覆盖，且上游两版均无插件机制。设计见 `docs/superpowers/specs/2026-09-11-pdf2zh-skill-overhaul-design.md`
```

- [ ] **Step 5: 更新文末的「最后更新」日期**

把 `*最后更新：…*` 一行改为 `*最后更新：2026-09-11（pdf2zh 默认路径改为本地 2B 直连；服务表实测订正；新增 Zotero 插件说明；删除失效补丁脚本）*`。

- [ ] **Step 6: 校验没留下「23+」**

```bash
cd "C:/Users/caill/.claude/skills"
grep -n "23+ 引擎\|未安装" README.md | grep -i "pdf2zh"
```

预期：**无输出**（旧口径已清干净）。

- [ ] **Step 7: 提交**

```bash
cd "C:/Users/caill/.claude/skills"
git add README.md
git commit -m "skills: README 同步 pdf2zh 重构（默认本地 2B、服务数订正、Zotero 节）

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: 收尾复核

**Files:**
- Test: `skills/pdf2zh/SKILL.md`、`skills/pdf2zh/references/zotero-plugin.md`、`skills/README.md`

**Interfaces:**
- Consumes: Task 1–5 的全部产物
- Produces: 无

- [ ] **Step 1: 复核台账里的每条结论都在文档里有落点**

逐行读 `docs/superpowers/plans/2026-09-11-pdf2zh-verification.md`，对每一条 `FORMULA_*` / `CONCURRENCY_*` / `CACHE_*`，在 SKILL.md 里找到对应句子。**任一条找不到 → 回去补。**

- [ ] **Step 2: 复核没有把「未实测」冒充成实测**

```bash
cd "C:/Users/caill/.claude/skills/pdf2zh"
grep -n "实测\|未实测\|上游口径\|未复验" SKILL.md references/zotero-plugin.md
```

判读：
- Zotero 文件里「未实测」声明**必须在**；
- SKILL.md 里凡出现「实测」的句子，都必须能对上台账里的证据；对不上的改成「未实测」或删掉。

- [ ] **Step 3: 端到端复跑一次默认路径**

按 SKILL.md「默认路径」小节**原文照抄**命令跑一遍（不许脑补修正）：

```bash
"C:/Users/caill/.claude/skills/local-ai/scripts/start.sh" minicpm > /c/Users/caill/AppData/Local/Temp/pdf2zh-v/server2.log 2>&1 &
sleep 12
cd /c/Users/caill/AppData/Local/Temp/pdf2zh-v
OPENAILIKED_BASE_URL=http://127.0.0.1:8080/v1 \
  "C:/Users/caill/.local/bin/pdf2zh.exe" attention.pdf \
    -s openailiked:minicpm5-2b \
    --lang-in en --lang-out zh-CN --pages 1 -t 4 --ignore-cache -o out4/
ls -la out4/
```

预期：`out4/attention-mono.pdf` 与 `out4/attention-dual.pdf` 都存在。
**若照抄命令跑不通，说明文档写错了 —— 修文档，不是修命令。**

- [ ] **Step 4: 释放显存**

```bash
"C:/Users/caill/.claude/skills/local-ai/scripts/stop.sh"
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
```

预期：显存回落，`llama-server` 不再驻留。

- [ ] **Step 5: 确认工作区只剩非本任务的改动**

```bash
cd "C:/Users/caill/.claude/skills"
git status --short
git log --oneline -6
```

预期：`git status` 只剩 `local-ai/README.md`、`local-ai/SKILL.md`（他人改动）与 `?? .obsidian/` —— **本任务的改动应已全部提交**。若还有未提交的本任务文件，补一次提交。
