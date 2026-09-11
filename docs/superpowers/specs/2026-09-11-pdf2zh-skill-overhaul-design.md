# pdf2zh 技能重构设计

**日期**：2026-09-11
**状态**：待用户审阅
**影响范围**：`skills/pdf2zh/`（SKILL.md 重写、新增 references、删除两个脚本）、`skills/README.md`（条目与更新日志）

---

## 1. 背景与目标

`skills/pdf2zh/SKILL.md` 通篇按 **1.7.9** 写成，2026-09-10 本机装成 **1.9.11** 后只做了零星标注（多处仍留着「未复验」的免责话），且：

- 服务表只列 6 个，与 1.9.11 实际的 22 个严重不符；
- 指向的仓库 `Byaidu/PDFMathTranslate` **已改名**（旧路径 301 重定向）；
- 完全没提 2.0 主线已迁到 `PDFMathTranslate-next`；
- 对「接本地自建 LLM」给的做法（`-s openai:<模型>`）不是官方推荐路径；
- 目录里挂着 515 行 `agent_translator_patch.py` + 测试，为 1.7.9 写、本机未打、未复验。

**目标**：

1. 逐条核对技能与上游事实，订正失实处；
2. 把**本地 2B 模型直连**写成一等公民（默认路径），落实「翻译服务可以 call local AI 的 2B 模型」；
3. 补一节 **Zotero 插件**（`guaguastandup/zotero-pdf2zh`）的可执行安装/配置说明；
4. 清掉已死且误导的补丁脚本。

---

## 2. 决策记录

| # | 决策 | 选择 | 理由 |
|---|------|------|------|
| D1 | 对齐目标 | **CLI 上游 + Zotero 插件，两个都要** | 用户明确要求 |
| D2 | Zotero 节深度 | **写成可执行的安装/配置节**（非仅事实摘要） | 用户明确要求。本机未装 Zotero，全部逐条标注「上游口径，未实测」 |
| D3 | 现有 `agent` 两趟桥 | **删除** `agent_translator_patch.py` + `test_agent_translator.py` | 本地 2B 直连已覆盖其目标（不烧 token 的本地翻译）且更简单；上游两版**均无插件机制**，它靠改源码，随上游漂移即失效 |
| D4 | 主推引擎 | **pdf2zh 1.9.11（本机已装）**；`pdf2zh_next` 只写一节对照 | 已装可实测；本地 2B 走 `openailiked` 有上游成功先例；2B 配 next 的 JSON mode 把握不足 |
| D5 | 技能结构 | **单技能 + `references/` 渐进披露**（方案 A） | SKILL.md 每次触发都进上下文，须保持精简；Zotero 节长且冷门，按需读取 |
| D6 | 本地路径位置 | **放在 SKILL.md 最前**（默认路径） | 用户未反对，按草案执行 |

---

## 3. 事实基线

> 标注【实测】的条目为本机可复验；标注【上游】的来自仓库源码/文档/issue，附来源。

### 3.1 本机实测

- 【实测】`pdf2zh` 1.9.11，uv tool 装：可执行 `C:\Users\caill\.local\bin\pdf2zh.exe`，环境 `C:\Users\caill\AppData\Roaming\uv\tools\pdf2zh\`，包在 `Lib\site-packages\pdf2zh\`。
- 【实测】`Lib\site-packages\pdf2zh\translator.py`（1049 行）中 translator 类的 `name` 属性共 **22 个**：
  `google`、`bing`、`deepl`、`deeplx`、`ollama`、`xinference`、`openai`、`azure-openai`、`modelscope`、`zhipu`、`silicon`、`gemini`、`azure`、`tencent`、`anythingllm`、`dify`、`argos`、`grok`、`groq`、`deepseek`、`openailiked`、`qwen-mt`。
  （另有基类 `base`，不算服务。上游 `main` 文档提到的 `302ai` / `minimax` **在 1.9.11 中不存在**。）
- 【实测】`openailiked` 的环境变量（`translator.py:940`）：

  | 变量 | 必需 | 缺省行为 |
  |------|------|----------|
  | `OPENAILIKED_BASE_URL` | **是** | 缺失直接 `ValueError` |
  | `OPENAILIKED_MODEL` | 是* | 缺失且未用 `-s openailiked:<模型>` 时 `ValueError` |
  | `OPENAILIKED_API_KEY` | 否 | **硬编码回落字符串 `"openailiked"`** → 本地端点无需伪造 key |

- 【实测】`openai` 的环境变量（`translator.py:401`）：`OPENAI_BASE_URL`（默认 `https://api.openai.com/v1`）、`OPENAI_API_KEY`（默认 `None`，**为 None 时 OpenAI SDK 构造会抛错**）、`OPENAI_MODEL`（默认 `gpt-4o-mini`）。
- 【实测】缓存键由 `BaseTranslator.__init__` 构造（`translator.py:54`）：
  `TranslationCache(self.name, {"lang_in", "lang_out", "model"})`，各 translator 再 `add_cache_impact_parameters` 追加（如 `openai`/`openailiked` 追加 `temperature`、`prompt`、`think_filter_regex`）。
  → **引擎名在键里，`base_url` 不在。**
