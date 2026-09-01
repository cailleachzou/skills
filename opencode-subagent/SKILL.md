---
name: opencode-subagent
description: "Delegate tasks to OpenCode CLI with local Qwen2.5 14B model. Use when the user wants to offload a coding subtask to the local LLM via OpenCode."
version: 1.1.0
---

# OpenCode Subagent

Delegate coding tasks to OpenCode CLI running the local Qwen2.5 14B model via llama.cpp Vulkan.

## Prerequisites

- llama-server (Vulkan) 运行在 `http://127.0.0.1:8080`，已加载 Qwen2.5 14B
- OpenCode CLI 已安装（`opencode`）
- Provider `local-llm` 已在 `~/.config/opencode/opencode.json` 配置，默认模型已设为 `local-llm/qwen2.5:14b`

## Usage

默认即本地模型（无需 `-m`）：

```bash
opencode run "任务描述"
```

显式指定本地模型：

```bash
opencode run "任务描述" -m local-llm/qwen2.5:14b
```

切回云端 302.AI Claude Sonnet 4.5：

```bash
opencode run "任务描述" -m 302ai/claude-sonnet-4-5
```

JSON 输出（便于程序解析）：

```bash
opencode run "任务描述" --format json
```

附加文件：

```bash
opencode run "Review this code for bugs" -f path/to/file.py
```

继续上次会话：

```bash
opencode run "Continue: add error handling" -c
```

## 启动本地模型服务

```cmd
cd /d C:\Users\caill\tools\llama-cpp\vulkan
llama-server.exe -m "C:\Users\caill\models\Qwen2.5-14B-Instruct-Q4_K_M.gguf" -ngl 99 --host 127.0.0.1 --port 8080 -c 2048 --alias qwen2.5:14b
```

验证: `curl http://127.0.0.1:8080/health`

## Limitations

- Qwen2.5 14B（8.4GB）GPU ~28 tok/s，适合中等复杂度任务（函数实现、代码片段、bug 修复、中文任务）
- 不适合超大上下文（默认 `-c 2048`）或架构级决策
- llama-server 必须已启动；检查 `curl http://127.0.0.1:8080/health`
- 涉及看/听/说走 mimo；复杂推理走主模型

## Model Selection

默认模型已设为 `local-llm/qwen2.5:14b`，覆盖方式：

```bash
opencode run "任务" -m 302ai/claude-sonnet-4-5   # 云端
```
