# cli-anything — 路由器化重构设计

**日期**：2026-06-15
**作者**：DUDU & Cailleach
**状态**：已批准，进入实施

---

## 目标

将 6 个独立的 CLI 技能（umi-ocr / dxf-dwg-converter / cli-anything-ffmpeg / cli-anything-pdf2zh / cli-anything-web-search-fast / mimo-multimodal）合并为一个**路由器型 meta-skill** —— `cli-anything/`，采用"选择器 + 二级加载"模式。

**动机**：
- 6 个技能全是"CLI 说明书"性质（包装外部 CLI 工具），无本质差异
- 统一入口降低用户认知负担（"用 CLI 工具" → router → 命中子技能）
- 简化后续扩展（加新 CLI = 写子 SKILL.md + 在 router 索引加一行）

---

## 架构

### 嵌套布局

```
cli-anything/                      ← 唯一对外入口
├── SKILL.md                       ← 路由器（手写）
└── sub-skills/                    ← 6 个子技能
    ├── ffmpeg/                    ← 原 cli-anything-ffmpeg
    ├── pdf2zh/                    ← 原 cli-anything-pdf2zh
    ├── web-search-fast/           ← 原 cli-anything-web-search-fast
    ├── ocr/                       ← 原 umi-ocr（重命名）
    ├── dwg/                       ← 原 dxf-dwg-converter（重命名）
    └── mimo/                      ← 原 mimo-multimodal（重命名）
```

**关键前提**：子技能在 `sub-skills/`，Claude 启动时**不会**自动发现。唯一被自动发现的是 `cli-anything/SKILL.md`。所有调用都从 router 入口走。

### 工作流（二级加载）

```
用户："帮我 OCR 一下这张图"
  ↓
Claude 读 cli-anything/SKILL.md（路由器：触发词 + 索引）
  ↓ 触发词匹配 → 命中 sub-skills/ocr
Claude 用 Read 工具读 cli-anything/sub-skills/ocr/SKILL.md（详细说明书）
  ↓
Claude 按说明书调 Umi-OCR
```

---

## Frontmatter Schema

### 路由器（cli-anything/SKILL.md）

```yaml
---
name: cli-anything
description: |
  CLI 工具统一入口路由器。当用户需要以下任一操作时触发本技能：
  OCR 文字识别、图片转文字、截图识字；DWG/DXF 转换、CAD 文字提取与翻译、图层管理；
  视频/音频转码、FFmpeg 编码；PDF 翻译（含 layout 保留）；
  联网搜索、网页抓取；图片/音频/视频多模态内容分析。
  命中后用 Read 工具读取 sub-skills/<name>/SKILL.md 获取详细命令。
type: meta
---
```

**不列旧名**（umi-ocr / dxf-dwg-converter / mimo-multimodal），强制用户用新触发词。

### 子技能（在原 frontmatter 上加 1 字段）

**通用模板**：

```yaml
---
name: <子技能 name 字段 — 视子技能决定改/不改>   # 见 §迁移详情
description: <原 description 完整保留>
type: cli-sub                                     # 新增，标识这是 cli-anything 的子技能
---
```

**`name` 字段策略**：
- 3 个重命名子技能（ocr / dwg / mimo）：`name` 改为新短名（`umi-ocr` → `ocr` 等）
- 3 个保留子技能（ffmpeg / pdf2zh / web-search-fast）：`name` 保持 `cli-anything-ffmpeg` 等原样

**不加触发词、prefix、binary 等新字段**。子技能在 `sub-skills/` 里 Claude 看不到，触发词由 router 维护。

---

## 迁移详情

### 6 个子技能迁移动作

| 原路径 | 新路径 | 改名 | SKILL.md 改动 |
|--------|--------|------|----------------|
| `umi-ocr/` | `cli-anything/sub-skills/ocr/` | `umi-ocr` → `ocr` | `name` 改 + `type: cli-sub` |
| `dxf-dwg-converter/` | `cli-anything/sub-skills/dwg/` | `dxf-dwg-converter` → `dwg` | 同上 |
| `mimo-multimodal/` | `cli-anything/sub-skills/mimo/` | `mimo-multimodal` → `mimo` | 同上 |
| `cli-anything-ffmpeg/` | `cli-anything/sub-skills/ffmpeg/` | （保留 `cli-anything-ffmpeg` 作为原名） | 仅加 `type: cli-sub` |
| `cli-anything-pdf2zh/` | `cli-anything/sub-skills/pdf2zh/` | 同上 | 同上 |
| `cli-anything-web-search-fast/` | `cli-anything/sub-skills/web-search-fast/` | 同上 | 同上 |

### 路径安全性验证

- `sub-skills/dwg/scripts/convert.py` — 相对路径 `scripts/`，SKILL.md 旁边仍有 scripts/ ✅
- `sub-skills/mimo/mimo_multimodal.py` — 相对路径 `./mimo_multimodal.py`，仍在 ✅
- `sub-skills/ocr/` 无 scripts/，原 SKILL.md 内的 `python -c "..."` 内联脚本 ✅
- 3 个 pip 安装的包（ffmpeg / pdf2zh / web-search-fast）—— 包名不变，导入路径不受目录迁移影响 ✅
- `cli-anything-pdf2zh` 用的 `C:\Program Files\pdf2zh\build\pdf2zh.exe` 绝对路径不受影响 ✅

