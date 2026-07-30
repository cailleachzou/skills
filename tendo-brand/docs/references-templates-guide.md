# Tendo references/ 模板参考文档

> 维护说明：新增模板/agent 时同步更新本文档。SKILL.md 的 agents 触发表以 SKILL.md 为准。

## 1. 概述

### 目的
作为 `SKILL.md` 的补充参考文档，系统记录 `references/` 每个模板的技术细节。当需要新增/修改 agent 或理解模板结构时，不必重新打开二进制文件。

### 范围
`references/` 中 7 个 docx/xlsx 模板：

| 序号 | 模板名 | 类型 |
|------|--------|------|
| 1 | TendoCN - Q&A for (Client Name) (Project Name) - (Date).xlsx | xlsx |
| 2 | TendoCN - Worker Name List.xlsx | xlsx |
| 3 | SBY - 每周项目状态报告 (中文).docx | docx |
| 4 | TendoCN - Cooley LLP - Cooley Shanghai Meeting Room Retrofit - Weekly Progress Report (项目周报) .xlsx | xlsx |
| 5 | TCMR2603-00005- Material Requisition - TCSO2603-00085.xlsx | xlsx |
| 6 | Service Report.xlsx | xlsx |
| 7 | TendoCN - Test Procedure.docx | docx |

**不含** 4 个非模板文件：`header_only.png`、`Screenshot 2026-07-15 133109.png`、`md2pdf-config.js`、`tendo-style.css`。

---

## 2. 模板速查总表

按业务流程排序：勘察 → 施工 → 交付。

| 模板名 | 类型 | 用途 | 对应 agent | 已有 spec | 说明深度 |
|--------|------|------|-----------|----------|---------|
| Q&A for (Client) (Project) - (Date).xlsx | xlsx | 现场勘察澄清表 | qa-sheet.md | 无 | 读 agent + 补结构 |
| Worker Name List.xlsx | xlsx | 项目人员名单 | worker-list.md | 无 | 读 agent + 补结构 |
| 每周项目状态报告 (中文).docx | docx | 中文周报（Word 版） | weekly-status-report.md | 无 | 读 agent + 补结构 |
| Weekly Progress Report (项目周报).xlsx | xlsx | 英文周报（Excel 版） | weekly-report.md + 3 subagents | 有 | 复用现有 spec |
| Material Requisition.xlsx | xlsx | 出库单 | delivery-order.md | 有 | 复用现有 spec |
| Service Report.xlsx | xlsx | 服务报告 | 无 | 无 | 解析二进制 |
| Test Procedure.docx | docx | 测试流程文档 | 无（仅作页眉图标来源） | 无 | 解析二进制 |

---

## 3. 模板间关系

### 两种周报对比

| 维度 | xlsx 周报 | docx 周报 |
|------|----------|----------|
| 语言 | 英文 | 中文 |
| 输出格式 | `.xlsx` 动态矩阵 | `.docx` 固定结构 |
| 结构 | 阶段×子项矩阵 + Site Photo + Issue_RFA Log | A-E 段固定章节 + 主要成果 + 风险表 + 照片 |
| 使用场景 | 国际客户、需照片自动匹配 | 国内客户、偏文档化汇报 |
| 触发词 | 进度周报、progress report、xlsx周报 | 中文周报、状态报告、docx周报 |

### 文件类型 vs 业务场景

| 文件类型 | 业务阶段 |
|---------|---------|
| 勘察 | Q&A.xlsx |
| 施工 | 周报×2、Worker List、Service Report |
| 交付 | 出库单、Test Procedure |

---

## 4. 逐个模板详解

### 4.1 Q&A for (Client) (Project) - (Date).xlsx

#### 用途
- **场景**：现场勘察前/后的澄清表，记录 Tendo 提出的问题、客户端确认、备注。
- **输入**：项目名称、勘察日期。
- **输出位置**：当前目录（手动归档到项目文件夹）。

#### 文件信息
- **文件名**：`TendoCN - Q&A for (Client Name) (Project Name) - (Date).xlsx`
- **类型**：xlsx
- **结构**：单 sheet，固定分类结构（IT/AV/Security/Others 四大类）。

#### 内部结构
```
Row 3   项目名称（无填充，等线16 Bold）
Row 4   日期行（无填充，等线12）
Row 7   标题行（A7:D7 合并，#0099FF 蓝底）
Row 8   表头行（S/N | Tendo | (Client) to Confirm | Remark）
Row 9   一级分类标题（A9:D9 合并，#A2A2A2 深灰底）
Row 10+ 数据行（无填充，白字，A列居中，B列左对齐）
```

