# Claude Code 插件技能地图

> 覆盖 **8 个插件、34 个技能**。`frontend-design` 和 `skill-creator` 各有两个插件来源，地图里合并成一行（`frontend-design` 的两个来源已逐字节比对，完全一致）。
> 全部内容读自各技能真实的 `SKILL.md`，生成于 2026-09-10。**不含本机自建的那 10 个技能**（outlook / tyc-it / dwg 等）。

---

## 怎么用

按你手上的活找到对应的桶，扫一遍**「什么信号让它启动」**那一列。

**你要记的是触发词，不是技能名。** 技能不是你想用才用的，是你说到某些话它自己跳出来——不知道触发词，等于装了没用。

### 先记这 5 个（最可能常用）

| 技能 | 一句话 |
|---|---|
| `internal-comms` | 说「写个周报」，从你的邮件/日程抓料写成三段式周报 |
| `docx` / `pdf` | 说「生成 Word」「读一下这个 PDF」，你本机 PDF 工具链已经装齐 |
| `brainstorming` | 任何还没想清楚的事，先说一句「我想做个 XX」 |
| `systematic-debugging` | 说「怎么突然不好使了」，它会逼你先查根因再动手 |
| `skill-creator` | 说「把刚才那套流程存成技能」，把重复活沉淀下来 |

### 三个坑，先说在前面

**1. 技能是自动触发的，你没法手动调用。**
打 `run internal-comms` 没用。你说「帮我写个周报」，它自己跳出来。

**2. `/` 斜杠命令 ≠ 技能，这是两套东西。**
技能靠说话触发；命令必须打 `/xxx` 才会跑。下表里带 `/` 前缀的是命令：`/code-review`、`/revise-claude-md`。

**3. 装了 ≠ 能用，改了要重启。**
`✔ enabled` 不等于技能能加载——缓存副本残缺会被静默遮蔽（2026-09-10 刚修过一次）。另外**技能列表在会话启动那一刻就固定了**，新装/新改/新修完，当前会话不会变。

---

## 桶一 · 文档 & 汇报（6）

| 技能 | 什么信号让它启动 | 你会拿到什么 | 跟谁搭 / 坑 |
|---|---|---|---|
| `docx` | 「生成一份 Word」「把这份 .docx 改了」「按模板出份报告/信函」「加批注」「走修订模式改合同」 | 带样式、目录、页眉页脚、批注修订的 `.docx` | **改现有文档必须走 unzip → 改 `word/document.xml` → zip**，docx-js 打不开已有文件；老 `.doc` 要先转 `.docx` |
| `xlsx` | 「打开我下载里那个 xlsx」「给这表加一列 / 写个公式」「CSV 转 Excel」「建个财务模型」 | 格式专业、公式可重算、零 `#REF!` 的 `.xlsx` | **只要含公式就必须跑 `scripts/recalc.py`**；`data_only=True` 存盘会**永久毁掉公式**；`.xlsm` 不加 `keep_vba=True` 丢宏；禁用 `XLOOKUP`/`SORT`/`FILTER` 等新函数 |
| `pptx` | 「做个 PPT」「做个 pitch deck」「从模板出几页」「加演讲备注」 | 版式丰富、图表为原生 PowerPoint 对象、过 schema 校验的 `.pptx` | 默认画布只有 10"×5.625"，**要先设 `pres.layout`**；hex 颜色不能带 `#`；改幻灯片顺序必须在填内容之前 |
| `pdf` | 「读一下这个 PDF」「把表格抽出来」「合并 / 拆分」「加水印」「设密码」「扫描件 OCR」「填表单」 | 文本/表格数据，或处理后的 PDF | **ReportLab 里绝不能用 Unicode 上下标字符**（渲染成黑方块），要用 `<sub>` 标签；OCR 需另装 `pytesseract` |
| `internal-comms` | 「写个周报 / 3P」「给团队发个进度同步」「全员信」「起草 FAQ」「上线状态报告」「事故复盘」 | 按你公司格式写好的内部沟通稿 | 先从邮件/日程/Slack/Drive 抓料，**本机没接这类数据源，抓不到就会直接问你**；只用于对内，不用于对外文档 |
| `doc-coauthoring` | 「帮我写个文档」「起草个提案」「写份技术方案」「写个 PRD / design doc / RFC」 | 三阶段打磨（拉上下文 → 精炼结构 → 找读者测）过的文档 | 它会**要求你别直接改文档**，而是描述要改什么（好让它学你的风格）；会先问你要不要走这套流程 |

