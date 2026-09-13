# cli — CLI 工具统一入口路由器设计

**日期**：2026-09-13
**作者**：Cailleach & Claude
**状态**：待用户 review

---

## 目标

把 4 个顶层 CLI 技能（`ffmpeg` / `ncm-dump` / `pdf2zh` / `tyc-it`）收进一个**容器型路由器** `cli/`，
提供物理归堆 + 统一入口（含 `/cli` 命令式调用）。

**动机**（用户明确的痛点，按优先级）：

1. **归堆** —— 四个技能散在顶层目录，想按「外部 CLI 包装器」归类管理
2. **统一入口** —— 想要一个命令式的统一调用口（`/cli ffmpeg`）

**明确不是动机**：解决「该触发时没触发」。用户未选此项，因此「子技能失去自动发现」这一代价对本次目标为零。

---

## 背景：这是第三次改主意

| 日期 | 动作 | 提交 |
|---|---|---|
| 2026-06-15 | 6 个 CLI 技能合并进 `cli-anything` 路由器（容器型，二级加载） | `b49a10f` |
| 2026-08-06/07 | **拆除**路由器，5 个 CLI 子技能提升为**顶层独立技能**（自动发现） | `3998d30` |
| 2026-09-13 | **本次**：重建容器型路由器 `cli/`，收 4 个技能 | 待提交 |

**08-06 拆除的实际推力**（本次必须避开）：拆除提交 `3998d30` 同时搬走了
`cli-anything/sub-skills/mimo.disabled/` 与 `web-search-fast.disabled/` 两个**停用但未清理**的子技能。
router 索引指向半死状态，维护成本超过收益，于是整体拆掉改走顶层自动发现。

结论：**上次失败不是架构错，是清理纪律缺失。** 本次用硬规则堵住（见「防漂移规则」）。

---

## 与 2026-06-15 设计的差异

