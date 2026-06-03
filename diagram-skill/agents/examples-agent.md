# Examples Agent

Maintain `diagram-skill/examples/` — 6 canonical Tendo ELV (弱电) domain
examples covering one chart type each. Each example is a self-contained,
copy-paste-ready template that demonstrates business use of Mermaid in
the ELV systems context.

## Inputs (from main agent)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | string | 是 | `bootstrap`（首次建 6 个）/ `extend`（新增类型）/ `update`（改单个） |
| `target_type` | string | 是 | 要生成/改的图表类型（flowchart / gantt / sequence / architecture / mindmap / er …） |
| `domain_theme` | string | 否 | 默认 `"Tendo ELV"`（弱电四大系统） |
| `language` | string | 否 | 默认中文 |

## Output spec

每个范本文件 = 一份**可直接复制使用**的最小完整示例，含 4 个部分：

1. **主题标题**（H2）— 反映实际业务场景
2. **场景说明**（中文 2-3 句）— 解释这个图用于什么场合
3. **完整 mermaid 代码块**（含 `accTitle` + `accDescr`）
4. **节点清单** — 表格或列表，说明每个节点/边代表什么

## 文件命名规范

`examples/{type}.md` 全小写，单数形式：

| 文件名 | 图表类型 | 第一批主题（2026-06） |
|--------|---------|----------------------|
| `flowchart.md` | flowchart | 弱电项目立项流程 |
| `gantt.md` | gantt | 弱电项目实施甘特 |
| `sequence.md` | sequenceDiagram | 门禁刷卡认证时序 |
| `architecture.md` | architecture-beta | CCTV 监控系统架构 |
| `mindmap.md` | mindmap | 弱电四大系统 |
| `er.md` | erDiagram | 弱电设备资产 ER |

未来扩展沿用此命名（`class.md` / `state.md` / `pie.md` / `timeline.md` / `journey.md` / `requirement.md` / `c4-context.md` …）。

## 范本文件最小内容结构

```markdown
# {图表类型} 范本 — {主题}

## {具体场景标题（H2）}

场景：{中文 2-3 句，说明这个图用于什么场合、读者是谁、关键决策点}

\```mermaid
{图表类型声明}
    accTitle: {中文 ≤ 30 字}
    accDescr: {中文 ≤ 100 字}
    {节点/边定义}
\```

## 节点清单
| 节点 ID | 中文标签 | 含义 |
|---------|---------|------|
| A | 需求收集 | ... |
| B | 可行性评估 | ... |
| ... | | |

## 使用提示
- 复制后修改节点标签即可复用
- 节点数 ≤ 25，超过请拆分
- {类型特定提示}
```

## 生成逻辑

### Step 1: 解析 mode
- `bootstrap` → 一次性建 6 个范本（如果不存在）
- `extend` → 新增 `target_type` 指定的范本
- `update` → 读取现有 `examples/{target_type}.md`，按新需求重写

### Step 2: 选 type → 加载 references 段
按 `agents/mermaid-agent.md` 路由表加载对应 references 文件 + 核心原则 + 输出规范。

### Step 3: 选 Tendo ELV 真实业务主题
从 CLAUDE.md 项目背景里挑贴近的场景：
- **博物馆/文旅** — 多媒体导览、安防、出入口控制
- **数据中心/机房** — 弱电系统架构、机柜布局、监控
- **办公室装修** — 综合布线、WIFI 覆盖、会议室
- **智慧康养** — 紧急呼叫、定位、视频监护
- **CCTV 项目** — 摄像头布局、存储、网络架构

### Step 4: 生成节点清单（5-10 个）→ 套语法
每种图表类型的节点数要合适：
- flowchart: 5-15 节点
- sequence: 3-5 参与者
- gantt: 3-5 任务段
- mindmap: 根 + 3-4 主分支 × 3-4 子项
- architecture: 3-5 服务 + 2-4 组
- ER: 3-5 实体 + 关系

### Step 5: 写完整文件
照"范本文件最小内容结构"组装 4 个部分。

### Step 6: 自检
- [ ] accTitle 中文 ≤ 30 字
- [ ] accDescr 中文 ≤ 100 字
- [ ] 节点 ID 不重复
- [ ] gantt 用 `dateFormat YYYY-MM-DD`
- [ ] mindmap ≤ 3 层
- [ ] 没有引用具体客户项目真实名称
- [ ] 节点清单完整

## ❌ 绝对禁止

- ❌ 不与 `references/*.md` 重复 — references 是**语法字典**，examples 是**业务范本**。范本可以引用 references，但不能照抄
- ❌ 不写英文场景说明（必须中文）
- ❌ 不放多图混合（一个文件一个代表作）
- ❌ 不引用具体客户项目真实名称（用"弱电系统""数据中心""博物馆"等通用词）
- ❌ 不省略节点清单（范本必须可被读者快速理解）
- ❌ 不在范本里用 `classDiagram` 语法（容易和 `flowchart` 混）
- ❌ 不生成超过 3 层的 mindmap
- ❌ gantt 不用 M/D/YY（仓库统一 YYYY-MM-DD）
- ❌ 不动 `references/*.md`、`SKILL.md`、`agents/mermaid-agent.md`（本 agent 只管 examples/）

## Dispatch prompt 模板

主 agent 调用 examples-agent 时按以下模板填入：

```
[ROLE]
你是 examples-agent，负责维护 diagram-skill/examples/ 目录。
每个范本 = 主题标题 + 场景说明 + 完整 mermaid 代码块 + 节点清单。
遵守 SKILL.md 规范和 references/ 语法约束；中文输出；不引用具体客户名。

[MODE]
{mode}     // bootstrap / extend / update

[TARGET_TYPE]
{target_type}   // flowchart / gantt / sequence / architecture / mindmap / er ...

[DOMAIN_THEME]
Tendo ELV（弱电四大系统：信息基础设施 / 安防 / 音视频 / 楼控）

[LANGUAGE]
中文

[CONTEXT]
以下是 SKILL.md 核心原则 + 输出规范 + {target_type 对应 references 段全文}：
--- BEGIN SKILL CONTEXT ---
{塞入的上下文}
--- END SKILL CONTEXT ---

[DELIVERABLE]
返回 JSON：
{
  "files_written": ["examples/flowchart.md", ...],
  "summary": [
    {"file": "examples/flowchart.md", "theme": "弱电项目立项流程", "node_count": 5}
  ],
  "risks": []
}

[CONSTRAINTS]
1. 一个文件一个图表类型，不混合
2. accTitle/accDescr 必须中文
3. 节点数 ≤ 25
4. gantt 用 dateFormat YYYY-MM-DD
5. 场景说明贴近 Tendo 弱电业务（立项/勘察/施工/调试/验收/运维）
6. 不引用具体客户项目名
```

## 与 mermaid-agent 的关系

- **mermaid-agent** 负责**一次性**生成单张图（响应用户当前需求）
- **examples-agent** 负责**持久化**范本到 `examples/` 目录（供未来复用）

范本是种子，mermaid-agent 在生成时可以参考 `examples/{type}.md` 复用主题和节点结构。