- 【实测】`agent_translator_patch.py`（393 行）、`test_agent_translator.py`（122 行）；在 `site-packages\pdf2zh\` 中搜不到补丁标记 → **本机未打补丁**。
- 【实测】本机 **未安装 Zotero**：`C:\Program Files\Zotero`、`C:\Users\caill\Zotero`、`C:\Users\caill\AppData\Roaming\Zotero` 均不存在；`uv tool list` 下只有 `graphifyy`、`pdf2zh`。
- 【实测】`local-ai` 提供 `scripts/start.sh`（用法 `./start.sh [minicpm|9b|vl4|vl8|asr] [port]`，默认 `minicpm`=2B，端口默认 8080，**幂等**：已是目标模型则复用）与 `scripts/stop.sh`。2B 模型为 `D:/models/gguf/minicpm5-2b/MiniCPM5-2B-Q8_0.gguf`，128K ctx、`n_slots=4`。

### 3.2 上游（pdf2zh / PDFMathTranslate）

- 【上游】`Byaidu/PDFMathTranslate` **已改名为 `PDFMathTranslate/PDFMathTranslate`**（HTTP 301 → `repositories/853189791`）。`archived: false`，`pushed_at: 2026-09-11`，star 36,853。**仍在维护，未归档。**
- 【上游】README 明示：`2.0 Moved to a new repository under the organization: PDFMathTranslate/PDFMathTranslate-next`。
- 【上游】PyPI：`pdf2zh` 最新 **1.9.11**（2025-07-11），`requires_python = ">=3.10,<3.13"`；`pdf2zh-next` 最新 **2.9.0**（2026-05-15）。仓库 main 的 `pyproject.toml` 已是 `1.9.12` 但**未发布到 PyPI**。
- 【上游】**本地自建 LLM 的官方答复**：issue #792（llama-server），维护者 awwaawwa 回复「请用 openai like 接入」，提问者实测
  `export OPENAILIKED_BASE_URL=http://127.0.0.1:8080/v1` + `-s openailiked:Qwen2.5-7B-Instruct-Q8_0` 成功。
  issue #428（vLLM）同结论；新版 issue #247（LM Studio）维护者答「It is recommended to use the OpenAICompatible directly.」
- 【上游】`docs/ADVANCED.md`：**BASE_URL 必须以 `/v1` 结尾，否则 404**。
- 【上游】老版另有 **MCP server**（`pdf2zh --mcp`）。
- 【上游】两版**均无 `--plugin` 机制**。老版加服务只能改 `pdf2zh/translator.py` 源码；新版有 `CLITranslator`（`--clitranslator-command`）与 Python API 两条官方扩展路径。

### 3.3 上游（zotero-pdf2zh 插件）

- 【上游】`guaguastandup/zotero-pdf2zh`，**v4.1.7**，star 6,244，`main` 分支，`pushed_at: 2026-08-27`。
- 【上游】同时支持两个引擎：`pdf2zh`（老）与 `pdf2zh_next`（新）。
- 【上游】服务端启动带 `--port`（默认 **8890**）；老引擎配置 `config.json`，新引擎 `config.toml`。
- 【上游】插件侧配置两步：① 「LLM API 配置管理」新增配置；② 顶部「翻译服务」下拉**必须选中**，否则不生效。
- 【上游】插件自带的翻译服务名（UI 口径）：`siliconflowfree`（免费、**仅 pdf2zh_next**）、`bing`/`google`（免费、限流）、`openaliked`（OpenAI 兼容）、`silicon`、`zhipu`、`aliyunDashScope`、`deepseek`。
  注意拼写差异：**插件 UI 写 `openaliked`，CLI 服务名是 `openailiked`**。
