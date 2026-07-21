---
name: tyc-it
description: 天眼查 CLI"天眼一下"（TYC It）商业查询入口。用于任何需要使用天眼查企业数据支撑的商业查询、企业信息查询、商业尽调、主体核验、合作方/客户/供应商评估、股权实控与关联关系、司法和行政风险、经营真实性、知识产权、人员背景、历史沿革、行业/园区/榜单发现、上市财务等问题；包括但不限于查公司、判断能否合作、识别关联关系、排查风险、发现行业企业、核验品牌/专利/投标机会等场景。
---

# 天眼一下

英文名：TYC It
建议唤起命令：`/tyc-it`

## 工具架构

`tyc` CLI 是天眼查 162 个商业数据工具的本地命令行入口，4 层渐进发现：

```
L0  实体锚定      1 个工具   简称 / 曾用名 / 模糊名 → 精确企业
L1  概要总览      6 个工具   每个 facet 1 个总览工具，返回 _summary
L2  维度下钻     57 个工具   股东、诉讼、商标、招投标、年报等明细维度
L3  专项工具     98 个工具   id 详情、search_*、垂直场景和专业查询
```

6 个分类组：`company`（49）· `risk`（35）· `intellectual_property`（14）· `operation`（32）· `history`（17）· `executive`（15）

推荐调用顺序：L0 锚定 → L1 总览 → L2 下钻 → L3 专项

## 触发条件

当用户提出宽泛或探索式商查问题，而不是已经指名某个专用 skill 时使用本 skill。

典型问题：

- "帮我查一下这家公司靠不靠谱"
- "这家公司能不能作为客户/供应商/合作方"
- "A 和 B 有没有关联关系"
- "某公司背后是谁控制的"
- "最近有没有诉讼、被执行、处罚或经营异常"
- "这家公司有没有真实经营、招投标、资质、招聘、客户供应商"
- "某品牌有没有商标风险，某技术方向有哪些专利公司"
- "找一下某行业/某地区/某标签下的企业名单"
- "给我做一个商查摘要，不要太长"

若用户明确要求银行 KYB、投前尽调、法务合同主体审查、供应商年审等已存在专用场景，优先使用对应专用 skill；本 skill 作为通用路由和兜底。

## 输入要求

用户输入可能是单一企业、多个企业、自然语言线索或非公司检索目标。先识别输入形态，再决定是否需要 L0 锚定。

| 输入形式 | 示例 | 处理方式 |
|---|---|---|
| 完整企业名 | `北京字节跳动科技有限公司` | 可跳过候选确认，仍建议用 `tyc company companies` 核验主体 |
| USCC | `91110108551385082Q` | 直接作为精确主体，必要时反查企业名称 |
| 简称/品牌/曾用名/模糊名 | `字节`、`抖音`、`天眼查` | 必须用 `tyc company companies <query>` 消歧 |
| 两个以上主体 | `联洋国融和启赢互联` | 分别锚定，每个主体保留独立名称和 ID |
| 行业/地区/标签/榜单 | `上海 AI 公司`、`专精特新企业` | 使用搜索类入口形成候选名单，再对重点公司下钻 |
| 商标/专利/招投标关键词 | `底库商标`、`云计算中标机会` | 使用 `tyc intellectual_property trademarks`、`tyc intellectual_property patents`、`tyc operation bids` 等 |

实体锚定规则：

1. 若输入匹配 USCC 正则 `^[0-9A-Z]{18}$`，直接使用。
2. 若输入含 `有限公司`、`股份有限公司`、`集团`、`合伙企业`、`个体工商户`、`事务所`、`中心`、`分公司` 等组织形式且长度足够，优先按完整企业名处理。
3. 其他情况调用 `tyc company companies "<userInput>"`。过滤 `regStatus` 为 `存续`、`在业`、`在营`、`开业` 的候选，按相关性、注册资本、成立时间和用户语境排序，最多展示 5 个。
4. 候选为 1 个时可自动锚定；候选大于等于 2 个时暂停并请用户确认；候选为 0 时请用户提供更完整名称、USCC 或其他线索。

候选确认话术：

