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
├── README.md                    ← 全量技能清单 + 环境依赖
├── CHANGELOG.md                 ← 封存档案（2026-05-18 → 2026-09-13），不再新增
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

## CLI 工具技能

**两类并存**：

- **路由器型** —— `cli`：容器型统一入口，下辖 4 个子技能（ffmpeg / ncm-dump / pdf2zh / tyc-it），
  位于 `cli/sub-skills/`，**不被自动发现**，只能经路由器进入。说自然语言自动触发，
  或 `/cli` 列清单、`/cli <工具名>` 直取子技能说明书。
  ⚠️ **维护硬规则**：停用子技能必须「移出目录 + 删索引行」，**禁止**留 `xxx.disabled/`
  ——2026-08-06 拆掉旧路由器 `cli-anything` 就是因为这类残留腐化了索引。
- **顶层独立型** —— `docling` / `dwg` / `officecli` / `graphify` / `local-ai` /
  `computer-repair-skill`：各自被 Claude 自动发现。

每个技能目录结构：`SKILL.md` + 可选 `scripts/`。技能名与目录名一致。

## 文档同步

- `README.md` — 全量技能清单 + 环境依赖（中文），每次技能增删改同步更新
- `CHANGELOG.md` — **封存档案，不再新增**。变更记录自 2026-09-13 起改由 **commit message** 承载

## Git 提交规范

提交信息**即变更日志** —— 自 2026-09-13 起不再往 `README.md` / `CHANGELOG.md` 追加日志，所以 message 要写清「做了什么 / 为什么 / 实测结论」，别只写一行标题：

```bash
git commit -m "$(cat <<'EOF'
简短描述

- 具体变更与理由
- 实测结论 / 踩坑

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

---

*最后更新：2026-09-13*
