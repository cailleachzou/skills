# cli 路由器实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `ffmpeg` / `ncm-dump` / `pdf2zh` / `tyc-it` 四个顶层技能收进容器型路由器 `cli/`，提供统一入口与 `/cli <工具名>` 命令式调用。

**Architecture:** 新建 `cli/SKILL.md` 作为唯一被自动发现的技能入口；四个子技能用 `git mv` 移入 `cli/sub-skills/`，从此不被独立发现。路由器只做分发——读索引表命中触发词或 `$tool` 参数，再 `Read` 对应子技能说明书，自身不含任何具体命令。

**Tech Stack:** Claude Code 技能机制（SKILL.md frontmatter）、Git Bash、`git mv`。

**Spec:** `docs/superpowers/specs/2026-09-13-cli-router-design.md`

## Global Constraints

- 仓库根：`C:\Users\caill\.claude\skills\`，分支 `master`，**直接提交到 master**（与既有历史一致）
- 技能名与目录名均为 `cli`（斜杠命令名由**目录名**决定，不是 frontmatter 的 `name`）
- 子技能 SKILL.md **内容原样不动**，唯一例外是 `tyc-it/SKILL.md:9` 删除失效引用
- **不加** `type: cli-sub` 或任何新 frontmatter 字段到子技能
- **不加** `disable-model-invocation`（加了会废掉自动触发）
- 归属范围**严格限定 4 个**：`ffmpeg`、`ncm-dump`、`pdf2zh`、`tyc-it`。`docling` / `dwg` / `officecli` / `graphify` / `local-ai` / `computer-repair-skill` 不动
- 停用子技能时禁止留 `xxx.disabled/`——移出目录 + 删索引行
- 测试素材含个人信息，pdf2zh **必须走本地模型**，禁止切云端翻译服务

---

### Task 1: 创建路由器 `cli/SKILL.md`

**Files:**
- Create: `cli/SKILL.md`

**Interfaces:**
- Consumes: 无（首个任务）
- Produces: 技能入口 `cli`，其「工具索引」表登记 4 个子技能名 `ffmpeg` / `ncm-dump` / `pdf2zh` / `tyc-it`。Task 2 迁移的目录名必须与这张表**逐字一致**

- [ ] **Step 1: 创建 `cli/SKILL.md`**

写入以下**完整**内容（一字不改）：

````markdown
---
name: cli
description: |
  本机 CLI 工具统一入口。当用户需要以下操作时触发：
  视频/音频转码、剪辑、抽帧、压制、批量处理（FFmpeg）；
  网易云 .ncm 加密音乐解密为 mp3/flac；
  PDF 翻译（保留公式与排版、离线不烧 token）；
  企业工商查询、尽调、股权与实际控制人、司法与行政风险（天眼查）。
  命中后用 Read 读取 sub-skills/<name>/SKILL.md 获取详细命令。
argument-hint: "[工具名]"
arguments: [tool]
---

# cli — 本机 CLI 工具统一入口

本技能是一个**路由器**，本身不执行任何操作。它只做一件事：
把请求分发到 `sub-skills/` 下的 4 个子技能说明书。

## 工具索引

| 子技能 | 触发词 | 一句话 |
|---|---|---|
| `ffmpeg` | 转码、剪辑、抽帧、压制、批量处理音视频 | FFmpeg 封装：预设、会话管理、批处理、JSON 输出 |
| `ncm-dump` | ncm、网易云、加密音乐、mp3、flac | 解密 .ncm → 通用 mp3/flac |
| `pdf2zh` | PDF 翻译、论文翻译、保留排版、双栏对照 | PDFMathTranslate，默认本地 2B 模型 |
| `tyc-it` | 查公司、尽调、股权、关联关系、司法风险 | 天眼查 CLI「天眼一下」 |

## 分发规则

按以下顺序判断，命中即停：

1. **带参数调用**（`/cli <工具名>`）

   本次调用传入的工具名参数是：「`$tool`」

   - 上面引号内是上表 4 个合法值之一 → 直接 `Read sub-skills/<该值>/SKILL.md`，按它执行
   - 上面引号内为**空**（说明本次是无参数调用，如 `/cli` 或自然语言触发）→ **跳过本规则**，看规则 2
   - 上面引号内有值但不属于那 4 个 → 列出 4 个合法值，**不猜、不兜底、不改用别的工具**
2. **无参数调用**（`/cli`）→ 列出上表 4 行，问用户要哪一个
3. **自然语言**（自动触发）→ 用上表「触发词」列匹配
   - 命中 → `Read sub-skills/<name>/SKILL.md`，按它执行
   - 未命中 → 见「认输规则」

## 认输规则

上表触发词全不命中时，**明说**「这不在本路由器的 4 个工具范围内」，
并列出 4 个工具名。**不调任何子技能，不试图用别的工具凑答案。**

本路由器只覆盖这 4 个 CLI。其他能力（文档解析、CAD、Office、知识图谱等）
不在范围内，不要假装路由过去。

## 维护规则

> ⚠️ 两条硬规则。2026-08-06 拆除旧路由器 `cli-anything` 的直接原因就是没遵守第二条。

**新增 CLI**（两步，零代码）：

1. 建 `sub-skills/<name>/SKILL.md`（+ 可选 `scripts/`、`references/`）
2. 在上方「工具索引」表加一行

**停用 CLI**：

1. 把 `sub-skills/<name>/` **整个目录移出**
2. **删掉**「工具索引」表对应行

**禁止**留 `sub-skills/<name>.disabled/` 这类残留——索引与目录必须严格一致。
若忘记加索引行，可用 `LS sub-skills/` 兜底发现。

## 子技能说明在哪

每个子技能的完整说明书在 `sub-skills/<name>/SKILL.md`，**按需 Read，不要预先全读**
（会浪费上下文）。本文件不含任何具体命令参数，参数一律看子技能说明书。
````

- [ ] **Step 2: 验证文件已创建且 frontmatter 合法**

Run:
```bash
cd "C:/Users/caill/.claude/skills" && head -1 cli/SKILL.md && grep -c "^name: cli$" cli/SKILL.md
```

Expected: 第一行输出 `---`（frontmatter 必须从文件**第一行**开始，否则整份文件会被当成正文静默降级）；第二行输出 `1`

- [ ] **Step 3: 验证 4 个索引行的技能名拼写**

Run:
```bash
cd "C:/Users/caill/.claude/skills" && grep -oE '^\| `[a-z0-9-]+`' cli/SKILL.md
```

Expected: 恰好 4 行，依次为 `` | `ffmpeg` ``、`` | `ncm-dump` ``、`` | `pdf2zh` ``、`` | `tyc-it` ``
（这 4 个字符串必须与 Task 2 迁入的目录名逐字一致）

- [ ] **Step 4: 提交**

```bash
cd "C:/Users/caill/.claude/skills" && git add cli/SKILL.md && git commit -m "$(cat <<'EOF'
feat(cli): 新增 CLI 工具路由器骨架

