# codex × 本机 llama.cpp

让 OpenAI Codex CLI 用本机模型跑 —— 全程不出本机、不花 token。

```bash
# 1. 起服务（必须用这个脚本，不能用 start.sh 9b）
nohup bash ~/.claude/skills/local-ai/codex/start-codex.sh 9b > /tmp/llama.log 2>&1 &

# 2. 用
codex -p local
```

2026-09-26 实测通过（codex 0.154.0 / llama-server b10883 / Qwen3.8-9B-Distill）：
9B 能完整走通 codex 的 agent 闭环 —— 读工具定义、发 `exec_command`、
读回错误、换写法重试、给出收尾答复。

---

## 一、为什么必须换 chat 模板（核心坑）

codex 0.154 **只讲 OpenAI Responses API** —— `wire_api = "chat"` 已被移除
（二进制里连 `chat/completions` 这个字符串都不剩，只剩 `/v1/responses`）。

llama-server 这边正好有内置转换层，日志会打：

```
Request converted: OpenAI Responses -> OpenAI Chat Completions
```

所以**协议本身是通的**。真正卡住的是消息角色：

```
codex 一次请求里既有顶层 `instructions`（实测 17,174 字符），
又有一条 `developer` 消息（skills / permissions 那几段），
llama-server 把两者都转成 system 角色
        ↓
消息列表以**两条 system 开头**
        ↓
Qwen3.8 原版模板第 83-86 行：

    {%- if message.role == "system" %}
        {%- if not loop.first %}
            {{- raise_exception('System message must be at the beginning.') }}

        ↓
**每一个** codex 请求都 HTTP 500
```

隔离实测（同一条请求，只改消息组成）：

| 请求组成 | 结果 |
| --- | --- |
| `instructions` + `developer` + `user` | **500** `System message must be at the beginning.` |
| `instructions` + `user` | OK |
| `developer` + `user` | OK |

**补丁**（`prepare.py` 自动生成）：把**所有** system 消息合并进模板本来就会输出的
那块 system，并去掉位置断言。工具调用解析、thinking 标签、其余渲染路径逐字未动 ——
`diff` 只有三处、共 +13 −9 行。单 system 的客户端（`llama_chat.py` / pi）下是 no-op。

> ⚠️ 与 SKILL.md 「注意事项」里「`--chat-template-file` 覆盖模板不生效」那条的区别：
> 那条说的是**关思考**（`enable_thinking`）不生效。本次实测 `--chat-template-file`
> **本身是生效的** —— 换模板后报错立即消失，`/props` 回读的也是新模板。
> 两者是不同机制，别因为那条结论放弃模板这条路。
>
> ⚠️ 追加位置有讲究：`--jinja` 必须**先于** `--chat-template-file` 出现，
> 否则自定义模板会被当成「非通用模板」拒掉。所以 start.sh 的透传参数追加在最后。

**MiniCPM5-2B 不需要补丁** —— 它的模板没有位置断言（非首个 system 直接渲染）。
`prepare.py` 认不出锚点时会如实报「无需补丁」，并把原模板原样写出。

---

## 二、codex 侧改了哪些文件

| 文件 | 作用 |
| --- | --- |
| `~/.codex/config.toml` | **只加** `[model_providers.local-llama]` 一段。不写 `model` / `model_provider`，所以 `codex` 默认仍走 openai/ChatGPT 登录态，本地模型必须显式指定。 |
| `~/.codex/local.config.toml` | `codex -p local` 读的 profile：model / provider / catalog / ctx / 工具输出上限。 |
| `~/.codex/local-models.json` | 本地模型目录，消除 `Model metadata not found` 警告并钉死 ctx。 |

两个容易踩的点：

- **`model_catalog_json` 是整体替换，不是合并。** 设了它，内置的 GPT-5.x/6
  全部消失（实测 `codex debug models` 只剩我们那两条）。所以它**只能放 profile**，
  绝不能进全局 `config.toml`。
- **`[profile]` / `[profiles]` 已废弃、写不进去了**，这个版本的机制是
  `--profile <name>` 叠加 `$CODEX_HOME/<name>.config.toml`。

