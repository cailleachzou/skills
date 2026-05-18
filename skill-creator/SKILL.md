---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, update or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
---

# 技能创建器

用于创建新技能并对其进行迭代改进的技能。

从高层视角来看，创建技能的过程如下：

- 明确技能的目标和大致实现方式
- 起草技能初稿
- 创建几个测试提示词，并在 claude-with-access-to-the-skill 上运行
- 帮助用户对结果进行定性和定量评估
  - 在运行期间，在后台起草一些定量评估（如果没有的话；如已有，可以直接使用或按需修改）。然后向用户解释这些评估（如已存在，则解释已有的评估）
  - 使用 `eval-viewer/generate_review.py` 脚本向用户展示结果，同时让他们查看定量指标
- 根据用户对结果的评估反馈重写技能（如定量基准测试中出现明显缺陷，也要一并修正）
- 重复上述步骤直至满意
- 扩大测试集，在更大规模上再次尝试

使用此技能时，你的工作是判断用户处于流程的哪个阶段，然后介入帮助他们推进各阶段。例如，用户说"我想做一个用于 X 的技能"。你可以帮助他细化需求、起草初稿、编写测试用例、确定评估方式、运行所有提示词，并反复迭代。

另一方面，如果用户已经有了初稿，则可以直接进入评估/迭代环节。

当然，要始终保持灵活性——如果用户说"不需要跑一堆评估，就这样聊聊吧"，那也可以。

技能完成后（如前所述，顺序是灵活的），还可以运行技能描述优化器（我们有专门的脚本）来优化技能的触发机制。

准备好了？那就开始吧。

## 与用户沟通

技能创建器可能被对编程术语熟悉程度差异很大的用户使用。如果你没听说过（你怎么可能听说过呢，毕竟这只是最近才兴起的趋势），现在的趋势是：Claude 的强大能力激发了水管工打开终端、父母祖父母去 Google"怎么安装 npm"。另一方面，大多数用户可能对计算机比较熟悉。

所以请注意上下文线索，理解如何措辞！举一个默认情况的例子：

- "evaluation"和"benchmark"是边界情况，但可以接受
- 对于"JSON"和"assertion"，只有在用户明确表现出对这些术语有所了解时才可以在不解释的情况下使用

如有疑问可以简要解释术语，如果不确定用户是否能理解，可以简短地澄清一下。

---

## 创建技能

### 需求捕获

首先理解用户的意图。当前对话可能已经包含了用户想要捕获的工作流程（例如，用户说"把这个变成一个技能"）。如果是，先从对话历史中提取答案——用到的工具、步骤顺序、用户的修正、观察到的输入/输出格式。用户可能需要补充空白，并在进入下一步前确认。

1. 此技能应该让 Claude 具备什么能力？
2. 此技能何时触发？（用户的哪些措辞/上下文）
3. 期望的输出格式是什么？
4. 是否需要设置测试用例来验证技能可用？具有客观可验证输出的技能（文件转换、数据提取、代码生成、固定工作流程步骤）受益于测试用例。具有主观输出的技能（写作风格、艺术）通常不需要。根据技能类型推荐适当的默认方案，但最终由用户决定。

### 调研与访谈

主动询问边缘案例、输入/输出格式、示例文件、成功标准及依赖项。等这部分敲定了再写测试提示词。

检查可用的 MCP——如果对研究有帮助（搜索文档、寻找类似技能、查阅最佳实践），如有子代理可用则并行研究，否则内联完成。带好上下文信息再与用户沟通，减少他们的负担。

### 编写 SKILL.md

根据用户访谈，填充以下组件：

- **name**：技能标识符
- **description**：何时触发、做什么。这是主要的触发机制——要同时包含技能的功能描述和具体使用场景。所有"何时使用"的信息都放在这里，不放在正文里。注意：目前 Claude 有"触发不足"的倾向——即在技能有用时没有调用它。为解决这个问题，请把技能描述写得稍微"激进"一些。例如，不要写"How to build a simple fast dashboard to display internal Anthropic data."，可以写"How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"
- **compatibility**：必需工具、依赖项（可选，一般很少需要）
- **其余内容 :)**

### 技能写作指南

#### 技能的结构