分类结构：
- IT Relocation（Server Room + Office Area）
- AV Relocation（Office Area）
- Security Relocation（Server Room + Office Area + New Security Cabling）
- Others

#### 对应 agent
- **文件**：`agents/qa-sheet.md`
- **触发关键词**：Q&A、勘察确认、现场勘察clarification
- **职责**：复制模板 → 填充项目名称和日期 → 保留所有格式和合并单元格 → 输出文件名按规范。

#### 关键字段
| 字段 | 单元格 | 数据来源 | 默认值 |
|------|--------|----------|--------|
| 项目名称 | A3 | 用户输入 | 必填 |
| Survey Date | A4 | 用户输入 | 必填 |

**样式要点**：
- 子标题（B22/B25 等）：**无填充、黑色字体、Bold+单下划线、无边框**
- 数据格：**无填充 + 白色字体**（白底白字，视觉不可见）

#### 注意事项
- 禁止从零创建 Workbook，必须复制模板。
- 禁止修改合并单元格范围、列宽、行高。
- (Client) to Confirm 和 Remark 列留空，由客户端/现场人员填写。

---

### 4.2 Worker Name List.xlsx

#### 用途
- **场景**：项目人员名单，用于进场报备、安全培训签到。
- **输入**：团队成员信息（姓名、性别、职位、联系方式、国籍等）。
- **输出位置**：当前目录（手动归档到项目文件夹）。

#### 文件信息
- **文件名**：`TendoCN - Worker Name List.xlsx`
- **类型**：xlsx
- **结构**：单 sheet，10 列固定表头。

#### 内部结构
```
Row 1-7: 标题和空白区
Row 8:   表头（No. | First Name | Last Name | Gender | Designation | Mobile No. | Email | National ID/Passport No. | Nationality | Remarks）
Row 9+:  数据行
```

示例数据（Row 3）：Wai Kiat Chea / Sai Sai He — **填充前删除**。

#### 对应 agent
- **文件**：`agents/worker-list.md`
- **触发关键词**：人员清单、worker name list、团队名单
- **职责**：删除示例行 → 按顺序填充团队成员信息 → 保留列宽和格式。

#### 关键字段
| 字段 | 说明 |
|------|------|
| No. | 从 1 开始递增 |
| First Name | 名 |
| Last Name | 姓 |
| Gender | M / F |
| Designation | 职位（Project Director / Sales Manager / Project Engineer 等） |
| Mobile No. | 含国家代码的电话号码 |
| Email | 公司邮箱 |
| National ID/Passport No. | 证件号（可空） |
| Nationality | 国家全名（如 Singapore、P.R.China） |
| Remarks | 可选备注 |

#### 注意事项
- 填充前删除 Row 3 的示例数据。
- Nationality 使用完整国家名，不写缩写。

---

### 4.3 每周项目状态报告 (中文).docx

#### 用途
- **场景**：中文周报，用于国内客户或内部汇报。
- **输入**：项目信息、工作进度、主要成果、风险问题、现场照片。
- **输出位置**：`项目目录/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/`

#### 文件信息
- **文件名**：`Tendo - DES-{YYYY}-{Project Name} - 周报 #{NN}.docx`
- **类型**：docx
- **结构**：固定 A-E 段章节。

#### 内部结构
```
头部表格：项目名称 | 客户名称 | 地点/地址 | 报告日期 | 项目经理
图例行：蓝色=已完成 | 绿色=符合预期 | 橙色=轻微延误 | 红色=严重延误

A. 结构化布线系统
B. 机房及IT系统
C.1/C.2 IT设备搬迁
D. AV设备搬迁
E. 检查与验收期

每段表格：项目 | 工作项 | 开始日期 | 结束日期 | 完成度(%) | 备注

主要成果 / 下一步关键计划（双列表格）
风险与问题表格
现场照片画廊
```

#### 对应 agent
- **文件**：`agents/weekly-status-report.md`
- **触发关键词**：中文周报、状态报告、weekly status report、docx周报
- **职责**：填充头部信息 → 按段填充工作进度 → 设置颜色编码 → 填充主要成果/风险/照片。

#### 关键字段

**头部表格**：
| 字段 | 示例 |
|------|------|
| 项目名称 | 塞恩斯伯里上海新办公室装修项目 |
| 客户名称 | Sainsbury's Argos 亚洲有限公司 |
| 地点/地址 | 上海市静安区天目西路128号嘉里企业中心1座20层 |
| 报告日期 | 2025年9月29日 |
| 项目经理 | Dayne Chea |

