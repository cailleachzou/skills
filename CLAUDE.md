# CLAUDE.md — Skills 开发规范

## 技能开发规范

新增或修改技能时：

- **SKILL.md** 是核心文件，包含 YAML frontmatter (name + description) 和 markdown 说明
- 描述字段（description）是触发机制，尽量"pushy"，让 Claude 在相关场景主动调用
- 目录结构：`SKILL.md` + 可选 `scripts/` `references/` `assets/` `evals/`
- 测试用例保存在 `<skill>/evals/evals.json`
- 使用 `/skill-creator` 开发技能，完整流程：draft → subagent test → human review → improve → repeat

## 目录结构

```
skills/
├── CLAUDE.md                    ← 本文件
├── README.md                    ← 全量技能清单 + 环境依赖 + 更新日志
└── <skill-name>/
    ├── SKILL.md                 ← 核心：YAML frontmatter + 说明
    ├── scripts/                 ← 可选：脚本文件
    ├── references/              ← 可选：参考文档
    ├── assets/                  ← 可选：静态资源
    └── evals/
        └── evals.json           ← 测试用例
```

## 测试与评估

```bash
# 查看技能列表
ls skills/

# 验证 SKILL.md 格式
head -20 skills/<skill-name>/SKILL.md  # 检查 YAML frontmatter
```

- **技能评估**：通过 `/skill-creator` 工作流运行（测试用例在 `<skill>/evals/evals.json`）：draft → subagent test → human review → improve → repeat
- ⚠️ `claude --skill --eval` 不是真实 CLI 命令（已用 `claude --help` 验证），勿用

## CLI 工具技能（顶层独立）

CLI 工具技能（文档解析 / CAD / FFmpeg / PDF 翻译 / DXF 复查）已提升为**顶层独立技能**，各自被 Claude 自动发现：

- **docling** — 文档解析与转换（PDF/DOCX/PPTX/XLSX/HTML/图片/音频 → Markdown/JSON，含 OCR）
- **dwg** — CAD 格式转换、文字提取/翻译、图层、SVG 导出
- **dxf-review** — DXF 视觉复查、渲染预览、多模态对比
- **ffmpeg** — 音视频转码、批量处理、预设管理
- **pdf2zh** — PDF 翻译（保留 layout）

每个技能目录结构：`SKILL.md` + 可选 `scripts/`。技能名与目录名一致。

## 文档同步

- `README.md` — 全量技能清单 + 环境依赖 + 更新日志（中文），每次技能增删改同步更新

## Git 提交规范

```bash
git commit -m "$(cat <<'EOF'
简短描述

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

*最后更新：2026-08-06*