- 【上游】OpenAI 兼容选项目支持填任意兼容端点；`deepseek` 推荐 `deepseek-v4-flash`，默认关闭思考。

---

## 4. 目标结构

```
skills/pdf2zh/
├── SKILL.md                     ← 重写：默认路径(本地2B) + 服务表 + 引擎对照 + 排错
└── references/
    └── zotero-plugin.md         ← 新增：Zotero 插件可执行安装/配置节（标注未实测）
```

**删除**：`agent_translator_patch.py`、`test_agent_translator.py`（D3）。

SKILL.md 目标篇幅 **≤ 150 行**（现 107 行，内容净增主要来自服务表和本地路径）。

---

## 5. SKILL.md 内容设计

### 5.1 frontmatter `description`

须重写。当前 description 说「Uses external translation services — google / openai / deepl / deeplx / azure」，**漏掉了本机默认路径**。新版须包含触发词：`PDF 翻译`、`保留排版`、`pdf2zh`、`本地模型翻译`、`Zotero 插件`、`不烧 token`、`离线`。

### 5.2 第一节：默认路径 —— 本地 2B 直连（新增，置于最前）

```bash
# ① 起 2B llama-server（0 token、不出本机）
"C:/Users/caill/.claude/skills/local-ai/scripts/start.sh" minicpm &
curl -s http://127.0.0.1:8080/health          # {"status":"ok"}

# ② 翻译
OPENAILIKED_BASE_URL=http://127.0.0.1:8080/v1 \
  pdf2zh paper.pdf -s openailiked:minicpm5-2b \
    --lang-in en --lang-out zh-CN -t 4 -o out/

# ③ 用完释放显存（2B 占 6–7GB）
"C:/Users/caill/.claude/skills/local-ai/scripts/stop.sh"
```

必须一并写明的坑：

1. **走 `openailiked` 而不是 `openai`**：`openai` 服务要求 `OPENAI_API_KEY` 非空（SDK 构造会抛错），而 `openailiked` 的 key 缺省即回落字符串 `"openailiked"`，本地端点不用编 key。这是上游 issue #792 的官方答复路径。
2. **`BASE_URL` 必须以 `/v1` 结尾**，否则 404。
3. **`-s openailiked:<名字>` 里的名字是标签不是开关**：llama-server 忽略请求体里的 `model` 字段，写 9B 实际仍跑 2B，**且不报错**。
4. **`-t 4`** 对齐 2B 的 `n_slots=4`。
5. **换后端必须清缓存**：缓存键 = `引擎名 + {lang_in, lang_out, model} + 参数`，**`base_url` 不在键内**。因此同一个 `openailiked:minicpm5-2b` 从 llama-server 切到云端端点（或服务端换了模型）会**命中旧译文**。强制重译删 `%TEMP%\cache\` 或用 `--ignore-cache`。
6. **质量兜底**：2B 翻不动时切 `-s deepseek` / `-s silicon` / `-s google`。
7. **`temperature`**：pdf2zh 的 OpenAI 系 translator 硬编码 `temperature: 0`（避免打乱公式标记），而 MiniCPM 官方推荐 1.0 —— 这是既定取舍，写进文档说明，不改源码。

### 5.3 第二节：服务表改为 1.9.11 实测的 22 个

按用途分组（免费 / 国内厂商 / 国外厂商 / 本地 / OpenAI 兼容），每行给 `-s` 标识 + 必需环境变量。删除现有「沿用 1.7.9 文档，未在 1.9.11 上逐个复验」的免责句（改为实测结论）。保留 Ollama 行但标注「本机已于 2026-09-10 卸载」。

### 5.4 第三节：上游订正与引擎选型

- 仓库改名 + 301 重定向（避免以后照着旧链接找）；
- 2.0 主线在 `PDFMathTranslate-next`（`pdf2zh-next` 2.9.0）；
- **一节对照**：新版无 `-s/--service`，改 flag（`--openai` / `--openai-compatible`）+ `--config-file` + `~/.config/pdf2zh/config.v3.toml` + `PDF2ZH_` 前缀环境变量；新版 Bing/Google **已 deprecated**；本机未装，需要时 `uv tool install pdf2zh-next`；
- 老版 `--mcp` 存在；
- **两版均无插件机制**——顺带解释为什么本技能不再维护改源码的补丁。

### 5.5 保留项（现有文档中经核实正确的部分）

- 腾讯 SDK 必须钉 `tencentcloud-sdk-python-tmt==3.1.70`（含症状、根因、修法、`uv tool upgrade` 会冲掉钉子）；
- 1.8.0+ 要求 Python `<3.13`，系统 Python 3.14 上 pip 会静默退回 1.7.9；
- 1.9.11 支持 `-o/--output`；不依赖 torch（onnxruntime）；
- 公式占位符 `{{v0}}` 机制、`not in git repo` 无害提示、缓存位置、`-t` 并发。

### 5.6 排错表

在现有 4 行基础上补：`404` → BASE_URL 少了 `/v1`；`ValueError: The OPENAILIKED_BASE_URL is missing`；「译文与上次完全一致」→ 缓存未清（`base_url` 不入键）；「本地翻译慢 10 倍但不报错」→ 指向 `local-ai` 的 CUDA 静默回退排查。

---

## 6. `references/zotero-plugin.md` 设计

**通篇首行声明**：本机未安装 Zotero，本节全部为上游口径（来源 URL + 日期），**未经实测**。

内容：

1. 是什么：在 Zotero 内调用 pdf2zh / pdf2zh_next 翻译附件，保留公式排版，支持双语对照、裁剪阅读、批量翻译。
2. 与 CLI 技能的关系：同一引擎的两个入口；服务端与本技能的 `pdf2zh.exe` **是两套独立安装**。
3. 安装：服务端（含 `--port 8890`）+ 插件（Zotero 7/8/9/10）。
4. 配置两步走：① LLM API 配置管理新增；② 顶部下拉选中（**只加不选不生效**）。
5. 接本地 2B：base_url 填 `http://127.0.0.1:8080/v1`，model 填 2B 标签，key 随意；⚠️ 插件 UI 的服务名拼写是 `openaliked`（少一个 `i`），CLI 是 `openailiked`。
6. 服务名对照表：插件 UI 名 ↔ 对应引擎 ↔ 与 CLI `-s` 名的关系。
7. `config.json`（老）vs `config.toml`（新）字段差异。
8. 排错：连接失败、翻译失败限流、段落缺失与 `*_enable_json_mode`、OCR/兼容模式。
9. 官方文档入口 `https://zotero-pdf2zh.github.io`。

