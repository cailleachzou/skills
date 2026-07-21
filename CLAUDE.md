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
├── <skill-name>/
│   ├── SKILL.md                 ← 核心：YAML frontmatter + 说明
│   ├── scripts/                 ← 可选：脚本文件
│   ├── references/              ← 可选：参考文档
│   ├── assets/                  ← 可选：静态资源
│   └── evals/
│       └── evals.json           ← 测试用例
└── cli-anything/
    ├── SKILL.md                 ← 路由器入口（唯一被自动发现）
    └── sub-skills/
        └── <name>/
            └── SKILL.md         ← 子技能（嵌套，不被自动发现）
```

## 测试命令

```bash
# 运行单个技能的测试
claude --skill <skill-name> --eval

# 查看技能列表
ls skills/

# 验证 SKILL.md 格式
head -20 skills/<skill-name>/SKILL.md  # 检查 YAML frontmatter
```

## CLI 工具统一入口（cli-anything 路由器）

所有 CLI 工具（OCR / CAD / FFmpeg / PDF 翻译 / 联网搜索 / 多模态）统一通过 `cli-anything/` 路由器入口走：

- **入口**：`cli-anything/SKILL.md`（唯一被 Claude 自动发现）
- **子技能**：`cli-anything/sub-skills/<name>/SKILL.md`（嵌套，Claude 不会自动发现）
- **工作流**：用户在 Claude 对话里说 CLI 需求 → router 触发 → Read 子技能 SKILL.md → 调命令
- **添加新 CLI**：在 `cli-anything/sub-skills/<name>/` 放 SKILL.md + 在 router 索引表加一行

不要直接 mv 出 `cli-anything/sub-skills/<name>/` 之外的位置 — router 依赖嵌套结构。

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

*最后更新：2026-06-20*
