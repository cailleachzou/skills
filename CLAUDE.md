# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库概述

这是一个 Claude Code 自定义技能库，每个子目录是一个独立技能。所有技能服务于同一个用户（DUDU/神棍INTP风格，弱电智能化设计师），所以风格和上下文高度一致。

## 技能开发工作流

使用 `/skill-creator` 创建或改进技能。完整流程：draft → test (subagent) → human review → improve → repeat。

开发新技能时：
1. 参照已有技能的目录结构（`SKILL.md` + 可选 `scripts/`/`references/`/`assets/`/`evals/`）
2. 测试用例保存在 `<skill>/evals/evals.json`
3. 提交时用 `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`

## 目录结构

```
skill-name/
├── SKILL.md          # 必需：YAML frontmatter (name/description) + markdown 说明
├── scripts/          # 可执行脚本（Python/Node等）
├── references/       # 按需加载的参考文档
├── assets/           # 模板、图标、字体等资源
└── evals/            # 测试用例 JSON
```

## 文档规范

- SKILLS.md 是全量技能清单（英中双语），更新技能后同步
- README.md 是对外展示入口（中文）
- 新技能触发关键词要明确写在 SKILL.md frontmatter 的 description 字段

## 用户语言习惯

- 日常中文，文件内容中英双语
- ELV = 弱电
- 避免机械模板回复，风格直接简洁

## Windows 环境注意

- Python 命令用 `py -3` 或 `python`，不用 `python3`
- Node 依赖需先 `npm install`
- 路径用 `/` 不用 `\`