- 新建 cli/SKILL.md：工具索引表（4 行）+ 分发规则 + 认输规则 + 维护规则
- 支持 /cli（列清单）与 /cli <工具名>（直取子技能说明书）两种命令式调用
- 本任务只建路由器，子技能尚未迁入，此时 router 尚无可用目标

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: 迁移 4 个子技能进入 `sub-skills/`

**Files:**
- Move: `ffmpeg/` → `cli/sub-skills/ffmpeg/`
- Move: `ncm-dump/` → `cli/sub-skills/ncm-dump/`
- Move: `pdf2zh/` → `cli/sub-skills/pdf2zh/`
- Move: `tyc-it/` → `cli/sub-skills/tyc-it/`
- Modify: `cli/sub-skills/tyc-it/SKILL.md:9`

**Interfaces:**
- Consumes: Task 1 建立的 `cli/` 目录与索引表中的 4 个技能名
- Produces: `cli/sub-skills/<name>/SKILL.md` 四个路径，供 Task 3-5 的 `Read` 使用

- [ ] **Step 1: 迁移前记录基线**

Run:
```bash
cd "C:/Users/caill/.claude/skills" && git status --porcelain && find ffmpeg ncm-dump pdf2zh tyc-it -type f | sort
```

Expected: `git status --porcelain` 为空（干净）；文件清单恰好 5 个——
`ffmpeg/SKILL.md`、`ncm-dump/SKILL.md`、`pdf2zh/SKILL.md`、`pdf2zh/references/zotero-plugin.md`、`tyc-it/SKILL.md`

