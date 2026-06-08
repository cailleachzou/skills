# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 技能开发规范

新增或修改技能时：

- **SKILL.md** 是核心文件，包含 YAML frontmatter (name + description) 和 markdown 说明
- 描述字段（description）是触发机制，尽量"pushy"，让 Claude 在相关场景主动调用
- 目录结构：`SKILL.md` + 可选 `scripts/` `references/` `assets/` `evals/`
- 测试用例保存在 `<skill>/evals/evals.json`
- 使用 `/skill-creator` 开发技能，完整流程：draft → subagent test → human review → improve → repeat

## 文档同步

- `README.md` — 全量技能清单 + 环境依赖 + 更新日志（中文），每次技能增删改同步更新

## Git 提交规范

```bash
git commit -m "$(cat <<'EOF'
简短描述

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```