**进度表格**：
| 字段 | 格式 |
|------|------|
| 工作项 | 中文描述 |
| 开始日期 | dd/mm/yy |
| 结束日期 | dd/mm/yy |
| 完成度 | 0–100% 整数 |
| 备注 | 已完成/进行中/轻微延误/严重延误/暂定 |

**颜色编码**：
- 100% + "已完成" → 蓝色
- 50–99% + 符合预期 → 绿色
- 1–49% 或轻微延误 → 橙色
- 0% + 严重问题 → 红色

#### 注意事项
- 日期格式统一：`dd/mm/yy`（如 07/09/25）。
- 周报编号 `#NN` 每周递增。
- 保留所有表格结构和格式。

---

### 4.4 Weekly Progress Report (项目周报).xlsx

#### 用途
- **场景**：英文周报，用于国际客户或需要照片自动匹配的场景。
- **输入**：项目信息、阶段列表、子项列表、进度数据、照片文件夹、Issue/RFA。
- **输出位置**：`项目目录/Tendo - 03_资料 Technical Archive/周报 - Weekly Report/`

#### 文件信息
- **文件名**：`TendoCN - {Client} - {Project} Weekly Progress Report (项目周报) {YYYY-MM-DD}.xlsx`
- **类型**：xlsx
- **结构**：3 个 sheet（Progress Report / Site Photo / Issue_RFA Log）。

#### 内部结构
**详见**：`docs/superpowers/specs/2026-07-20-weekly-report-workflow-design.md`

#### 对应 agent
- **文件**：`agents/weekly-report.md`（协调器）+ 3 个 subagent
- **触发关键词**：进度周报、progress report、xlsx周报、weekly progress
- **职责**：
  - Progress Report：填充阶段列、子项行、进度数据、颜色编码、AVERAGE 公式
  - Site Photo：扫描照片文件夹 → AI 图像理解 → 生成 Description → 插入照片
  - Issue_RFA Log：填充问题跟踪和 RFI/RFA 日志

#### 关键字段
**详见现有 spec**。核心：
- 进度数据：完成百分比 + 状态（In Progress/Delay/Not Started/Completed）+ Till Date + Target Date
- 颜色编码：Green（In Progress）、Red（Delay）、Orange（Not Started）、Black（Completed）

#### 注意事项
- xlsx 周报 vs docx 周报：语言不同、结构不同、触发词不同。
- 照片插入失败时回退到手动插入提示。

---

### 4.5 Material Requisition.xlsx

#### 用途
- **场景**：出库单，记录物料出库信息。
- **输入**：用户粘贴的邮件/消息文本。
- **输出位置**：`项目目录/Tendo - 03_资料 Technical Archive/出库单 Material Requisition/`

#### 文件信息
- **文件名**：`{Requisition No}- Material Requisition - {Sales Order No.}.xlsx`
- **类型**：xlsx
- **结构**：单 sheet，标题+头部信息+物料表+签字区。

#### 内部结构
**详见**：`docs/superpowers/specs/2026-07-22-delivery-order-generator-design.md`

#### 对应 agent
- **文件**：`agents/delivery-order.md`
- **触发关键词**：出库单、Material Requisition、TCMR、delivery order
- **职责**：解析邮件文本 → 填充头部信息和物料表 → 保留公式 → 输出文件。

#### 关键字段
**详见现有 spec**。核心：
- 头部：Requisition No. / Date / Company / Address / Sales Order No. / Quotation No. / Submitted By
- 物料表：Part No. / Description（英文） / Qty / Unit / Unit Cost / Total Cost（公式）
- 公式：H12-H37（Qty × Unit Cost）、G7-G9（Sub-Total/Tax/Total）

#### 注意事项
- 公式单元格禁止覆盖（A13-A37 序号递增公式、H12-H37 总价公式、G7-G9 金额公式）。
- Description 只取英文部分，中文说明丢弃。

---

### 4.6 Service Report.xlsx

#### 用途
- **场景**：服务交付确认单，服务完成后向客户索要签收确认。
- **输入**：客户信息、报告编号、服务明细、服务类型、进出时间、双签字。
- **输出位置**：当前目录（手动归档到项目文件夹）。

#### 文件信息
- **文件名**：`Service Report.xlsx`
- **类型**：xlsx
- **结构**：单 sheet `SERVICE REPORT`，A1:M59，无公式，21 处合并单元格。