**若清单不符（多出 `scripts/` 等文件），停下来报告**——spec 的路径安全性结论基于「零 scripts/」这个前提。

- [ ] **Step 2: 建 `sub-skills/` 目录并执行 4 次 `git mv`**

⚠️ `cli/sub-skills/` 在 Task 1 结束时**并不存在**（T1 只建了 `cli/`）。
`git mv` 不会自动创建目标父目录，直接搬会报 `fatal: destination directory does not exist`。
所以必须先 `mkdir -p`：

```bash
cd "C:/Users/caill/.claude/skills" && mkdir -p cli/sub-skills && git mv ffmpeg cli/sub-skills/ffmpeg && git mv ncm-dump cli/sub-skills/ncm-dump && git mv pdf2zh cli/sub-skills/pdf2zh && git mv tyc-it cli/sub-skills/tyc-it
```

- [ ] **Step 3: 验证迁移结果与历史保留**

⚠️ 本步**故意**让 `ls` 失败（旧路径应当消失），因此**不能用 `&&` 串联**——
`&&` 会在 `ls` 失败处截断，后面的 rename 检查根本不会跑。用 `;` 分隔：

```bash
cd "C:/Users/caill/.claude/skills" && find cli -type f | sort; echo "--- 顶层是否还有残留（预期 4 行 No such file）---"; ls -d ffmpeg ncm-dump pdf2zh tyc-it 2>&1 | head -5; echo "--- git 是否识别为 rename ---"; git status --porcelain | head -20
```

Expected:
- `find cli -type f` 恰好 6 个文件：`cli/SKILL.md` + 5 个迁移文件（含 `cli/sub-skills/pdf2zh/references/zotero-plugin.md`）
- `ls -d` 对 4 个旧路径全部报 `No such file or directory`
- `git status --porcelain` 显示 `R`（rename）而非 `D`+`??`，证明历史保留

- [ ] **Step 4: 删除 `tyc-it/SKILL.md` 中失效的唤起命令引用**

打开 `cli/sub-skills/tyc-it/SKILL.md`，删除第 9 行：

```markdown
建议唤起命令：`/tyc-it`
```

同时删除该行上方紧邻的**空行**（若删除后出现连续两个空行，合并为一个）。
其余内容**一字不改**。

- [ ] **Step 5: 验证引用已删除且正文行数正确**

Run:
```bash
cd "C:/Users/caill/.claude/skills" && grep -c "建议唤起命令" cli/sub-skills/tyc-it/SKILL.md; wc -l < cli/sub-skills/tyc-it/SKILL.md
```

Expected: `grep -c` 输出 `0`（且退出码非 0，属正常）；第二个输出 ≤ 315（原 315 行，删掉 1 行引用 + 可能 1 行空行）

- [ ] **Step 6: 验证子技能的绝对路径引用未被破坏**

Run:
```bash
cd "C:/Users/caill/.claude/skills" && grep -n "local-ai/scripts\|references/zotero-plugin.md" cli/sub-skills/pdf2zh/SKILL.md
```

Expected: 4 处命中，且 `local-ai/scripts/*.sh` 仍是**绝对路径** `C:/Users/caill/.claude/skills/local-ai/scripts/...`（绝对路径不受迁移影响）；`references/zotero-plugin.md` 仍是相对路径，该文件确实存在于 `cli/sub-skills/pdf2zh/references/`

- [ ] **Step 7: 提交**