```
skill-name/
├── SKILL.md（必需）
│   ├── YAML frontmatter（name、description 为必需字段）
│   └── Markdown 指令
└── 捆绑资源（可选）
    ├── scripts/    - 用于确定性/重复性任务的可执行代码
    ├── references/ - 按需加载到上下文中作为参考的文档
    └── assets/     - 输出中使用的文件（模板、图标、字体）
```

#### 渐进式披露

技能使用三级加载系统：
1. **元数据**（name + description）——始终在上下文中（约 100 词）
2. **SKILL.md 正文**——技能触发时在上下文中（理想情况 < 500 行）
3. **捆绑资源**——按需加载（无限制，脚本可在不加载的情况下执行）

这些字数是近似值，如需要可以超出。

**关键模式：**
- SKILL.md 控制在 500 行以内；如接近此限制，添加额外的层级结构，并清晰指出模型在跟进时应去哪里继续。
- 在 SKILL.md 中清晰引用文件，并说明何时应读取它们。
- 对于大型参考文件（> 300 行），包含目录表。

**领域组织**：当技能支持多个领域/框架时，按变体组织：
```
cloud-deploy/
├── SKILL.md（工作流 + 选择逻辑）
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Claude 只读取相关的参考文件。

#### 零意外原则

不言自明，但技能不得包含恶意软件、漏洞利用代码或任何可能危及系统安全的内容。技能的内容不应在意图上让用户感到意外。不要配合创建误导性技能或旨在协助未经授权访问、数据泄露或其他恶意活动的技能。不过，像"扮演 XYZ"这样的角色扮演是可以的。

#### 写作模式

指令中优先使用祈使句。

**定义输出格式**——可以这样写：
```markdown
## 报告结构
始终使用此确切模板：
# [标题]
## 执行摘要
## 关键发现
## 建议
```

**示例模式**——包含示例很有用。可以这样格式化（但如果示例中有"输入"和"输出"，你可能需要稍微调整一下格式）：
```markdown
## 提交信息格式
**示例 1：**
输入：Added user authentication with JWT tokens
输出：feat(auth): implement JWT-based authentication
```

### 写作风格

尽量向模型解释为什么某些东西是重要的，而不是用沉重的"必须""不得"的指令。利用心理理论，使技能具有通用性，不要过于狭窄地针对特定示例。先写一份初稿，然后用新鲜的眼光审视并改进。

### 测试用例

写完技能初稿后，想出 2-3 个现实的测试提示词——用户实际会说出的那种。与用户分享：[不一定用原话]"这里是我想尝试的几个测试用例。看起来对吗？要不要再添加一些？"然后运行它们。

将测试用例保存到 `evals/evals.json`。先不写断言——只有提示词。等运行开始后，在下一步起草断言。

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "用户的任务提示词",
      "expected_output": "预期结果描述",
      "files": []
    }
  ]
}
```

完整的 schema 参见 `references/schemas.md`（包含稍后要添加的 `assertions` 字段）。

## 运行和评估测试用例

本节是一个连续的流程——不要中途停止。不要使用 `/skill-test` 或任何其他测试技能。

将结果放入技能目录同级的 `<skill-name>-workspace/` 中。在工作空间内，按迭代组织结果（`iteration-1/`、`iteration-2/` 等），每个测试用例在迭代目录下有自己的目录（`eval-0/`、`eval-1/` 等）。不要预先创建全部——边走边创建目录。

### 步骤 1：在同一轮中启动所有运行（带技能 AND 基线）

对于每个测试用例，在同一轮中启动两个子代理——一个带技能，一个不带。这很重要：不要先启动带技能的运行，然后再来做基线。一次全部启动，这样它们几乎同时完成。

**带技能运行：**

```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what the user cares about — e.g., "the .docx file", "the final CSV">
```

**基线运行**（相同提示词，但基线取决于上下文）：
- **创建新技能**：完全不用技能。相同提示词，无技能路径，保存到 `without_skill/outputs/`。
- **改进现有技能**：旧版本。编辑前先给技能打快照（`cp -r <skill-path> <workspace>/skill-snapshot/`），然后让基线子代理指向快照目录。保存到 `old_skill/outputs/`。