```markdown
你说的「{userInput}」匹配到多家企业，请确认是哪一家：

| # | 企业名称 | USCC | 状态 | 法定代表人 | 注册地 |
|---|---|---|---|---|---|
| 1 | ... | ... | 存续 | ... | ... |
| 2 | ... | ... | 存续 | ... | ... |

回复编号继续，或回复"都不是"重新输入。
```

## 意图分流

先把用户问题归入一个或多个商查意图。只调用回答问题所需的最小工具链，不要为了"全面"扫完所有维度。

| 意图 | 判断线索 | 优先工具链 |
|---|---|---|
| 主体画像 | 查一下、公司概况、背景、一页纸 | `tyc company companies` -> `tyc company registration-info`；必要时 `tyc company capabilities` -> 按需下钻 |
| 合作准入/风险初筛 | 靠不靠谱、能否合作、客户/供应商准入 | `tyc company registration-info` -> `tyc company capabilities` -> `tyc risk overview`、`tyc risk business-exception`、`tyc risk administrative-penalty`、`tyc risk judgment-debtor-info`、`tyc risk dishonest-info` |
| 股权实控/UBO | 背后是谁、控制人、受益人、股权穿透 | `tyc company equity-ratio` 或 `tyc company equity-tree` -> `tyc company capabilities` -> `tyc company shareholder-info`、`tyc company actual-controller`、`tyc company beneficial-owners`、`tyc company controlled-companies` |
| 关联关系 | 两家公司有没有关系、关联方、同一实控 | 分别 `tyc company companies` -> `tyc company relation-path`；再按需 `tyc company relation-graph`、`tyc company group-info`、`tyc company key-personnel` |
| 司法诉讼/执行 | 诉讼、裁判文书、开庭、被执行、限高 | `tyc company capabilities` -> `tyc risk overview`、`tyc risk judicial-case`、`tyc risk judicial-documents`、`tyc risk case-filing-info`、`tyc risk judgment-debtor-info`、`tyc risk dishonest-info`、`tyc risk high-consumption-restriction` |
| 行政/税务/ESG 合规 | 行政处罚、环保处罚、税收违法、严重违法 | `tyc company capabilities` -> `tyc risk administrative-penalty`、`tyc risk environmental-penalty`、`tyc risk tax-violation`、`tyc risk tax-arrears-notice`、`tyc risk serious-violation` |
| 经营真实性 | 真实经营、资质、招投标、招聘、客户供应商 | `tyc company registration-info` -> `tyc company capabilities` -> `tyc company scale`、`tyc operation qualifications`、`tyc operation bidding-info`、`tyc operation suppliers-and-customers`、`tyc operation recruitment-info`、`tyc operation products-info`、`tyc operation administrative-license` |
| 知产/品牌/技术 | 专利、商标、软著、品牌冲突、技术实力 | `tyc company capabilities` -> `tyc intellectual_property ipr-score`、`tyc intellectual_property patent-info`、`tyc intellectual_property trademark-info`、`tyc intellectual_property software-copyright-info`；关键词搜索用 `tyc intellectual_property trademarks`、`tyc intellectual_property patents` |
| 人员背景 | 法人/高管背景、任职、关联公司、个人风险 | `tyc company key-personnel` -> `tyc executive person-profile` 或 `tyc executive person-risk-overview`；必要时 `tyc executive personnel-positions`、`tyc executive personnel-related-companies` |
| 历史沿革 | 曾用名、股东变更、频繁变更、历史处罚 | `tyc company capabilities` -> `tyc history historical-overview`、`tyc history historical-registration`、`tyc history historical-shareholders`、`tyc history historical-investments`、`tyc company change-records`、`tyc company history-names` |
| 行业/名单发现 | 找公司、行业名单、园区、榜单、标签 | `tyc company companies-by-industry-region`、`tyc company companies-by-tag`、`tyc company companies-by-ranking`、`tyc company park-companies`；对候选 Top N 再画像 |
| 上市/财务 | 财务、利润表、资产负债、股本、公告、股票 | `tyc company capabilities` -> `tyc company financial-summary`、`tyc company financial-data`、`tyc company listing-info`、`tyc company income-statement`、`tyc company balance-sheet`、`tyc company cash-flow-statement`、`tyc company stock-shareholders` |

## 执行流程

### Step 1: 明确问题边界

