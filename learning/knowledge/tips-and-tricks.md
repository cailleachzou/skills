# 使用技巧、常见坑、组合模式

> 实战经验总结，帮你少走弯路。

---

## 1. 提示词技巧

### 1.1 描述意图，别描述工具

```
❌ 帮我调用 docx 技能生成一个文件
✅ 帮我把这份方案生成 Word 文档，要有目录和页眉，用 Tendo 品牌模板
```

Claude 会根据你的描述自动匹配最合适的技能。你越具体，它越准。

### 1.2 给够上下文

```
❌ 帮我处理一下那个 PDF
✅ 帮我把 C:/项目资料/报价单.pdf 里的表格提取出来，写入 Excel，加上合计公式
```

关键信息：
- 文件路径
- 期望输出格式
- 特殊要求（品牌、模板、语言）

### 1.3 用中文就行

所有自建技能都支持中文触发。不需要翻译成英文，也不需要背诵技能名。

```
✅ 画一张系统架构图
✅ 把这份 DWG 翻译成英文
✅ 生成一封邮件给客户
```

### 1.4 复合任务一句话说清

```
✅ 我有一份投标资料 PDF（C:/投标/资料.pdf），帮我：
   1. 提取文字
   2. 生成技术方案 Word 文档
   3. 画系统架构图和甘特图
   4. 最后生成一份 15 页的 PPT
```

Claude 会自动拆解步骤、串联技能。你不需要手动指定每一步用什么技能。

### 1.5 渐进式细化

先让 Claude 出初稿，再逐步修改：

```
第一轮：帮我生成一份技术方案
第二轮：第二章太简略了，补充系统架构的详细描述
第三版：在方案里加一张网络拓扑图
```

比一次性写一个超长提示词更可控。

---

## 2. 常见坑 & 解法

### 2.1 文件被占用

```
报错：PermissionError: Permission denied on .docx
原因：文件被 Word 或其他程序打开
解法：关闭所有 Word 窗口，用 Get-Process word* 确认无残留
```

### 2.2 Python 命令错误

```
报错：Python was not found
原因：Windows 上没有 python3 命令
解法：用 python 或 py -3（不要用 python3）
```

### 2.3 Node 依赖缺失

```
报错：Cannot find module 'adm-zip'
原因：npm 包未安装
解法：npm install adm-zip
```

### 2.4 大文件读取超时

```
问题：读取大 PDF 或大 Excel 很慢
解法：用 offset 和 limit 分段读取
示例：Read file_path offset=100 limit=50
```

### 2.5 网络搜索失败

```
问题：WebSearch/WebFetch 不好用
解法：用 WebSearch 工具重试，或换搜索引擎 / 加关键词
```

### 2.6 PDF 提取乱码

```
问题：扫描版 PDF 提取文字全是乱码
解法：pdf 技能有自动 fallback 链
      pdfplumber → docling → AI 视觉识别
      如果 pdfplumber 失败，会自动尝试 OCR
```

---

## 3. 技能组合模式

### 3.1 串行流水线

```
输入 → 技能A → 中间结果 → 技能B → 输出
```

示例：
```
PDF → markitdown → Markdown → docx → Word 文档
```

适用：步骤之间有明确的输入输出关系。

### 3.2 并行扇出

```
输入 → 技能A → 输出A
     → 技能B → 输出B
     → 技能C → 输出C
```

示例：
```
项目资料 → 同时生成：
  - Word 方案文档（docx）
  - 架构图（diagram-skill）
  - PPT 汇报（pptx）
```

适用：多个独立输出，互不依赖。

### 3.3 条件分支

```
输入 → 判断 → 技能A（条件1）
             → 技能B（条件2）
```

示例：
```
PDF 提取 → 文字可读？→ 是 → 直接用
                     → 否 → docling → 再用
```

适用：根据中间结果决定下一步。

### 3.4 迭代循环

```
输入 → 技能A → 输出 → 审查 → 不满意 → 技能A（修改）→ ...
                                      → 满意 → 完成
```

示例：
```
需求 → docx 生成初稿 → 审查 → 补充细节 → docx 修改 → 审查 → OK
```

适用：需要反复打磨的场景。

---

## 4. Superpowers 使用技巧

### 4.1 开始新功能前先 brainstorming

别直接写代码，先让 Claude 帮你理清需求：

```
我想做一个技能，把微信聊天记录导出成 Markdown
```

Claude 会问你一系列问题，帮你发现你没想到的细节。

### 4.2 用 writing-plans 拆解任务

```
基于刚才的设计，写一个实现计划
```

得到分步计划后，再开始实现。比直接写代码效率高 3 倍。

### 4.3 遇到 bug 先 systematic-debugging

别急着改代码，先让 Claude 系统化定位问题：

```
测试报错了：TypeError: Cannot read property 'xxx' of undefined
```

Claude 会按步骤排查，而不是瞎猜。

### 4.4 完成前必须 verification

```
跑一下所有测试，确认通过
```

不要口头说「应该没问题」，让 Claude 实际跑一遍。

---

## 5. Obsidian 生态技巧

### 5.1 用 obsidian-cli 批量管理笔记

```
搜索所有带 #项目 标签的笔记
创建一个新笔记，frontmatter 里加上 project: 江阴博物馆
```

### 5.2 用 obsidian-bases 创建数据库视图

```
创建一个 .base 文件，表格视图显示所有项目笔记的：名称、状态、截止日期
按状态分组，按截止日期排序
```

### 5.3 用 defuddle 抓网页内容

```
把这篇文章保存到 Obsidian：https://example.com/article
```

比 WebFetch 干净，自动去广告和导航。

---

## 6. 效率倍增器

### 6.1 善用 batch 操作

- `batch-image-renamer` — 批量重命名图片
- `dwg` — 批量 DWG↔DXF 转换
- `ffmpeg` — 批量视频转码

### 6.2 善用模板

- `docx` — Tendo 信纸模板
- `pptx` — 模板编辑模式
- `tendo-brand` — 统一品牌风格

### 6.3 善用 fallback 链

- `pdf` — pdfplumber → docling → AI 视觉
- `docling` — PDF/DOCX/图片 → Markdown/JSON（内置 OCR）

不需要你手动切换，技能会自动尝试。