```bash
cd "C:/Users/caill/.claude/skills" && git add -A && git commit -m "$(cat <<'EOF'
refactor(cli): 4 个 CLI 技能迁入 sub-skills/，失去独立发现

- git mv ffmpeg / ncm-dump / pdf2zh / tyc-it → cli/sub-skills/
- 删 tyc-it/SKILL.md 中失效的「建议唤起命令：/tyc-it」（迁移后该命令不再存在）
- 子技能 SKILL.md 其余内容原样不动，不加 type 字段
- 已核查：pdf2zh 对 local-ai/scripts 是绝对路径、对 references/ 是相对路径，
  两者迁移后均仍有效
- 此刻起这 4 个技能不再被 Claude 自动发现，只能经 cli 路由器进入

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: 机制验证（硬门禁 —— 失败则停机重设计）

**这是整个计划的唯一硬失败点。** spec 中「子技能放进 `sub-skills/` 后不被独立发现」这条**官方文档没有明文**，仅有 2026-06-15 那次的实测声称。本任务实测确认。**场景 8 失败则架构前提不成立，停止执行后续任务并回报。**

**Files:**
- 只读，不修改任何文件

**Interfaces:**
- Consumes: Task 2 完成的目录结构
- Produces: 「嵌套隔绝发现」这一前提的实测结论——Task 4、5 的验证都建立在它成立之上

> ⚠️ **必须在全新会话中执行。** 技能发现发生在会话启动时；当前会话的技能列表可能仍是旧的。执行者应告知用户开启新会话后再继续本任务。

- [ ] **Step 1: 场景 8 —— 验证子技能未被独立发现**

在**新会话**中，让用户输入 `/`，查看技能菜单。

Expected: 菜单中出现 `cli`，**不出现** `ffmpeg` / `ncm-dump` / `pdf2zh` / `tyc-it` 这四个独立条目。

**若四个子技能仍出现在菜单中 → 硬失败。**立即停止，不要执行后续任务，回报：
「嵌套隔绝发现的前提不成立，`cli/sub-skills/` 下的技能仍被独立发现，架构需重新设计。」

- [ ] **Step 2: 场景 7a —— 验证 `/cli` 无参数调用**

在新会话中输入 `/cli`。

Expected: 列出工具索引表的 4 行（ffmpeg / ncm-dump / pdf2zh / tyc-it）并询问用户要用哪一个。
**不**直接执行任何工具，**不**读任何子技能说明书。

- [ ] **Step 3: 场景 7b —— 验证 `/cli <工具名>` 带参数调用**

在新会话中输入 `/cli ffmpeg`。

Expected: 直接 `Read cli/sub-skills/ffmpeg/SKILL.md` 并按其说明行动；
**不**重新询问要用哪个工具（参数已指明）。

- [ ] **Step 4: 记录实测结论**

把 Step 1-3 的观察结果（菜单实际内容、`/cli` 与 `/cli ffmpeg` 的实际反应）记录下来，
作为 Task 6 文档同步与最终 commit message 的实测依据。
若 Step 1 通过但 Step 2/3 任一失败，**不算硬失败**——记下现象，继续，但须在 commit message 中写明。

---

### Task 4: 四个工具的功能验证（场景 1-4）

**Files:**
- 只读测试素材；产物写入临时目录
- 不修改仓库内任何文件

**Interfaces:**
- Consumes: Task 3 确认成立的嵌套隔绝前提
- Produces: 4 个子技能确实可用的实测证据

> 在**新会话**中，用自然语言（不指定 `/cli`）触发路由器，验证自动分发。
> **所有产物一律写入测试目录 `C:/Users/caill/AppData/Local/Temp/cli-router-test/`**，
> 不得写回素材所在目录。该目录可能不存在，首次使用前先建。

- [ ] **Step 0: 建测试目录**

```bash
mkdir -p "/c/Users/caill/AppData/Local/Temp/cli-router-test" && ls -d "/c/Users/caill/AppData/Local/Temp/cli-router-test"
```

- [ ] **Step 1: 场景 1 —— ffmpeg 转码**

让路由器处理，**在提示里明确指定输出到测试目录**：

```
把这个视频转成 mp4，输出到 C:\Users\caill\AppData\Local\Temp\cli-router-test\scene1.mp4：
C:\Users\caill\Videos\NVIDIA\Desktop\Desktop 2026.09.10 - 18.10.36.01.mp4
```

Expected: router 命中 ffmpeg → Read `cli/sub-skills/ffmpeg/SKILL.md` → 调用 FFmpeg。
验证产物：

```bash
ffprobe -v error -show_entries format=format_name,duration -of default=nw=1 "C:/Users/caill/AppData/Local/Temp/cli-router-test/scene1.mp4"
```

Expected: 命令成功（退出码 0），输出含 `format_name=` （含 `mp4`）与非零 `duration`。
**若 ffprobe 报 "No such file" → 场景 1 失败**（router 未产出或写错位置）。

- [ ] **Step 2: 场景 2 —— ncm 解密**

**先把素材拷到测试目录**（避免在 `VipSongsDownload\` 内生成产物）：

```bash
cp "/d/CloudMusic/VipSongsDownload/ALI - Wild Side.ncm" "/c/Users/caill/AppData/Local/Temp/cli-router-test/scene2.ncm" && ls -la "/c/Users/caill/AppData/Local/Temp/cli-router-test/scene2.ncm"
```

然后让路由器处理：

```
把这个 .ncm 解密成能播的格式，输出到 C:\Users\caill\AppData\Local\Temp\cli-router-test\：
C:\Users\caill\AppData\Local\Temp\cli-router-test\scene2.ncm
```

Expected: router 命中 ncm-dump。产物为 `scene2.mp3` 或 `scene2.flac`，验证：

```bash
ls -la "/c/Users/caill/AppData/Local/Temp/cli-router-test/" | grep scene2
ffprobe -v error -show_entries format=format_name,duration -of default=nw=1 "C:/Users/caill/AppData/Local/Temp/cli-router-test/scene2.mp3" 2>/dev/null || ffprobe -v error -show_entries format=format_name,duration -of default=nw=1 "C:/Users/caill/AppData/Local/Temp/cli-router-test/scene2.flac"
```

Expected: 能读出 `format_name`（`mp3` 或 `flac`）与合理时长（非 0）。

- [ ] **Step 3: 场景 3 —— pdf2zh 翻译（zh→en，必须走本地模型）**

```
把这份 PDF 翻译成英语，保留排版，输出到 C:\Users\caill\AppData\Local\Temp\cli-router-test\：
C:\Users\caill\Downloads\Documents\5_学籍在线验证报告_邹景焘.pdf
```

⚠️ **必须使用本地 MiniCPM5-2B 路径**（pdf2zh 默认）。**禁止**加 `-s google` / `-s deepl` 等云端引擎——该素材含个人信息。

Expected: router 命中 pdf2zh。产物文件名由 pdf2zh 决定（通常 `<原名>-en.pdf` 或 `-mono.pdf` 变体）。
先用 `ls` 查出实际产物名，再验证：

```bash
ls -la "/c/Users/caill/AppData/Local/Temp/cli-router-test/"
PYTHONIOENCODING=utf-8 py -3 -c "
import glob, pymupdf
for f in glob.glob(r'C:\Users\caill\AppData\Local\Temp\cli-router-test\*.pdf'):
    d = pymupdf.open(f)
    print('file:', f)
    print('pages:', d.page_count)
    print('sample:', repr(''.join(p.get_text() for p in d)[:200]))