| 项 | 2026-06-15 版 | 本次 | 理由 |
|---|---|---|---|
| 技能名 | `cli-anything` | `cli` | 短，且 `/cli` 好打 |
| 命令式调用 | 未设计（仅自动触发） | **`/cli` + `/cli <tool>`** | 当年不知道技能支持斜杠调用（已核实文档） |
| 子技能 frontmatter | 加 `type: cli-sub` | **不加** | 该字段无任何消费者，是死字段；目录路径已标识身份 |
| 归属范围 | 6 个（含 ocr/mimo/web-search-fast） | **4 个** | 那 3 个已分别被 docling / mimo 计费 / 移除取代 |
| 子技能 scripts/ | 大量相对路径，需逐项验证 | **零 scripts/** | 4 个技能均只有 SKILL.md（pdf2zh 另有 references/） |
| 停用清理 | 无规定（导致 08-06 失败） | **硬规则** | 见下 |

---

## 架构

### 目录布局

```
cli/                                 ← 唯一对外入口；技能名与目录名均为 cli
├── SKILL.md                         ← 路由器（手写，约 80 行）
└── sub-skills/
    ├── ffmpeg/SKILL.md
    ├── ncm-dump/SKILL.md
    ├── pdf2zh/
    │   ├── SKILL.md
    │   └── references/zotero-plugin.md
    └── tyc-it/SKILL.md
```

### 关键机制

Claude Code 的技能发现扫描 `.claude/skills/<name>/SKILL.md`（**一层**）。
子技能位于 `sub-skills/` 之下，因此**不被独立发现**——只有 `cli/SKILL.md` 是技能入口。

> ⚠️ **待实测项**：官方文档只示例到 `skills/<skill-name>/SKILL.md` 这一层，
> 未明文规定「技能目录内再套技能目录」是否扫描。2026-06-15 的设计声称实测过，
> 当前仓库结构亦与之自洽。迁移后必须实测确认（见测试场景 8）。

### 二级加载工作流

```
用户：「把这个视频转一下」
  ↓
Claude 读 cli/SKILL.md（路由器：索引表 + 触发词 + 分发规则）
  ↓ 触发词命中 ffmpeg
Read cli/sub-skills/ffmpeg/SKILL.md（详细说明书）
  ↓
按说明书调 FFmpeg
```

---

## Frontmatter Schema

### 路由器（`cli/SKILL.md`）

```yaml
---
name: cli
description: |
  本机 CLI 工具统一入口。当用户需要以下操作时触发：
  视频/音频转码、剪辑、抽帧、批量处理（FFmpeg）；
  网易云 .ncm 加密音乐解密为 mp3/flac；
  PDF 翻译（保留公式与排版、离线不烧 token）；
  企业工商查询、尽调、股权与实际控制人、司法与行政风险（天眼查）。
  命中后用 Read 读取 sub-skills/<name>/SKILL.md 获取详细命令。
argument-hint: "[工具名]"
arguments: [tool]
---
```

- **不加** `disable-model-invocation`（加了会废掉自动触发；默认值即两条路都通）
- ⚠️ `argument-hint` / `arguments` 在**打包上传**场景会硬报错（仅
  `name`/`description`/`license`/`compatibility`/`metadata`/`allowed-tools` 合规）。
  本技能纯本地使用，无碍；若将来要 `package_skill.py` 打包，先删这两个字段。

### 子技能

**SKILL.md 内容原样不动**，仅 `tyc-it` 需删一行失效引用（见「迁移详情」）。

不加任何新字段，不加 `type`。子技能在 `sub-skills/` 下不被发现，
其 frontmatter 无消费者；**router 的索引表是唯一真相来源**。

---

## 路由器正文设计

### 索引表

```markdown
| 子技能 | 触发词 | 一句话 |
|---|---|---|
| ffmpeg | 转码、剪辑、抽帧、压制、批量处理音视频 | FFmpeg 封装：预设、会话管理、批处理、JSON 输出 |
| ncm-dump | ncm、网易云、加密音乐、mp3、flac | 解密 .ncm → 通用 mp3/flac |
| pdf2zh | PDF 翻译、论文翻译、保留排版、双栏对照 | PDFMathTranslate，默认本地 2B 模型 |
| tyc-it | 查公司、尽调、股权、关联关系、司法风险 | 天眼查 CLI「天眼一下」 |
```

### 分发逻辑

```
若 $tool 非空
    → 合法值 {ffmpeg, ncm-dump, pdf2zh, tyc-it} 之一：
      Read sub-skills/$tool/SKILL.md，按其执行
    → 非法值：列出 4 个合法值，不猜、不兜底
若 $tool 为空但触发词命中索引表某行
    → Read sub-skills/<name>/SKILL.md，按其执行
若都不命中
    → 认输（见下）
```

### 认输规则

触发词不命中任何一行时，router **明说**「不在本路由器的 4 个工具范围内」，
**不调任何子技能**，不试图用别的工具凑答案。这条写死在 SKILL.md 里，
防止 router 退化成「什么都想接」。

---

## 唤起方式

官方文档（code.claude.com/docs/en/skills）已核实：

1. 自建技能支持 `/skill-name` 手动调用——「Claude uses skills when relevant, or you can invoke one directly with `/skill-name`.」
2. **斜杠命令名由目录名决定，不是 frontmatter 的 `name`**——故目录必须是 `cli/`。
3. 支持参数：`/cli ffmpeg` 中 `ffmpeg` 经 `arguments: [tool]` 展开为 `$tool`。

三种入口：

| 用法 | 效果 |
|---|---|
| `/cli` | 列出 4 个工具并询问要哪个 |
| `/cli ffmpeg` | 跳过判断，直接加载 ffmpeg 说明书 |
| 「把这个视频转一下」 | description 自动触发 → 命中 ffmpeg |

注意：`/cli ffmpeg` 本质是「`/cli` 带一个参数」，**不是注册子命令**；
不存在 `/cli:ffmpeg` 这类命名空间。

---

## 迁移详情

全部用 `git mv` 保留历史：

| 原路径 | 新路径 | SKILL.md 改动 |
|---|---|---|
| `ffmpeg/` | `cli/sub-skills/ffmpeg/` | 无 |
| `ncm-dump/` | `cli/sub-skills/ncm-dump/` | 无 |
| `pdf2zh/` | `cli/sub-skills/pdf2zh/` | 无 |
| `tyc-it/` | `cli/sub-skills/tyc-it/` | 删第 9 行「建议唤起命令：`/tyc-it`」 |

### 路径安全性验证

已逐项核查，结论：**本次无风险点**。

| 检查项 | 结果 |
|---|---|
| `ffmpeg` / `ncm-dump` / `tyc-it` 有无 `scripts/` | 无 ✅ |
| `pdf2zh/SKILL.md:10,148` 引用 `references/zotero-plugin.md` | 相对路径，`references/` 随目录同行 ✅ |
| `pdf2zh/SKILL.md:16,26` 引用 `local-ai/scripts/*.sh` | **绝对路径**，不受迁移影响 ✅ |
| 技能内有无 `.claude/skills/<自身>` 自引用 | 无 ✅ |

---

## 防漂移规则（针对 08-06 失败模式）

这两条同时写进 `cli/SKILL.md` 与 `CLAUDE.md`：

- **新增 CLI** = 建 `sub-skills/<name>/` + router 索引表加一行（两步，零代码）
- **停用 CLI** = 从 `sub-skills/` **移出目录** + **删掉索引行**。
  **禁止**留 `xxx.disabled/` 在 `sub-skills/` 下

第二条是硬规则。08-06 的拆除正是 `mimo.disabled/` + `web-search-fast.disabled/` 累积的结果。

---

## 文档同步

| 文件 | 改动 |
|---|---|
| `README.md:13,15,18` | 4 行独立技能行 → 合并为 1 行 `cli`，子工具在说明列列出 |
| `CLAUDE.md:49` 附近 | 「CLI 工具技能已提升为**顶层独立技能**，各自被 Claude 自动发现」→ 改写为 router 机制 + 防漂移规则 |
| `tyc-it/SKILL.md:9` | 删失效的「建议唤起命令：`/tyc-it`」 |

**不属于本次范围**：`docling` / `dwg` / `officecli` / `graphify` / `local-ai` /
`computer-repair-skill` 仍留顶层不动（不带 `cli-` 前缀，非「纯外部 CLI 包装器」定位）。

---

## 测试方案

### 6 个功能场景

| # | 场景 | 材料 | 预期 |
|---|---|---|---|
| 1 | 视频转码 | 任选一个 mp4 | router → ffmpeg，**真产出文件** |
| 2 | ncm 解密 | 任选一个 .ncm | router → ncm-dump，**真产出 mp3/flac** |
| 3 | PDF 翻译 | 任选一篇论文 PDF | router → pdf2zh，**真产出 `*-zh.pdf`** |
| 4 | 企业查询 | 任一家公司名 | router → tyc-it，**真返回企业数据** |
| 5 | 不命中 | 「帮我看看这个 Excel 怎么做透视表」 | router **认输**，不调任何子技能 |
| 6 | 非法工具名 | `/cli` 后跟一个不存在的工具名 | 列出 4 个合法值，不猜 |

### 2 个机制验证（本次新增，因文档未明文）

| # | 验证 | 方法 | 预期 |
|---|---|---|---|
| 7 | 斜杠调用 | 输入 `/cli` 与 `/cli ffmpeg` | 前者列清单，后者直取 ffmpeg 说明书 |
| 8 | 嵌套隔绝发现 | 查看 `/` 菜单 | **不**出现 `ffmpeg`/`tyc-it`/`pdf2zh`/`ncm-dump` 独立条目 |

### PASS 准则

- 1-4：**真产出**（文件生成或数据返回）+ 命中正确子技能
- 5-6：router 主动认输 / 正确拒绝
- 7-8：机制成立。**若 8 失败**（子技能仍被独立发现），架构前提不成立，
  须停下来重新分类任务并重新设计——此为本次唯一的「硬失败」点

---

## 风险与边界

| 风险 | 缓解 |
|---|---|
| 嵌套隔绝发现**未经文档确认** | 测试场景 8 实测；失败则停机重设计 |
| 子技能失去自动发现 | 用户明确表示这不是痛点（未选该项） |
| 08-06 的索引漂移重演 | 防漂移硬规则 + 写进 CLAUDE.md |
| `cli` 名字太泛导致误触发 | description 中列出具体触发词限定范围；实测场景 5 验证认输 |
| 加新 CLI 忘改索引表 | router 正文写明两步流程；正文另附 `LS sub-skills/` 兜底提示 |
| 打包上传时 `arguments` 字段报错 | 本技能不打包；如需打包，删 `argument-hint`/`arguments` |

---

## 实施 Checklist

### Phase 1 — 创建骨架
- [ ] 创建 `cli/` 与 `cli/sub-skills/`
- [ ] 写 `cli/SKILL.md`（索引表 + 分发逻辑 + 认输规则 + 防漂移规则）

### Phase 2 — 迁移 4 个子技能（git mv）
- [ ] `git mv ffmpeg/ cli/sub-skills/ffmpeg/`
- [ ] `git mv ncm-dump/ cli/sub-skills/ncm-dump/`
- [ ] `git mv pdf2zh/ cli/sub-skills/pdf2zh/`
- [ ] `git mv tyc-it/ cli/sub-skills/tyc-it/`

### Phase 3 — 修正失效引用
- [ ] 删 `tyc-it/SKILL.md:9` 的「建议唤起命令：`/tyc-it`」

### Phase 4 — 跑 8 个测试场景（含机制验证 7、8）

### Phase 5 — 文档同步
- [ ] `README.md` 技能表合并为 `cli` 一行
- [ ] `CLAUDE.md` 改写 CLI 小节 + 防漂移规则

### Phase 6 — 提交
- [ ] `git add` + `git commit`（message 需含：做了什么 / 为什么 / 实测结论）

---

## 已确认决策

| 决策 | 选择 |
|---|---|
| 形态 | 容器型路由器（方案 A），非索引型、非双轨薄壳 |
| 归属范围 | 4 个：ffmpeg / ncm-dump / pdf2zh / tyc-it |
| 技能名 | `cli`（目录名 = 命令名） |
| 子技能 frontmatter | **不加** `type: cli-sub` |
| 子技能 SKILL.md | 内容原样不动，仅删 tyc-it 一处失效引用 |
| 唤起 | 自动触发 + `/cli` + `/cli <tool>` 三者并存 |
| 停用清理 | 硬规则：移出目录 + 删索引行，禁止 `.disabled/` |

---

## 附：本次顺带发现的过时信息

`CLAUDE.md` 中「⚠️ `claude --skill --eval` 不是真实 CLI 命令（已用 `claude --help` 验证），勿用」
——`--eval` 这个 flag 确实不存在，但**真正的评测入口是 `claude plugin eval`**（本会话可用）。
该项与本次任务无关，另行处理。