---

## 桶二 · 写代码 & 交付流程（16）

> 前 13 个 superpowers 技能是一条**流水线**，按顺序走：
> `brainstorming` → `writing-plans` → `subagent-driven-development`（或 `executing-plans`）→ `finishing-a-development-branch`
> 中间横向支撑：`test-driven-development`、`systematic-debugging`、`requesting/receiving-code-review`、`verification-before-completion`、`using-git-worktrees`、`dispatching-parallel-agents`。
> **先记住这条线，再记单个技能。**

| 技能 | 什么信号让它启动 | 你会拿到什么 | 跟谁搭 / 坑 |
|---|---|---|---|
| `brainstorming` | **任何还没想清楚的事**：「我想做个 XX」「帮我加个功能」「这个能不能做？」 | 想法 → 设计（聊天的短的，或 `docs/superpowers/specs/...-design.md`） | 流水线起点。**硬门禁：没你点头不准写码、不准动手**；发现隐藏复杂度只升不降 |
| `writing-plans` | 「设计定了，写个实施计划」「分几步做，列个计划」 | `docs/superpowers/plans/...md`，每任务 2-5 分钟粒度、带精确文件路径 | 上游是 `brainstorming`；下游必接 `subagent-driven-development`（推荐）或 `executing-plans`；**计划里不许出现 TBD /「加适当错误处理」** |
| `subagent-driven-development` | 「在这个会话里按计划把任务一个个派给子 agent 做」 | 每任务新派一个子 agent + 每个任务后双评审，全程记 ledger | 上游 `writing-plans`；下游 `finishing-a-development-branch`；**绝不并行派多个实现者**；每任务修复循环 5 轮封顶 |
| `executing-plans` | 「按这个计划执行」「照那份计划做」——**另开会话**干活时 | 逐任务执行完并验证 | 上游 `writing-plans`；下游必接 `finishing-a-development-branch`；当前环境有子 agent 能力的话，官方建议改用它上面那个 |
| `dispatching-parallel-agents` | 「这几个测试文件都挂了，一起修」「这几处报错互不相干」「并行处理一下」 | 一次响应派多个子 agent 并行修，汇总各自根因 | 跟 `subagent-driven-development` 恰好相反（那个强调一次只派一个）；**agent 之间会改同一个文件时必须串行** |
| `test-driven-development` | 「实现这个功能」「修这个 bug」「重构这块代码」——任何动生产代码之前 | 先写会失败的测试 → 眼看它失败 → 最小实现 → 重构 | 上游接 `brainstorming` 批准后；**铁律：先写了代码就得删掉从头来**，不许留作「参考」 |
| `systematic-debugging` | 「这个测试挂了」「线上报错了」「怎么突然不好使了」「性能变差了」 | 四阶段（根因调查→模式比对→假设验证→修复）→ 根因 + 单个修复 | **铁律：没做完根因调查不许提方案**；同一问题修 3 次还没好 = 架构问题，停下来讨论 |
| `verification-before-completion` | 你**准备说**「搞定了」「修好了」「应该没问题」的时候 | 先跑完整验证、读完整输出、看退出码，才允许说出口 | 通用于所有技能的尾部；**不是这条消息里跑的验证就不算证据**；子 agent 报 success 也要自己查 diff 核实 |
| `requesting-code-review` | 「帮我 review 一下」「这块写完了找人看看」「合并前先审一遍」 | diff → 子 agent 按模板审 → Critical / Important / Minor 清单 | **不许自己看 diff 省事**——那会烧掉协调用的上下文；下游接 `finishing-a-development-branch` |
| `receiving-code-review` | 「reviewer 让我改 1-6 条」「这条意见我觉得是错的」 | 逐条核实后再改，不合理的技术性顶回去 | **禁止说「You're absolutely right」这类表演式附和**；一次只改一条，各自测试 |
| `using-git-worktrees` | 「开个独立分支干活，别动我现在这份代码」「用 worktree 隔离一下」 | 隔离工作区，装好依赖、跑通基线测试并报告 | **有原生 `EnterWorktree` 工具时手搓 `git worktree add` 是头号错误**（会产生 harness 看不见的幽灵状态）；项目内目录要先 `git check-ignore` 确认被忽略 |
| `finishing-a-development-branch` | 「做完了，怎么收」「合回主干还是发 PR」「这个分支怎么办」 | 跑全量测试 → 三选一菜单（本地合并 / 开 PR / 原样保留）→ 按你选的执行并清理 | 上游 `executing-plans` 或 `subagent-driven-development`；**测试红了菜单根本不出现**；只有你亲口打 `discard` 才允许删 |
| `using-superpowers` | **会话里任何一句话**（自举入口） | 先判定该调哪个技能，声明「Using [skill] to [purpose]」 | 流程类技能优先（`brainstorming`、`systematic-debugging`），再让实现类落地；被派去干活的子 agent 忽略它 |
| `/code-review`（命令） | 打 `/code-review <PR号>`，或「review 一下这个 PR」「看看 #123」 | 5 个并行 agent 从五个角度审 → 打分 → 用 `gh` 评论回 PR | 只审 GitHub PR，**不审本地未推送的 diff**；**置信分 < 80 的意见会被全部过滤掉，可能什么都不发** |
| `mcp-builder` | 「给这个 API 写个 MCP server」「把 XX 服务封装成 MCP」 | 可用的 MCP server + 实现指南 + 10 道评测题 | 跟 superpowers 流水线无强绑定；官方推荐 TypeScript + streamable HTTP；工具命名要带统一前缀（如 `github_create_issue`） |
| `webapp-testing` | 「测一下本地这个前端页面」「截个图看看渲染」「验证下登录流程能不能走通」 | Playwright 脚本 → 截图、DOM 选择器、控制台日志、验证结果 | 动态应用**必须先 `wait_for_load_state('networkidle')`**，否则抓到半渲染状态；`scripts/` 当黑盒用别读源码（会烧光上下文） |