"
```

Expected: 至少一个 `.pdf` 产物；`pages: 1`（与原文一致）；`sample` 中能看出英文译文
（不再是原文的「注意事项：1、《学籍在线验证报告》是教育部学籍电子注册备案的查询结果。」）。
**若 sample 仍是中文原文 → 场景 3 失败**（未真正翻译）。

- [ ] **Step 4: 场景 4 —— tyc-it 企业查询**

```
查一下北京字节跳动科技有限公司的工商信息
```

Expected: router 命中 tyc-it → Read `cli/sub-skills/tyc-it/SKILL.md` → 调用 `tyc` 命令 → **返回真实企业数据**（企业名、状态、法定代表人等），而非空表或占位内容。

- [ ] **Step 5: 记录 4 个场景的实际命令与结果**

把每个场景中 router 实际 `Read` 的子技能路径、实际执行的命令、产物路径记下来，作为 commit message 的实测依据。

**若任一场景失败**：不要修改子技能 SKILL.md 来「修好它」——子技能内容是本次迁移的**不变量**。
失败说明分类错误，回报并停下。

---

### Task 5: 认输行为验证（场景 5-6）

**Files:**
- 只读，不修改任何文件

**Interfaces:**
- Consumes: Task 3 确认成立的路由器分发逻辑
- Produces: 路由器边界行为的实测证据

- [ ] **Step 1: 场景 5 —— 不命中时认输**

在新会话中输入：

```
帮我看看这个 Excel 怎么做透视表
```

Expected: router **不命中**任何触发词 → 明说「这不在本路由器的 4 个工具范围内」并列出 4 个工具名。
**关键：不得调用任何子技能，不得试图用别的工具凑答案。**

- [ ] **Step 2: 场景 6 —— 非法工具名**

在新会话中输入 `/cli` 后跟一个不存在的工具名，例如：

```
/cli excel
```

Expected: 列出 4 个合法值（ffmpeg / ncm-dump / pdf2zh / tyc-it），**不猜、不兜底**、不改用别的工具。

- [ ] **Step 3: 记录认输行为的实际措辞**

记下 router 实际输出的措辞，作为 commit message 实测依据。
若 router 在场景 5 中调用了任何子技能（哪怕「顺便」），这是**行为缺陷**——
回到 `cli/SKILL.md` 强化「认输规则」小节措辞，然后重跑本任务 Step 1。

---

### Task 6: 文档同步

**Files:**
- Modify: `README.md`（第 13、15、18 行附近的技能表）
- Modify: `CLAUDE.md`（第 49 行附近的「CLI 工具技能」小节）

**Interfaces:**
- Consumes: 前五个任务的全部实测结论
- Produces: 仓库文档与新目录结构一致

- [ ] **Step 1: 读取 README.md 技能表现状**

Run:
```bash
cd "C:/Users/caill/.claude/skills" && grep -n "pdf2zh\|tyc-it\|ncm-dump\|ffmpeg" README.md | head -20
```

记下这 4 个技能各占的整行内容（含表格首尾的 `|`），后续整体替换。

- [ ] **Step 2: 合并 README.md 的 4 行为 1 行**

把技能表中 `pdf2zh` / `tyc-it` / `ncm-dump` / `ffmpeg` 的 4 个独立行**删除**，
在原位置插入一行 `cli`：

```markdown
| **cli** | CLI 工具统一入口 | 容器型路由器，含 4 个子工具：**ffmpeg**（转码/剪辑/批处理）、**ncm-dump**（网易云 .ncm 解密）、**pdf2zh**（PDF 翻译，默认本地 2B）、**tyc-it**（天眼查商查）。调用方式：说自然语言自动触发，或 `/cli` 列清单、`/cli <工具名>` 直取。详细说明见 `cli/sub-skills/<name>/SKILL.md` |
```

**保留**其它行不动（`docling` / `dwg` / `officecli` / `graphify` / `local-ai` / `computer-repair-skill` 仍在顶层）。

- [ ] **Step 3: 同步 README.md 的依赖表与命令路径表**

⚠️ 本步覆盖**两个**目录路径行，不是只有一个。Task 2 的评审发现计划初稿漏掉了 `ffmpeg/`：

```bash
cd "C:/Users/caill/.claude/skills" && grep -n '`ffmpeg/\|`pdf2zh/\|`ncm-dump/\|`tyc-it/' README.md
```

必须先跑上面这条命令拿到**实际**的命中行，再逐行改。基于 2026-09-13 的实测，预期存在两行：

| 行 | 现状 | 改为 |
|---|---|---|
| README.md:95 | `\| **ffmpeg / ffprobe** \| \`ffmpeg/\` \| 音视频转码 \|` | 路径列改为 `` `cli/sub-skills/ffmpeg/` `` |
| README.md:96 | `\| **pdf2zh.exe** \| \`pdf2zh/\` \| ...` | 路径列改为 `` `cli/sub-skills/pdf2zh/` `` |