从用户原话提取：

- `subject[]`：企业、个人、品牌、专利/商标/招投标关键词、行业/地区/标签。
- `intent[]`：使用上表归类，可多选。
- `depth`：快速摘要、标准商查、深度报告。
- `decision_context`：合作准入、销售拜访、授信、投前、法务、采购、竞品、市场拓展等。

若只有"查一下某公司"且没有决策语境，默认输出"主体画像 + 风险初筛 + 经营真实性 + 股权实控摘要"的轻量商查。

### Step 2: 锚定主体

对每个企业线索执行输入要求中的锚定规则。不要在候选不唯一时自行选第一条。完成锚定后，在内部记录：

```text
company_name = 候选表中的精确企业名称
company_id = 候选表中的 id
creditCode = 候选表中的 creditCode
```

### Step 3: 调用高密度公开入口

按问题选择公开入口：

- 单主体基础问题：优先 `tyc company registration-info "<company_name>"`。
- 集团/股权/关联粗看：优先 `tyc company equity-ratio` 或 `tyc company equity-tree`。
- 人员问题：先 `tyc company key-personnel`，再指定人员调用 `tyc executive person-profile` 或 `tyc executive person-risk-overview`。
- 行业/标签/榜单/园区名单：直接用对应 `tyc company companies-by-*` 入口形成候选清单。

如果公开画像已经足够回答，直接输出结论；不要为了形式继续下钻。

### Step 4: 能力发现与下钻

当用户问题需要具体维度时，调用 `tyc company capabilities <company_id> --company-name "<company_name>"`。从返回表格复制可执行的 CLI 命令，按意图分流表调用必要工具。

CLI 命令格式示例：

```bash
tyc risk judicial-case "字节跳动"
tyc company shareholder-info "字节跳动"
tyc intellectual_property trademark-info "字节跳动"
tyc operation bidding-info "字节跳动" --page 1 --page-size 10
```

列表型工具显式传 `--page`、`--page-size`，即使服务端有默认值。详情型工具先从上游列表拿 `id`、`regNo` 或其他编号，再单独调用详情工具。

### Step 5: 交叉验证和判断

把结论建立在至少两个维度的互证上：

- 主体真实性：工商登记、联系方式/地址、经营范围、成立年限、参保/分支/对外投资。
- 经营能力：招投标、客户供应商、资质许可、招聘、产品业务、荣誉榜单。
- 风险判断：风险总览与具体负面记录互证；重大结论不能只依据 `_summary`。
- 控制关系：股东、实控人、受益所有人、股权树、关系路径或集团画像互证。
- 知产能力：`tyc intellectual_property ipr-score` 与专利/商标/软著明细互证。

明确区分"已查无记录""工具未返回""未覆盖该维度"。不要把空结果写成绝对安全。

### Step 6: 输出

默认结论先行，再给证据和建议。除非用户要求，不输出冗长原始数据。

快速摘要模板：

```markdown
# 商查摘要：{company_name}

## 结论
{1-3 句话，回答用户问题}

## 关键信号
| 维度 | 发现 | 判断 |
|---|---|---|
| 主体 | ... | 通过/关注/异常 |
| 风险 | ... | 低/中/高 |
| 经营 | ... | 强/一般/弱 |
| 股权/关系 | ... | 清晰/需复核 |

## 建议
- {下一步动作 1}
- {需要人工复核的点 2}

## 数据来源
天眼查 CLI：{命令列表}
```

标准商查报告模板：

```markdown
# {company_name} 商查报告

> 用户问题：{user_question}
> 锚定主体：{company_name} / {creditCode}
> 数据来源：天眼查 CLI (tyc)

## 一、结论先行
- 综合判断：适合合作 / 谨慎合作 / 暂缓 / 需补充材料
- 风险等级：低 / 中 / 高
- 核心理由：...

## 二、主体与经营基础
| 字段 | 内容 |
|---|---|
| 经营状态 | ... |
| 法定代表人 | ... |
| 成立时间 | ... |
| 注册资本 | ... |
| 经营范围 | ... |
| 参保/分支/投资 | ... |

## 三、风险与合规
| 维度 | 数量/状态 | 重点说明 |
|---|---:|---|
| 司法诉讼 | ... | ... |
| 被执行/失信/限高 | ... | ... |
| 行政处罚/严重违法 | ... | ... |
| 经营异常/税务环保 | ... | ... |

## 四、股权与关联
- 股东结构：...
- 实际控制人/受益所有人：...
- 关联关系或集团链路：...

## 五、经营真实性
- 招投标/客户供应商：...
- 资质许可/荣誉：...
- 招聘/产品/舆情：...

## 六、待复核事项
- ...

## 七、调用链
`tyc company companies` -> `{tyc 命令列表}`
```