为每个测试用例编写 `eval_metadata.json`（断言可以暂时为空）。给每个评估起一个描述性名称，基于它所测试的内容——不要只是"eval-0"。目录也用这个名称。如果本次迭代使用了新的或修改过的评估提示词，为每个新的评估目录创建这些文件——不要假设它们会从上一次迭代继承过来。

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "用户的任务提示词",
  "assertions": []
}
```

### 步骤 2：运行期间起草断言

不要只是等待运行完成——这段时间可以有效利用。为每个测试用例起草定量断言，并向用户解释。如果 `evals/evals.json` 中已有断言，审查它们并解释它们在检查什么。

好的断言是客观可验证的，且有描述性名称——它们在基准查看器中应该清晰可读，这样有人扫一眼结果就能立即理解每个断言在检查什么。主观性技能（写作风格、设计质量）更适合定性评估——不要把需要人工判断的东西强行加上断言。

起草完成后，更新 `eval_metadata.json` 文件和 `evals/evals.json` 中的断言。同时向用户解释他们在查看器中会看到什么——包括定性输出和定量基准。

### 步骤 3：运行完成时捕获计时数据

每个子代理任务完成时，你会收到包含 `total_tokens` 和 `duration_ms` 的通知。立即将此数据保存到运行目录的 `timing.json` 中：

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

这是捕获这些数据的唯一机会——它通过任务通知传递，不会保存在其他地方。收到每个通知就立即处理，不要试图批量处理。

### 步骤 4：评分、汇总，并启动查看器

所有运行完成后：

1. **每个运行评分**——启动评分子代理（或内联评分），读取 `agents/grader.md`，对每个断言对照输出进行评估。将结果保存到每个运行目录的 `grading.json`。grading.json 的 expectations 数组必须使用 `text`、`passed` 和 `evidence` 字段（不是 `name`/`met`/`details` 或其他变体）——查看器依赖这些确切的字段名。对于可以编程检查的断言，编写并运行脚本而不是肉眼判断——脚本更快、更可靠，且可以在迭代间复用。

2. **汇总为基准**——从 skill-creator 目录运行汇总脚本：
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   这会生成 `benchmark.json` 和 `benchmark.md`，包含每个配置项的 pass_rate、时间和 token，附有 mean ± stddev 和 delta。如需手动生成 benchmark.json，参见 `references/schemas.md` 了解查看器期望的确切 schema。
   将每个 with_skill 版本放在对应的基线版本之前。

3. **做一轮分析**——阅读基准数据，找出汇总统计可能隐藏的模式。参见 `agents/analyzer.md`（"分析基准结果"一节）了解需要关注的内容——比如那些无论是否使用技能都总是通过的断言（无区分度）、高方差的评估（可能不稳定）以及时间/token 的权衡。

4. **启动查看器**，同时展示定性输出和定量数据：
   ```bash
   nohup python <skill-creator-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   第二次迭代起，还需要传入 `--previous-workspace <workspace>/iteration-<N-1>`。

   **Cowork / 无头环境：** 如果 `webbrowser.open()` 不可用或环境没有显示器，使用 `--static <output_path>` 写入独立的 HTML 文件而非启动服务器。用户点击"提交所有评论"后，反馈将下载为 `feedback.json` 文件。下载后将 `feedback.json` 复制到工作空间目录，以便下次迭代拾取。

   注意：请使用 generate_review.py 创建查看器，无需编写自定义 HTML。

5. **告知用户**类似这样的话："我已在浏览器中打开了结果。有两个标签页——'输出'让你逐个点击测试用例并留下反馈，'基准'显示定量对比。完成后回来告诉我。"

### 用户在查看器中看到的内容

"输出"标签每次显示一个测试用例：
- **提示词**：给出的任务
- **输出**：技能生成的文件，尽可能以内联方式渲染
- **上一次输出**（第二次迭代+）：折叠区域，显示上一次迭代的输出
- **正式评分**（如运行了评分）：折叠区域，显示断言通过/失败情况
- **反馈**：自动保存的文本框
- **上一次反馈**（第二次迭代+）：他们上次的评论，显示在文本框下方

"基准"标签显示统计摘要：每个配置的通过率、时间、token 使用量，以及每个评估的细分和分析师观察。

通过 prev/next 按钮或方向键导航。完成后，点击"提交所有评论"将所有反馈保存到 `feedback.json`。

### 步骤 5：阅读反馈