`ncm-dump` 与 `tyc-it` 预计无目录路径行——但**以实际 grep 结果为准**，有就一并改。

**注意**：`pdf2zh.exe` 的安装路径 `C:\Users\caill\.local\bin\pdf2zh.exe` **不变**（uv tool 装的，与技能目录无关）；`ffmpeg / ffprobe` 的二进制路径同理不变。只改**技能目录**那一列。

- [ ] **Step 4: 改写 CLAUDE.md 的 CLI 小节**

找到 `CLAUDE.md` 第 49 行附近的原文：

```markdown
## CLI 工具技能（顶层独立）

CLI 工具技能（文档解析 / CAD / FFmpeg / PDF 翻译）已提升为**顶层独立技能**，各自被 Claude 自动发现：
```

改为：

```markdown
## CLI 工具技能

**两类并存**：

- **路由器型** —— `cli`：容器型统一入口，下辖 4 个子技能（ffmpeg / ncm-dump / pdf2zh / tyc-it），
  位于 `cli/sub-skills/`，**不被自动发现**，只能经路由器进入。说自然语言自动触发，
  或 `/cli` 列清单、`/cli <工具名>` 直取子技能说明书。
  ⚠️ **维护硬规则**：停用子技能必须「移出目录 + 删索引行」，**禁止**留 `xxx.disabled/`
  ——2026-08-06 拆掉旧路由器 `cli-anything` 就是因为这类残留腐化了索引。
- **顶层独立型** —— `docling` / `dwg` / `officecli` / `graphify` / `local-ai` /
  `computer-repair-skill`：各自被 Claude 自动发现。
```