## 常用 CLI 命令速查

| 场景 | 命令 |
|---|---|
| 搜索企业 | `tyc company companies "关键词"` |
| 企业基础信息 | `tyc company registration-info "企业名"` |
| 企业能力发现 | `tyc company capabilities <id> --company-name "企业名"` |
| 风险总览 | `tyc risk overview "企业名"` |
| 股东信息 | `tyc company shareholder-info "企业名"` |
| 实际控制人 | `tyc company actual-controller "企业名"` |
| 司法案件 | `tyc risk judicial-case "企业名"` |
| 被执行人 | `tyc risk judgment-debtor-info "企业名"` |
| 失信信息 | `tyc risk dishonest-info "企业名"` |
| 行政处罚 | `tyc risk administrative-penalty "企业名"` |
| 招投标 | `tyc operation bidding-info "企业名"` |
| 商标信息 | `tyc intellectual_property trademark-info "企业名"` |
| 专利信息 | `tyc intellectual_property patent-info "企业名"` |
| 人员画像 | `tyc executive person-profile "人员名"` |
| 历史总览 | `tyc history historical-overview "企业名"` |
| 关联路径 | `tyc company relation-path "企业A" --target "企业B"` |

## 错误处理

- 候选企业不唯一：停止下钻，先让用户确认。
- 能力表没有目标工具：不要猜测工具名；换用公开画像、相关搜索入口或向用户说明该维度当前未开放。
- 命令返回未知错误：重新调用 `tyc company capabilities`，复制真实命令后重试一次。
- 列表工具为空：使用 `_empty` 和 `_summary` 说明"当前返回为空"，不要写成"永久无风险"。
- 多主体关系问题只锚定到其中一个主体时：先补齐另一个主体；关系判断不能只看单方画像。
- 用户要求法律、投资、授信等最终决策时：给出数据驱动建议，并提示仍需结合合同、财务报表、现场访谈或专业意见。

## 示例

### 示例 1：合作方初筛

用户：`帮我看看北京百度网讯科技有限公司能不能作为合作方`

流程：
```bash
tyc company companies "北京百度网讯科技有限公司"
tyc company registration-info "北京百度网讯科技有限公司"
tyc company capabilities <company_id> --company-name "北京百度网讯科技有限公司"
tyc risk overview "北京百度网讯科技有限公司"
tyc risk business-exception "北京百度网讯科技有限公司"
tyc risk administrative-penalty "北京百度网讯科技有限公司"
tyc risk judgment-debtor-info "北京百度网讯科技有限公司"
tyc operation bidding-info "北京百度网讯科技有限公司"
tyc operation qualifications "北京百度网讯科技有限公司"
```

输出：合作建议、主体基础、负面风险、经营能力、待复核材料。

### 示例 2：关联关系

用户：`联洋国融和启赢互联有没有关联关系`

流程：
```bash
tyc company companies "联洋国融"
tyc company companies "启赢互联"
tyc company relation-path "联洋国融" --target "启赢互联"
# 按需补：
tyc company relation-graph "联洋国融"
tyc company group-info "联洋国融"
```

输出：是否有关联、最短路径、共同股东/高管/投资关系、证据链和置信度。

### 示例 3：行业发现

用户：`找一下上海人工智能行业里比较活跃的公司`

流程：
```bash
tyc company companies-by-industry-region "人工智能" --region "上海"
# 选 Top 10 后：
tyc company registration-info "候选企业名"
tyc operation bidding-info "候选企业名"
tyc intellectual_property ipr-score "候选企业名"
tyc operation news-sentiment "候选企业名"
```

输出：候选企业清单、筛选口径、活跃度信号、推荐跟进对象。