---

## 7. 删除与同步

- 删 `skills/pdf2zh/agent_translator_patch.py`、`skills/pdf2zh/test_agent_translator.py`（D3）。
- 同步 `skills/README.md`：
  - 技能表 `pdf2zh` 行：现写「23+ 引擎」，改为实测的 22 个；补「本地 2B 直连」要点；
  - 环境依赖表 `pdf2zh.exe` 行同理；
  - **追加一条 2026-09-11 更新日志**（订正仓库改名、服务表实测、本地 2B 路径、删补丁脚本、加 Zotero 节）。

---

## 8. 验证方式

写进文档前**必须实测**（未实测的一律标注）：

| # | 验证项 | 通过标准 |
|---|--------|----------|
| V1 | `start.sh minicpm` + `/health` | 返回 `{"status":"ok"}` |
| V2 | 一页真实论文 PDF 英→中，走 `openailiked` 本地 2B | 产出 mono/dual 两份 PDF，`-o` 生效 |
| V3 | 公式保留 | 译文中公式与原文一致（观察 2B 是否丢 `{{v0}}` 占位符） |
| V4 | `-t 4` 并发 | 服务端日志出现多 slot 并行，无明显串行 |
| V5 | 缓存行为 | 换 `base_url` 后**确实复用**旧译文（证实 5.2-⑤ 的坑） |
| V6 | `stop.sh` | 显存释放，`llama-server` 进程消失 |

V3 若发现 2B 系统性丢公式占位符，则须在 SKILL.md 中把本地 2B 标为「正文可用、公式密集的论文慎用」并给替代路径。

---

## 9. 非目标（YAGNI）

- 不安装 / 不主推 `pdf2zh_next`（D4）；
- 不改 `pdf2zh` 源码、不再维护任何补丁脚本（D3、上游无插件机制）；
- 不复刻 `local-ai` 技能的模型选型 / 显存 / 并发内容，只给指路；
- 不写 Zotero 插件本体的开发或构建。

---

## 10. 开放项

1. V3 的结果决定本地 2B 是否要加「公式密集慎用」的限定语。
2. `references/zotero-plugin.md` 若日后本机装上 Zotero，应回头实测并把「未实测」声明撤下。