- [ ] **Step 5: 校验文档无残留旧表述**

Run:
```bash
cd "C:/Users/caill/.claude/skills" && echo "--- 不应再有『顶层独立技能』描述这 4 个 ---" && grep -n "已提升为\*\*顶层独立技能\*\*" CLAUDE.md; echo "--- README 中这 4 个技能的独立行应为 0 ---"; grep -cE '^\| \*\*(ffmpeg|ncm-dump|pdf2zh|tyc-it)\*\*' README.md
```

Expected: 第一条无输出（退出码非 0 属正常）；第二条输出 `0`

- [ ] **Step 6: 提交**

commit message 的「实测结论」段落**必须用 Task 3-5 的真实观察替换**，
逐条写清：菜单是否隔绝了子技能（场景 8）、`/cli` 与 `/cli ffmpeg` 的实际行为（场景 7）、
4 个工具各自的产物路径与验证结果（场景 1-4）、认输行为的实际措辞（场景 5-6）。
**不得**保留任何未填的尖括号占位。

```bash
cd "C:/Users/caill/.claude/skills" && git add README.md CLAUDE.md && git commit -m "$(cat <<'EOF'
docs: 同步 cli 路由器迁移（README 技能表 + CLAUDE.md 说明）

- README 技能表：4 行独立技能合并为 1 行 cli，子工具列在说明中
- README 依赖/路径表：pdf2zh/ 目录路径改为 cli/sub-skills/pdf2zh/
  （pdf2zh.exe 的 uv tool 安装路径不变）
- CLAUDE.md：改写「CLI 工具技能已提升为顶层独立技能」为「路由器型 + 顶层独立型两类并存」，
  并写入防漂移硬规则（停用必须移出目录 + 删索引行，禁止 .disabled/）
- 实测结论：
  - 场景 8（嵌套隔绝）：<菜单实际内容>
  - 场景 7（斜杠调用）：<cli 与 /cli ffmpeg 的实际行为>
  - 场景 1-4（功能）：<4 个产物路径 + 验证结果>
  - 场景 5-6（认输）：<实际措辞>

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

## 完成后的状态

```
cli/                                 ← 唯一被自动发现的入口，命令 /cli
├── SKILL.md                         ← 路由器
└── sub-skills/                      ← 4 个子技能，不被独立发现
    ├── ffmpeg/SKILL.md
    ├── ncm-dump/SKILL.md
    ├── pdf2zh/{SKILL.md, references/zotero-plugin.md}
    └── tyc-it/SKILL.md

docling/ dwg/ officecli/ graphify/ local-ai/ computer-repair-skill/   ← 仍在顶层，不动
```

## 需要人工执行的部分

以下步骤**无法由 agent 独立完成**，需用户配合：

- **Task 3 Step 1-3**：在新会话中查看 `/` 菜单、输入 `/cli` 与 `/cli ffmpeg`（agent 无法观测自己的技能菜单）
- **Task 4 全部**：在**新会话**中用自然语言触发（当前会话的技能列表可能是旧快照）
- **Task 5 全部**：同上

agent 可完成：Task 1、2、6 的文件操作与提交；Task 3-5 的结果记录与 commit message 撰写。