---

## 桶三 · 视觉 & 前端（8）

| 技能 | 什么信号让它启动 | 你会拿到什么 | 跟谁搭 / 坑 |
|---|---|---|---|
| `frontend-design` | 「做个有新意的界面」「这页面太模板感了 / 一眼 AI 味」「帮我定视觉方向、选字体配色」 | 设计计划（具名 hex 色板 + 字体角色 + ASCII 线框）→ 按它写 UI 代码 | 只给指导、**不产成品文件**；SKILL 里点名要避开的 AI 套路：奶油底 + 陶土橙、近黑底 + 单一酸绿、SaaS 卡片墙、全大写 eyebrow 标签 |
| `theme-factory` | 「给这套幻灯片换个主题 / 配色」「有现成的主题模板吗」「这套 deck 想要统一风格」 | 从 10 套预设主题（Ocean Depths、Sunset Boulevard…）选一套，或现场生成新主题 | **流程写死：必须先给你看 `theme-showcase.pdf`、等你明确选定才能动手**，不许替你选；自定义主题也要先给你 review |
| `brand-guidelines` | 「用 Anthropic 那套品牌色」「按公司 VI 来」「这份 PPT 要符合公司视觉标准」 | 品牌常量（`#141413`/`#faf9f5`/橙 `#d97757`/蓝 `#6a9bcc`/绿 `#788c5d`，标题 Poppins、正文 Lora）刷到已有产物上 | 搭 `theme-factory`；它**本身不生成新文件**，只是往已有产物上刷装；Poppins/Lora 没预装会回退 Arial/Georgia |
| `canvas-design` | 「做张海报」「设计一张封面」「要能进美术馆那种质感的单页视觉」 | `.pdf` 或 `.png` 单页视觉 + 一份 `.md` 设计哲学 | 与 `algorithmic-art` 同一套「先哲学后实现」流程；**只允许输出 `.md`/`.pdf`/`.png`**；**文字必须极简，不许溢出画布也不许重叠** |
| `algorithmic-art` | 「用代码画点生成艺术」「做个流场 / 粒子系统」「用 p5.js 画个会动的东西」 | 算法哲学 `.md` + 自包含 HTML 交互作品（带 seed 导航、参数滑块、PNG 下载） | **必须先 Read `templates/viewer.html` 照抄结构**，不许从零写 HTML、不许自创配色；p5.js 走 CDN 需联网 |
| `web-artifacts-builder` | 「做个带状态 / 路由的复杂 artifact」「React + Tailwind + shadcn/ui 做个页面」「别给我那种简陋的单文件 HTML」 | 自包含 `bundle.html`（React 18 + TS + Vite + Tailwind + shadcn/ui 全量内联） | 简单单文件 HTML **别用它**；要 Node 18+ 和 bash，初始化会装 40+ 组件需联网；明确要求避开「AI slop」（过度居中、紫色渐变、统一圆角、Inter 字体） |
| `playground` | 「做个 playground 让我调参数」「给我个能拖拖看的调参小工具」「这堆选项文字说不清，让我自己试试」 | 单文件 HTML：左控件 + 右实时预览 + 底部可复制的自然语言 prompt | **产物常常是喂回给 Claude 的 prompt，而不是最终作品**；必须单文件零外部依赖；无 Apply 按钮，改动即时重渲染 |
| `slack-gif-creator` | 「做个 Slack 用的 GIF」「做个 128×128 的 emoji 动图」「把这张图变成会动的表情包」 | Slack 规格 `.gif`（emoji 128×128 / 消息 480×480） | 需 `pip install pillow imageio numpy`；**不能用 emoji 字体**（跨平台不可靠），图形得用 PIL 原语自己画 |