#### 内部结构
```
Row 1-2   标题区（A1:G2 合并，"Service Report"）
Row 4-9   抬头信息区（左右双栏）
          左侧 A-D 列：Deliver To / Company / Address / Telephone / Email
          右侧 E-I 列：Tax Reg. No. / Service Report No. / Date / Customer Ref. / Our Ref. / Attn By
Row 11    明细表头（No. | Description(B-D合并) | Qty | Unit）
Row 12-41 明细数据区（30 行空白待填）
Row 42-44 工作确认区（服务类型勾选 + Time In / Time Out / Date）
Row 47    签字声明（A47:D47 合并）
Row 48-58 签字区（双栏：Client Verification 左 + Attended By 右，含 Signature/Name/Title/Date）
```

#### 对应 agent
- **状态**：无 agent。

#### 关键字段
| 字段 | 位置 | 说明 |
|------|------|------|
| Service Report No. | 右侧抬头 | 编号体系 TCSR（如 TCSR20260423） |
| Customer Ref. | 右侧抬头 | 编号体系 TCSO（客户订单号） |
| Our Ref. | 右侧抬头 | 编号体系 TCSQ（我方报价号） |
| Deliver To / Company / Address / Telephone / Email | 左侧抬头 | 客户信息 |
| Date / Attn By | 右侧抬头 | 报告日期 / 我方经办人 |
| 明细行 | Row 12-41 | No. / Description / Qty / Unit |
| 服务类型勾选 | Row 42-44 | Maintenance / Fault / Variation / Request / Troubleshoot / Others |
| Time In / Time Out / Date | Row 42-44 | 现场进出时间 |
| Client Verification 签字 | Row 48-58 左 | 客户方 Signature / Name / Title / Date |
| Attended By 签字 | Row 48-58 右 | 我方 Signature / Name / Title / Date |

#### 注意事项
- 无公式，纯布局模板，依赖 21 处合并单元格构建版式。
- 编号体系 TCSR/TCSO/TCSQ 是 Tendo 内部单据追溯关键字段。
- 当前 references 中的文件是一份已填写实例（Edrington 客户），版式结构稳定可直接参考。
- 该模板未自动化，需手动填写。

---

### 4.7 Test Procedure.docx

#### 用途
- **场景**：原意图为 ELV 系统测试流程/测试报告模板，但正文已清空，当前为空壳。
- **附加价值**：页眉图标来源（md-to-pdf 流程解包此 docx，从 `word/media/` 取 image2.jpg=📍、image3.jpg=✉️ 转 base64 嵌入 PDF 页眉）。
- **输入**：无（正文为空）。
- **输出位置**：不作为输出目标。

#### 文件信息
- **文件名**：`TendoCN - Test Procedure.docx`
- **类型**：docx
- **结构**：正文为空（0 段落、0 表格、0 图片），仅 1 个 Section 的页眉/页脚承载内容。

#### 内部结构
```
正文：空（document.xml 仅框架，无任何内容）
页眉 header1/header2：Tendo 主 Logo（image4.png）+ 公司全称 + VAT 税号 + 地址（配 image2.jpg 📍）+ 网址（配 image3.jpg ✉️）
页脚 footer1：空
media 文件夹：
  image1.png — numbering.xml 列表符号图（正文为空未使用，残留）
  image2.jpg — 📍 地点图标（页眉用）
  image3.jpg — ✉️ 邮件图标（页眉用）
  image4.png — Tendo 主 Logo（页眉用）
```

#### 对应 agent
- **状态**：无 agent（仅作为页眉图标来源使用）。

#### 关键字段
| 资源 | 路径 | 用途 |
|------|------|------|
| 📍 图标 | `word/media/image2.jpg` | md-to-pdf 页眉地址图标 |
| ✉️ 图标 | `word/media/image3.jpg` | md-to-pdf 页眉邮件图标 |
| Logo | `word/media/image4.png` | 页眉主 Logo（实际 md-to-pdf 改用 assets/Logo Transparent (Header).png） |

#### 注意事项
- 正文为空壳，无章节/表格/签字区/测试项矩阵。
- 该模板唯一有效用途是作为 md-to-pdf 页眉渲染的图标素材源（image2/image3）。
- 与 SKILL.md 中"图标来源：从 TendoCN - Test Procedure.docx 解包获取"完全一致。

---

## 附录：非模板文件

`references/` 中 4 个非模板文件不纳入本文档范围：

| 文件 | 用途 |
|------|------|
| header_only.png | 页眉 Logo 资源（备用） |
| Screenshot 2026-07-15 133109.png | 截图参考 |
| md2pdf-config.js | md-to-pdf 配置文件 |
| tendo-style.css | Tendo 品牌 CSS 样式 |