---

## 添加新 CLI 流程

1. 在 `cli-anything/sub-skills/<name>/` 下建 SKILL.md（+ 可选 scripts/）
2. 在 `cli-anything/SKILL.md` 路由器索引表加一行（工具名 + 触发词 + 一句话描述）

两步，零代码。

---

## 测试方案

### 4 个核心场景

| # | 场景 | 测试材料 | 预期 |
|---|------|---------|------|
| 1 | OCR 文字提取 | `%USERPROFILE%\Downloads\Documents\MiniMax_TokenPlan_UsageReport.png` | router → ocr → 输出非空文本 |
| 2 | 多模态理解 | 同上 | router → mimo → MiMo 返回描述 |
| 3 | DWG → DXF 转换 | `%USERPROFILE%\OneDrive\桌面\Tendo-rochling suzhou 2#.dwg` | router → dwg → 生成 .dxf |
| 4 | PDF 翻译 | `%USERPROFILE%\Downloads\Documents\smart_building_dc_power_distribution_and_backup_with_cisco_panduit_fmps.pdf` | router → pdf2zh → 生成 `*-zh.pdf` |

### 2 个边缘场景

| # | 场景 | 操作 | 预期 |
|---|------|------|------|
| 5 | FFmpeg 视频剪切 | `%USERPROFILE%\Downloads\Video\整洁中心 - 整洁.mp4` → 提取前 3 秒 | router → ffmpeg → 输出 3 秒 mp4 |
| 6 | router 失败回退 | "我有个 excel 表格要透视分析" | router 不命中 → Claude 给出"无匹配子技能"提示 |

### PASS 准则

- ✅ 1-5：输出文件**真生成** + router 一次命中正确子技能
- ✅ 6：router 主动认输（不调任何子技能）

---

## 风险与边界

| 风险 | 缓解 |
|------|------|
| 子技能 description 写得宽，router 抢触发失败 | 子技能在 `sub-skills/` 不被自动发现，不存在抢触发问题 |
| 嵌套 SKILL.md 加载路径出错 | 已逐项验证相对路径（见"路径安全性验证"）|
| 旧名（umi-ocr 等）失效 | 故意行为 — router description 不列旧名，强制迁移到新触发词 |
| 加新 CLI 忘了在 router 加索引 | router 索引是手写小表（6 行），漏加 Claude 会主动用 `LS sub-skills/` fallback 发现 |

---

## 实施 Checklist

### Phase 1 — 创建骨架
- [ ] 创建 `cli-anything/` 和 `cli-anything/sub-skills/`
- [ ] 写 `cli-anything/SKILL.md`（路由器主体）

### Phase 2 — 迁移 6 个子技能
- [ ] `git mv cli-anything-ffmpeg/ cli-anything/sub-skills/ffmpeg/`
- [ ] `git mv cli-anything-pdf2zh/ cli-anything/sub-skills/pdf2zh/`
- [ ] `git mv cli-anything-web-search-fast/ cli-anything/sub-skills/web-search-fast/`
- [ ] `git mv umi-ocr/ cli-anything/sub-skills/ocr/`
- [ ] `git mv dxf-dwg-converter/ cli-anything/sub-skills/dwg/`
- [ ] `git mv mimo-multimodal/ cli-anything/sub-skills/mimo/`

### Phase 3 — 改 frontmatter
- [ ] 3 个重命名子技能：`name` 改 + 加 `type: cli-sub`
- [ ] 3 个 cli-anything-* 子技能：仅加 `type: cli-sub`

### Phase 4 — 验证脚本路径
- [ ] dwg/scripts/*.py 相对路径
- [ ] mimo/mimo_multimodal.py 相对路径
- [ ] 3 个 pip 包导入路径

### Phase 5 — 跑 6 个测试场景

### Phase 6 — 文档与提交
- [ ] 更新 `README.md`（技能清单 + 变更日志）
- [ ] 更新 `CLAUDE.md` 提到 router 机制
- [ ] `git add <files>` + `git commit`

---

## 实施前置条件

- [x] 干净 baseline commit（`bd1992a`）
- [ ] 设计文档落档（本文件）
- [ ] 用户最终 review

---

## 已确认决策

| 决策 | 选择 |
|------|------|
| 合并范围 | 全部 6 个 CLI 技能 |
| 路由器形态 | 路由器型（meta-skill） |
| 子技能发现 | 二级加载（router → Read sub-skill） |
| 目录布局 | 嵌套（`cli-anything/sub-skills/<name>/`） |
| 实现复杂度 | 纯文档（无 scripts/、无 REGISTRY.json） |
| 旧名处理 | 强制新触发词（router description 不列旧名） |
| 子技能 frontmatter | 仅加 `type: cli-sub` 字段 |
| 测试材料 | MiniMax_TokenPlan_UsageReport.png / Tendo-rochling 2#.dwg / cisco panduit fmps.pdf / 整洁中心 整洁.mp4 |