---

## 桶四 · 改造 Claude 自己（4）

| 技能 | 什么信号让它启动 | 你会拿到什么 | 跟谁搭 / 坑 |
|---|---|---|---|
| `claude-md-improver` | 「帮我审一下 CLAUDE.md」「检查我的 CLAUDE.md 是不是过期了」「这仓库的 CLAUDE.md 该更新了吧」 | 全仓扫描 → 逐文件 A–F 加权打分 + 问题清单 + 补充建议 | **它会真的写 CLAUDE.md**——但先出报告、必须你批准才动手；管「和代码库对齐」（定期体检） |
| `/revise-claude-md`（命令） | 打 `/revise-claude-md`，或「把这次学到的东西记到 CLAUDE.md 里」「刚摸清的命令存下来」 | 复盘当前会话 → 几条一行式补充建议（diff + 一句 why），你批准后只改你点头的文件 | 管「会话沉淀」，跟上面那个别混用；轻量场景直接用内置 `#` 快捷键更快 |
| `skill-creator` | 「把刚才那套流程存成技能」「我想从零写个技能」「这技能怎么老不触发，优化下 description」「跑个评测看它到底行不行」 | `SKILL.md` + `evals/evals.json` + 带/不带技能的并行对照 + benchmark（通过率、耗时、token）+ 浏览器评测页 | 是**工具链**（评测、benchmark、触发调优、打包）；`grading.json` 字段名必须严格用 `text`/`passed`/`evidence`，否则 viewer 读不了 |
| `writing-skills` | 「我要写个新技能」「这技能到底管不管用、怎么验证它会生效」「怎么让 agent 别绕过规则、别找借口」 | TDD 式闭环：先跑无技能基线（**逐字记录 agent 的借口**）→ 写最小技能 → 带技能复跑 → 堵漏洞 | **前置依赖：必须先懂 `test-driven-development`**；铁律 NO SKILL WITHOUT A FAILING TEST FIRST；与 `skill-creator` 互补不重复——这个管「该写什么、凭什么叫它对」，那个管「怎么量、怎么打包」 |

---

## 下一步：挑 2-3 个实操

地图看完了，从里面挑你真想掌握的，我们跑通。我的建议顺序：

1. **`internal-comms`** —— 你原本就想找的那个。本机没接 Slack / Google Drive 这类数据源，**正好能练「它抓不到料时怎么问你要」这个环节**
2. **`docx` 或 `pdf`** —— 你本机 PDF 工具链已经装齐（pymupdf / pdfplumber / pypdf / reportlab），上手就有产出
3. **`brainstorming`** —— 我们这会儿正在走它，回头看一眼就懂它为什么这么烦人（硬门禁、不许跳步）

> 第二步开跑之前，先把上面那三个坑过一遍。尤其是**坑一**：你要做的是「把话说对」，不是「找到按钮」。