---

## 三、已知限制

| 限制 | 说明 |
| --- | --- |
| **沙箱导致工具全被拒** | 当前 codex 在 Windows 上 `sandbox backend: disabled`，所有 `exec_command`（连 `dir` / `ls`）都被拒：`Rejected(... rejected: blocked by policy)`。拒绝发生在 `codex_core::tools::router` 里，**与 provider 无关**，用云端模型同样如此 —— 属既有问题，不是接本地模型引入的。成因与修法见第四节。 |
| **没有 `apply_patch`** | `apply_patch` 在 Responses 里是 `custom` 工具（Lark 文法），llama-server 只支持 `function` 类型，会 skip 掉。所以目录里把 `apply_patch_tool_type` 留空，让模型改走 shell 命令编辑文件。 |
| 9B 池子 64K 且 4 slot 共享 | codex 一次请求的固定开销约 **7.9K token**（系统提示 + 工具定义）。已经用 `model_context_window` / `model_auto_compact_token_limit` 钉住，别去掉。 |
| decode 53.75 tok/s | 实测（60 tok / 1097 ms）。单轮短问答约 1.1 s，带工具调用的任务数秒。慢是 9B 在 8G 卡上的物理上限，不是配置问题。 |
| 2B 能跑但别指望 | `start-codex.sh minicpm` 可以起，agent 质量明显更弱。codex 场景默认用 9B。 |

## 四、沙箱问题怎么修（未做，需要你决定）

`codex doctor` 的沙箱段：

```
✓ sandbox      restricted fs + restricted network · approval OnRequest
      filesystem sandbox       restricted
      sandbox backend          disabled      ← 关键
```

`--sandbox workspace-write` 会被解析成 `sandbox: read-only`，因为 Windows 沙箱后端
没启用 → 失败关闭（fail-closed）→ 连读命令都拒。三条路，按侵入性排序：

1. **先试交互式 TUI**：`codex -p local` 在真终端里跑，遇到命令会弹审批。
   （本次全程在非交互的 `codex exec` 里测，`approval: never` 下审批一律直接拒。）
2. **查杀软**：doctor 警告 Microsoft Defender 可能干扰，需给
   `codex.exe` / `codex-windows-sandbox-setup.exe` / `codex-command-runner.exe`
   加排除项。`codex doctor --all` 会列出要排除的具体目标。
3. **绕过沙箱**：`--dangerously-bypass-approvals-and-sandbox`。
   ⚠️ 等于让本地模型在你机器上**无审批、无沙箱**地执行任意命令 —— 这是你的决定，
   本次没有替你开。

---

## 五、文件清单与重新生成

```
codex/
├── start-codex.sh          # 入口：生成模板 → 幂等判断 → 调 start.sh 带模板起服务
├── prepare.py              # 四个子命令：template / catalog / check-template / show
├── template-9b.jinja       # 生成物（9B 合并版模板）
└── template-minicpm.jinja  # 生成物（2B 原版模板，无需补丁）
```

`prepare.py` 直接从 **GGUF 读模板**（只扫 header，不碰权重、不占显存、秒级），
不走「起服务→取 /props→重启」那套。

```bash
# 看某模型的模板要不要补丁
py -3 prepare.py show --model 9b

# 重新生成模板（模型换了、或 llama.cpp 升级后）
py -3 prepare.py template --model 9b --out template-9b.jinja

# 重新生成模型目录（改了 CATALOG_MODELS 之后）
py -3 prepare.py catalog --out ~/.codex/local-models.json
```

`start-codex.sh` 的幂等判断是**比对模板内容**，不是看模型名、也不是找固定 marker ——
`start.sh 9b` 起的同名服务模板不对，而 2B 的模板本来就不需要补丁（永远没有 marker），
两种偷懒写法都会退化成「每次都重启」。

**依赖**：`scripts/start.sh` 第 3 个参数起会把额外参数原样透传给 llama-server
（`"${@:3}"`，追加在最后）。这是为 codex 加的唯一一处改动，其余分支行为不变。