用户告诉你完成后，读取 `feedback.json`：

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "图表缺少坐标轴标签", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."},
    {"run_id": "eval-2-with_skill", "feedback": "完美，喜欢", "timestamp": "..."}
  ],
  "status": "complete"
}
```

空反馈意味着用户认为没问题。将改进重点放在用户有具体抱怨的测试用例上。

完成后杀死查看器服务器：

```bash
kill $VIEWER_PID 2>/dev/null
```

---

## 改进技能

这是循环的核心。你已经运行了测试用例，用户也审查了结果，现在需要根据他们的反馈让技能变得更好。

### 如何思考改进

1. **从反馈中归纳 generalization。** 这里发生的大局是：我们试图创建可以重复使用一百万次（也许字面上是，甚至更多）的技能，跨无数不同的提示词。这里你和用户只在几个例子上反复迭代，因为这样更快。用户对这些例子了如指掌，评估新输出对他们来说很快。但如果你们协作开发的技能只适用于那些例子，那它就毫无用处。与其做些花哨的容易过拟合的改动，或者设置压抑性的、限制性强的"必须"规则，不如另辟蹊径——尝试不同的比喻，或推荐不同的工作模式。尝试成本很低，也许能找到很棒的方案。

2. **保持提示词精简。** 删除那些不出力的部分。务必阅读 transcripts，不只是最终输出——如果看起来技能让模型浪费大量时间做无产出的事，可以尝试删掉让模型做那些事的技能部分，然后看效果。

3. **解释为什么。** 努力解释你要求的每件事背后的**原因**。今天的 LLM 很聪明。它们有很好的心理理论，当给了一个好的框架时可以超越死板指令，真正把事情做成。即使用户的反馈简短或急躁，也要试着真正理解任务、理解用户为什么写他们写的东西、理解他们实际写了什么，然后把这种理解传递到指令中。如果你发现自己写了全大写的"总是"或"绝不"，或者使用超级僵硬的结构，那是黄旗信号——如果可能，重构并解释原因，让模型理解你要求的事情为什么重要。这是一种更人性化、更有力、更有效的方法。

4. **寻找跨测试用例的重复工作。** 阅读测试运行的 transcripts，注意子代理是否都独立写了相似的辅助脚本或对某事物采取了相同的多步骤方法。如果 3 个测试用例都导致子代理写了 `create_docx.py` 或 `build_chart.py`，这是强烈信号，表明技能应该捆绑那个脚本。写一次，放到 `scripts/`，然后告诉技能使用它。这为每次未来的调用省去了重复造轮子。

这个任务相当重要（我们正在这里创造每年数十亿美元的经济价值！），你的思考时间不是瓶颈——慢慢来，仔细琢磨。我的建议是写一份修订草案，然后用新的眼光审视并改进。真的尽你所能进入用户的头脑，理解他们想要什么、需要什么。

### 迭代循环

改进技能后：

1. 将改进应用到技能上
2. 将所有测试用例重新运行到新的 `iteration-<N+1>/` 目录，包括基线运行。如果是创建新技能，基线始终是 `without_skill`（无技能）——跨迭代保持不变。如果是改进现有技能，自行判断以什么作为基线有意义：用户最初带来的原始版本，还是上一次迭代。
3. 启动审查器，加上 `--previous-workspace` 指向上一次迭代
4. 等待用户审查并告知完成
5. 读取新反馈，再次改进，重复

继续直到：
- 用户表示满意
- 反馈全部为空（一切看起来都很好）
- 没有取得有意义的进展

---

## 高级：盲对比

对于需要更严格比较两个技能版本的情况（例如，用户问"新版本真的更好吗？"），有一个盲对比系统。阅读 `agents/comparator.md` 和 `agents/analyzer.md` 了解详情。基本思路是：将两个输出交给一个独立代理，不告诉它哪个是哪个，让它评判质量。然后分析获胜者为什么赢。

这是可选的，需要子代理，大多数用户不需要。人工审查循环通常足够。

---

## 描述优化

SKILL.md frontmatter 中的 description 字段是决定 Claude 是否调用技能的主要机制。创建或改进技能后，主动提出优化描述以获得更好的触发准确性。

### 步骤 1：生成触发评估查询

创建 20 个评估查询——混合应该触发和不应该触发的类型。保存为 JSON：

```json
[
  {"query": "用户的提示词", "should_trigger": true},
  {"query": "另一个提示词", "should_trigger": false}
]
```

这些查询必须真实可信，是 Claude Code 或 Claude.ai 用户实际会输入的内容。不是抽象的请求，而是具体、详细、真实的请求。比如文件路径、个人工作背景或处境、列名和值、公司名、URL 等。加上一些背景故事。有的可以是 lowercase 或包含缩写、拼写错误、口语化表达。长度要有变化，关注边缘案例而非显而易见的区分（用户会有机会审核确认）。

差的例子：`"Format this data"`、`"Extract text from PDF"`、`"Create a chart"`

好的例子：`"ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage. The revenue is in column C and costs are in column D i think"`

对于**应该触发**的查询（8-10 个），考虑覆盖率。需要同一意图的不同措辞——有的正式，有的随意。包括用户没有明确命名技能或文件类型但明显需要它的情况。加入一些不常见的用例，以及此技能与其他技能竞争但应该获胜的情况。

对于**不应该触发**的查询（8-10 个），最有价值的是"差一点就触发"的查询——那些共享关键词或概念但实际需要不同东西的查询。考虑相邻领域、模糊措辞（朴素关键词匹配会触发但不应该），以及查询涉及技能功能但在另一个工具更合适的场景。

需要避免的关键问题：不要让不应该触发的查询明显无关。"Write a fibonacci function" 作为 PDF 技能的负面测试太简单——什么都测试不出来。负面案例应该真正具有挑战性。

### 步骤 2：与用户一起审核

使用 HTML 模板向用户展示评估集进行审核：

1. 从 `assets/eval_review.html` 读取模板
2. 替换占位符：
   - `__EVAL_DATA_PLACEHOLDER__` → JSON 数组（不加引号——它是 JS 变量赋值）
   - `__SKILL_NAME_PLACEHOLDER__` → 技能名称
   - `__SKILL_DESCRIPTION_PLACEHOLDER__` → 技能当前描述
3. 写入临时文件（例如 `/tmp/eval_review_<skill-name>.html`）并打开：`open /tmp/eval_review_<skill-name>.html`
4. 用户可以编辑查询、切换 should-trigger、添加/删除条目，然后点击"导出评估集"
5. 文件下载到 `~/Downloads/eval_set.json`——检查下载文件夹中的最新版本（可能有多个，例如 `eval_set (1).json`）

这一步很重要——糟糕的评估查询会导致糟糕的描述。

### 步骤 3：运行优化循环

告诉用户："这需要一些时间——我将在后台运行优化循环，并定期检查进度。"

将评估集保存到工作空间，然后在后台运行：

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

使用系统提示词中的模型 ID（为当前会话提供支持的那个），这样触发测试就与用户实际体验一致。

运行时，定期 tail 输出，给用户更新迭代进度和分数情况。

这自动处理完整的优化循环。它将评估集分成 60% 训练集和 40% 保留测试集，评估当前描述（每个查询运行 3 次以获得可靠的触发率），然后调用 Claude 进行扩展思考，根据失败情况提出改进。它在训练集和测试集上重新评估每个新描述，迭代最多 5 次。完成后，在浏览器中打开 HTML 报告，显示每次迭代的结果，并返回包含 `best_description` 的 JSON——按测试分数而非训练分数选择，以避免过拟合。

### 技能触发原理

理解触发机制有助于设计更好的评估查询。技能以 name + description 出现在 Claude 的 `available_skills` 列表中，Claude 根据该描述决定是否需要咨询技能。需要知道的关键点是：Claude 只在无法独立轻松处理的任务时才会咨询技能——简单、一步到位的查询（如"读取这个 PDF"）可能不会触发技能，即使描述完全匹配，因为 Claude 可以用基本工具直接处理。复杂、多步骤或专业化的查询，当描述匹配时，会可靠地触发技能。

这意味着你的评估查询应该足够实质，让 Claude 真正受益于咨询技能。简单的查询如"读取文件 X"不是好的测试用例——无论描述质量如何，它们都不会触发技能。

### 步骤 4：应用结果

从 JSON 输出中取出 `best_description`，更新技能的 SKILL.md frontmatter。向用户展示前后的变化并报告分数。

---

### 打包与呈现（仅在 `present_files` 工具可用时）

检查是否有 `present_files` 工具的访问权限。如果没有，跳过此步骤。如果有，打包技能并将 .skill 文件呈现给用户：

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

打包后，将生成的 .skill 文件路径告诉用户，以便安装。

---

## Claude.ai 特定说明

在 Claude.ai 中，核心工作流程相同（起草 → 测试 → 审核 → 改进 → 重复），但因为 Claude.ai 没有子代理，某些机制有所不同。以下是需要调整的地方：

**运行测试用例**：没有子代理意味着无法并行执行。对于每个测试用例，阅读技能的 SKILL.md，然后按照其指令完成测试提示词。逐一进行。这比独立子代理（你写了技能又自己运行，拥有完整上下文）缺乏严谨性，但它是有效的合理性检查——人工审核步骤可以弥补。跳过基线运行——只用技能按要求完成任务。

**审查结果**：如果无法打开浏览器（例如 Claude.ai 的 VM 没有显示器，或者你在远程服务器上），完全跳过浏览器审查器。直接在对话中呈现结果。对于每个测试用例，展示提示词和输出。如果输出是用户需要查看的文件（如 .docx 或 .xlsx），保存到文件系统并告诉用户文件位置，以便他们下载检查。inline 征求反馈："看起来怎么样？有什么想改的吗？"

**基准测试**：跳过定量基准测试——它依赖于在没有子代理的情况下没有意义的基线比较。专注于用户的定性反馈。

**迭代循环**：与之前相同——改进技能，重新运行测试用例，征求反馈——只是中间没有浏览器审查器。如果你有文件系统，仍然可以将结果组织到迭代目录中。

**描述优化**：此部分需要 `claude` CLI 工具（具体是 `claude -p`），仅在 Claude Code 中可用。在 Claude.ai 上跳过。

**盲对比**：需要子代理。跳过。

**打包**：`package_skill.py` 脚本在任何有 Python 和文件系统的环境中都可以运行。在 Claude.ai 上你可以运行它，用户可以下载生成的 .skill 文件。

---

## Cowork 特定说明

如果在 Cowork 中，需要知道的主要事项是：

- 你有子代理，所以主要工作流程（并行启动测试用例、运行基线、评分等）都能正常工作。（不过，如果遇到严重的超时问题，串行运行测试提示词也是可以的。）
- 你没有浏览器或显示器，所以在生成评估查看器时，使用 `--static <output_path>` 写入独立的 HTML 文件而非启动服务器。然后提供一个链接，用户可以点击在浏览器中打开 HTML。
- 不知为何，Cowork 配置似乎不太倾向于让 Claude 在运行测试后生成评估查看器，所以再次强调：无论你在 Cowork 还是 Claude Code 中，运行测试后都应始终生成评估查看器，让人类在你自己评估输入之前尽快查看测试用例——使用 `generate_review.py`（不要自己写花哨的 HTML 代码）。提前道歉，但我还是要大写：**在评估输入之前生成评估查看器**！你要尽快让人工审阅这些案例！
- 反馈机制不同：由于没有运行中的服务器，查看器的"提交所有评论"按钮会将 `feedback.json` 下载为文件。然后你可以从这里读取（可能需要先请求访问权限）。
- 打包可以工作——`package_skill.py` 只需要 Python 和文件系统。
- 描述优化（`run_loop.py` / `run_eval.py`）在 Cowork 中应该可以正常工作，因为它通过子进程使用 `claude -p`，而非浏览器，但请等到技能完全完成且用户确认状态良好后再进行。

---

## 参考文件

agents/ 目录包含专门子代理的指令。需要生成相关子代理时阅读它们。

- `agents/grader.md` — 如何对照输出评估断言
- `agents/comparator.md` — 如何对两个输出进行盲 A/B 对比
- `agents/analyzer.md` — 如何分析一个版本为何胜出

references/ 目录有额外的文档：
- `references/schemas.md` — evals.json、grading.json 等的 JSON 结构

---

再重复一遍核心循环以示强调：

- 搞清楚技能要做什么
- 起草或修改技能
- 在测试提示词上运行 claude-with-access-to-the-skill
- 与用户一起评估输出：
  - 创建 benchmark.json 并运行 `eval-viewer/generate_review.py` 帮助用户审查
  - 运行定量评估
- 重复直到你和用户都满意
- 打包最终技能并返回给用户

如果你的任务列表中有这一项，请添加步骤以确保不忘。如果你在 Cowork 中，请特别将"创建 evals JSON 并运行 `eval-viewer/generate_review.py` 以便人工审查测试用例"放入任务列表以确保它会发生。

祝你好运！