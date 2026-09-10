---
name: local-ai
description: >
  本机本地模型层（llama.cpp CUDA + RTX 5060 Laptop 8GB）—— 省 token、可离线、保隐私。
  用途：① 单次轻量任务（改写/摘要/分类/抽取/短句翻译）；② 批量并发处理几十上百条同质小任务；
  ③ 本地 agent（pi CLI + 本地模型，自己读文件、改写、写回、多步闭环）。
  遇到「大量简单重复的活」——批量改写、逐条分类打标、逐条抽取字段、批量摘要、批量翻译短句——
  不要在主上下文里逐条做，也别急着派联网 subagent（那同样烧 token）：交给本机跑完，
  只把一份回执（条数 / 异常清单 / 抽样）带回本对话，主模型整体看过再决定落地。
  需要读写文件或多步闭环的，交给 pi 在本地跑完，主模型只看摘要。
  用户提到"本地处理 / 离线 / 断网 / 不耗 token / 省 token / 最简单任务 / 省电 / 隐私 / 本机模型"时同样使用本技能。
  不适用：需要准确事实知识、需要跨条全局推理、或本地小模型明显扛不住的高难度任务。
  视觉/OCR/音频走 mimo 或 docling，不在此技能。
compatibility: |
  硬件: AMD Ryzen 9 8945HX (16C/32T) + NVIDIA RTX 5060 Laptop 8GB VRAM (GB206 / Blackwell / sm_120 / CC 12.0) + 32GB DDR5，驱动 592.01
  软件:
  - llama.cpp 预编译版 b10883 (CUDA 13.3): `C:\Users\caill\tools\llama-cpp\cuda-b10883\llama-server.exe`
  - 该目录自带 cudart64_13.dll / cublas64_13.dll（CUDA 13 runtime 已含，无需另配 cudart zip）
  - ⚠️ 必须用 b10883：9B-Distill 是 qwen35 架构（Gated DeltaNet / SSM 混合），旧版 llama.cpp 不认这个架构
  - ollama 已于 2026-09-10 彻底卸载，本技能不再依赖 ollama
  - pi CLI (@earendil-works/pi-coding-agent)：本地 agent 层，provider `llamacpp` 已配在
    `~/.pi/agent/models.json`（baseUrl http://localhost:8080/v1，两个模型 cost 均为 0）。
    `settings.json` 的 `packages` 已清空（原为 pi-subagents），实测默认参数 11s 跑完 10 条改写；
    ⚠️ 若重装 pi-subagents 这类编排扩展，必须加 `--no-extensions`，否则约 7K 的编排提示词
    会让小模型陷入死循环（实测 400s+ 零产出）
  GGUF 模型 (位于 D:\models\gguf\):
  - minicpm5-2b/MiniCPM5-2B-Q8_0.gguf (2.68GB) — **默认模型**，~85–107 tok/s，128K ctx
  - qwen3.8-9b-distill/Qwen3.8-9B-Q4_K_M.gguf (5.78GB) — 按需（pi agent / 复杂任务），~55 tok/s @32K
  - Git Bash 别名（`~/.bashrc`）：`llama` = 2B，`llama9` = 9B；scripts 目录本身在 PATH 里
  ⚠️ 两个模型都是 thinking 模型，**默认开思考**（本机主要用来跑 pi coding agent）。
     要关思考必须走请求级 `chat_template_kwargs`（`llama_chat.py --no-think` / `llama_batch.py --no-think` 已内置）；
     server 启动参数全部实测无效 —— 见下方「思考控制」一节
metadata:
  author: Cailleach Zou
  version: "6.2"
  created: 2026-08-11
  updated: 2026-09-10
allowed-tools: Bash(*)
---

# local-ai — 本机本地模型

这一层解决的是同一件事：**手上有一堆简单重复的活，主模型逐条做等于烧钱。**
交给本机跑，主模型只处理「派活」和「验收」两头。

```
主模型                          本机（0 token）                  主模型
读懂任务、切成原子步骤   →   批量并发跑 / pi 多步闭环   →   读回执、抽样、决定落地
```

三条派发路径（详见下文）：

- **单条 / 少量** → `llama_chat.py`
- **几十上百条同质小任务（最划算）** → `llama_batch.py` 并发，跑完自动落**回执**
- **要读文件、多步决策** → pi 当本地 agent

复杂规划、跨系统重构留主模型；视觉/OCR/音频走 mimo 或 `docling`。

## 一、本机一次只跑一个模型

`llama-server` 是**单模型**进程：一次只加载一个 GGUF，而且**忽略请求体里的 `model` 字段**。
所以：

- **选型是「轮次级」决策，不是「每批级」。** 开工前看这一轮主要干什么，选一次，跑到底。
- 切换 = 重启 server（加载 2–4s，前缀缓存全丢）。**不要为单条任务来回切。**
- **默认挂 2B**（`llama` / 无参 `start.sh`）。它的覆盖面比很多人以为的宽得多 —— 批量、长文本、并发、
  单条改写自不必说，**它同样有 tool use，pi 拿它跑多步 agent 闭环也成立**；再加上 128K 上下文，
  整体覆盖面其实比 9B 更广。**别把它当成「9B 的降级备用」。**
- 只有**任务本身确实难**时才切 9B（`llama9` / `start.sh 9b`）—— 代码、长链推理这类 ——
  并且把这一轮所有 9B 的活攒在一起一次干完，跑完切回 2B。
- **要并发的任务、以及超过 32K 的单条任务，永远留在 2B** —— 9B 既不能并发，池子也只有 32K。
- 单条 / 少量任务**不为它切模型** —— 有什么用什么。

⚠️ **9B 不并发 —— 这是硬规则，不是偏好。** 要并发就切 2B。

理由：`-c 32768` 时 `/slots` 显示每槽 `n_ctx = 32768`，看着像 4 路各 32K，**其实不是**。
启动日志写的是 `n_slots = 4, n_ctx_slot = 32768, kv_unified = 'true'` —— `kv_unified` 意味着
KV 是**一个共享池**，4 个 slot 从同一个 32K 的池子里取。加上整卡只剩不到 1GB 余量
（实测 6891 MiB / 8151，其中模型权重本身就占 5502 MiB），拿 9B 开并发轻则互相挤、重则装不下。

2B 没这个问题：池子 128K、每槽 32K，并发 4 稳定跑（实测约 2× 串行吞吐）。

### 裸模型是「函数」，套上 pi 才是「agent」

**llama-server 本身**是个无状态单轮 API：喂一段文本，吐一段文本。它没有工具调用、不能读写文件、
看不到同批第 2 条任务长什么样、也不会自己跑多步。所以拿它直接干活时，分工永远是：

```
外面这层          = 读懂任务 → 切成原子步骤 → 准备输入 → 读回结果 → 校验 → 汇总
裸 llama-server   = 只负责每一步的「文本进 → 文本出」
```

关键在**外面这层不必是联网的 Claude** —— pi CLI + 本地模型就能胜任（见「用法 3」），
整条链留在本机、不花一个 token。

## 二、主模型怎么派活（三步）

### 第 1 步：先定模型 —— 在派活之前，不是在执行中

不要「先派出去再说」，模型是**派发指令的一部分**。看这一轮是什么活，一次定死：

| 这一轮主要是 | 用哪个 | 为什么 |
| --- | --- | --- |
| 批量同质小任务、长文本、要并发、单条改写、**agent 多步闭环** | **2B**（默认，多半已经在跑） | 存量状态；它也有 tool use，覆盖面更广 |
| 代码、长链推理这类真正难的活（上下文 < 32K） | **9B** | 只有这种才值得切 |
| 单条 > 32K | **2B**（别切 9B） | 9B 的共享池只有 32K，装不下 |

切换不用自己动手 —— **`start.sh` 本身就是幂等的**：

```bash
bash C:/Users/caill/.claude/skills/local-ai/scripts/start.sh 9b        # 需要 9B 时才切
```

它会先问在跑的是哪个模型：已经是目标 → 打印 `[复用]` 直接返回（不重启、不丢前缀缓存）；
是另一个 → 走 `stop.sh` 停掉（**并等显存真的回收**）再启动目标；没在跑 → 直接启动。

所以「定模型」这一步就是调一次 `start.sh <模型>`，看它回 `[复用]` 还是 `[切换]`。
**把这一轮所有该模型的活攒在一起跑，别一条一换。**

### 第 2 步：派下去

纯文本批量用 `llama_batch.py`；要读写文件、多步闭环用 pi。prompt 写法见「五、写 prompt 的实测经验」——
那两条坑不避开，会大面积返工。

### 第 3 步：只读回执，别读全量结果

`llama_batch.py` 跑完会自动在输出旁边写 `<out>.report.md`。
**主模型读那一份就够了** —— 把几十上百条结果全 `Read` 进上下文，等于把省下的 token 又原样花回去，
还比自己做更慢。回执里含 **server 实际模型名**，这是第 1 步有没有搞错的唯一闭环检查点。

详见「四、回流」。

### 第 4 步：收工 —— 把后台的 server 关掉

`llama-server` **不会自己退出**，停在那儿就占着 6–7GB 显存。一轮本地活干完、且没有后续任务时
把它停掉 —— 尤其是用 `run_in_background` 起的那个 shell，别留在后台吃资源。

```bash
bash C:/Users/caill/.claude/skills/local-ai/scripts/stop.sh
```

`stop.sh` 杀进程后会**轮询显存直到真的回落**才返回（驱动回收有延迟；不等的话，
下次启动新模型会有部分层掉到 CPU，不报错只是慢十倍）。

## 三、三条派发路径

### 用法 1：单次调用（`llama_chat.py`）

适合条数少（≲10 条）或只要一次结果。

```bash
py -3 "C:\Users\caill\.claude\skills\local-ai\scripts\llama_chat.py" "用一句话介绍量子计算"
py -3 "...\llama_chat.py" --no-think "把这句话改得正式些：这方案不太行"   # 关思考，省 90% token
py -3 "...\llama_chat.py" -s "只输出JSON" -n 200 "抽取姓名和公司：张三在字节跳动"
bash ".../scripts/chat.sh"                                             # 交互式
```

`llama_chat.py` 没有 `--model` 参数 —— 它打的就是 server 上当前加载的那个。

### 用法 2：批量并发（`llama_batch.py`）—— 量大时的正解

```bash
# 每行一条 prompt
py -3 "...\llama_batch.py" tasks.txt -o out.jsonl -j 4 --no-think

# JSONL 输入：可逐条指定 id / system / max_tokens / temperature
py -3 "...\llama_batch.py" tasks.jsonl -o out.jsonl --no-think \
    -s "只输出一个JSON对象 {\"text\": \"改写结果\"}，不要解释"
```

输入两种格式（`-f auto` 自动探测）：

```jsonc
// text：每行一条 prompt
把这句话改得正式些：这方案不太行

// jsonl：只有 prompt 必填，其余按需覆盖全局默认
{"id": "a1", "prompt": "...", "system": "你是公文助手", "max_tokens": 100, "temperature": 0.3}
```

输出 JSONL，**保持输入顺序**（并发完成顺序会乱，脚本已重排）：

```json
{"index": 0, "id": "a1", "prompt": "...", "result": "...",
 "completion_tokens": 42, "elapsed": 1.8, "error": null}
```

关键参数：`-j` 并发度（默认 4，**只在 2B 上用** —— server 跑着 9B 时脚本会警告并让你改 `-j 1`）、
`--no-think` 关思考、`--resume` 断点续跑（读已有输出跳过已完成的行）、`--retries` 单条重试。
单条失败不会中断整批，原因记在 `error` 字段。

跑完输出旁边自动多一个 `<out>.report.md` —— 那是给主模型看的回执，见「四、回流」。

**并发实测数据**（MiniCPM5-2B / n_slots=4，8 条任务）：

| 模式 | 墙钟 | 吞吐 |
| --- | --- | --- |
| 串行 | 3.0s | 84 tok/s |
| 并发 2 | 3.0s | 125 tok/s |
| **并发 4** | **2.0s** | **169 tok/s** ← 默认，约串行的 2 倍 |
| 并发 8 | 2.1s | 178 tok/s ← 超过 slot 数，收益基本没了 |

### 用法 3：pi 当本地 agent（能自己读写文件的 subagent）

上面两种用法都只是「文本进 → 文本出」。当任务需要**读文件、看情况决定下一步、写回结果**时，
用 pi（已全局安装，provider `llamacpp` 已配好），**全程本机、零 token、断网可跑**。

```bash
cd <工作目录>
pi -p \
  --no-skills --no-context-files \
  --provider llamacpp --model qwen3.8-9b-distill \
  --thinking off --no-session \
  "读取 tasks.txt，逐行改写成正式书面语，用 write 工具写入 out.jsonl（每行一个 JSON 对象）"
```

（装了编排类扩展再加 `--no-extensions`；工具太多、模型挑花眼时可用 `--tools read,write` 限定。）

⚠️ **`--model` 只是标签，真正跑的是 server 上加载的那个。** llama-server 忽略请求里的 model 字段，
所以这里写 9B、server 上跑着 2B 时，实际用的还是 2B —— **不报错**，只是跟你以为的不是一个模型。
**2B 一样能跑 pi 的 tool use**，不是「降到不能用了」；但如果这一轮打定主意要 9B，就得先 `llama9` 切过去。

**关键：别让编排类扩展污染 prompt。** 实测同一条「逐条改写」任务：

| 配置 | 耗时 |
| --- | --- |
| 装了 `pi-subagents` 时（默认） | **400s+ 超时，零产出** |
| `--no-extensions` | **7s** |
| `--no-extensions --tools read,write` | **12s**，结果正确落盘 |
| **packages 清空后（默认参数）** | **11s，10 条全对** ← 当前本机状态 |

`pi-subagents` 这类扩展是给**强模型**做多智能体编排用的，它们往 system prompt 里塞约 7K tokens
的编排说明（`workflowScript` / `runs.run` / lanes…）。9B 读到「批量 N 条」就去套那套 JavaScript
编排语法，套不出来就反复重试 —— **死循环**，而且不报错、只表现为「慢」，很容易误判成模型不行。

本机 `~/.pi/agent/settings.json` 的 `packages` 已清空，**默认配置即可直接跑**。
一旦重装这类扩展，就必须加 `--no-extensions` 才跑得动。

第三方 agent 直接调 API 时**不发 `chat_template_kwargs`** —— 模板变量处于未定义状态，
模型按自身默认行为走，实测就是**思考开启**，正好符合 agent 场景，无需额外配置。

**什么时候用 pi，什么时候用 `llama_batch.py`：**

- **纯文本变换**（改写/分类/抽取，几十上百条）→ `llama_batch.py`。没有 agent 开销，5 条约 2s。
- **需要动文件或多步决策**（读进来 → 判断 → 改写 → 写回去 → 再校验）→ pi。
  它慢（多轮 + 7K prompt），但能自己把活干完，不用你在外面写胶水代码。

## 四、回流：本机跑完，主模型看什么

**这是最容易做错的一步。** 本地跑完 60 条，主模型要是把 60 条全读进上下文，
省下来的 token 又原样花回去了。所以回到本对话的是**回执**，不是结果：

- 全量结果落 `out.jsonl`，**默认不读**
- 主模型只读 **`out.report.md`**（`llama_batch.py` 跑完自动生成；pi 路径让 pi 按同样格式写一份）
- 回执里有：
  - **条数 / 成功 / 失败**
  - **异常清单**：失败、空结果、原样回显、带代码块围栏、JSON 解析失败、过短
  - **抽样 3–5 条**（首 / 中 / 尾 + 第一条异常）
  - **server 实际模型名** —— 核对第 1 步的选型
- 要深查某几条时再按 index 去 `Read out.jsonl`

有了回执，「整体看一下」才是一件几十行的事，而不是把几百条灌进上下文。

## 五、审阅与落地：分级闸门

拿到回执后按风险分级，别一刀切：

- **自动落地** —— 新增文件、草稿、分类打标、可回滚的产物：校验通过就直接写，不打断用户。
- **先确认** —— 覆盖原件、外发、不可逆操作、事实类最终交付：汇总到本对话，等用户点头。

回执不过关就回炉：改 prompt（加 one-shot 示例最常见）、降温度、或换模型重跑。
`llama_batch.py --resume` 只补失败项，不用整批重来。

## 六、什么该外包，什么不该

| ✅ 适合（文本变换类） | ❌ 不适合 |
| --- | --- |
| 改写、润色、摘要、格式化、短句翻译 | 需要准确事实/知识的问题（会幻觉，见下） |
| 逐条分类、打标、情感判断 | 需要跨条全局推理（单条无状态，看不到别条） |
| 从一条文本里抽固定字段 | 高风险的最终交付（结果必须再过一遍人工/主模型） |
| 批量生成候选（草稿、标题、关键词、测试数据） | 依赖实时信息、要调外部工具链 |

> ⚠️ **别拿它答事实题**。实测 MiniCPM5-2B 会一本正经地瞎编：问 Zig 说「用汇编语言编写的」，
> 问 Elixir 说「运行在贝叶斯计算引擎上」—— 两条都是错的，措辞还很自信。
> 它擅长的不是「回忆世界知识」，而是「处理你喂给它的文本」。事实性内容只当草稿用。

## 七、写 prompt 的实测经验

下面两条是实跑出来的坑，都会导致**大面积返工**，不是个别条目的问题：

- **JSON 示例必须是干净字面量**。给 2B 做抽取时，如果把字段说明写进示例的**值**里
  （如 `{"公司": "此处填公司名"}`），它会把说明当成答案抄下来 —— 实测 30 条里 24 条把公司名
  抽成 `null`，连原文明写的都漏。正确做法是给一条**真实样例**，说明写在 prompt 正文里。
- **纯指令约束不住它，要给 one-shot 示例**。要求「只输出改写结果」时，实测 60 条里有 26 条
  原样回显、2 条跑成英文。加一个示例、把 `-t` 降到 0.2 之后，60/60 全合格。
- 抽取/分类这类任务把 temperature 调低（`-t 0.2`）；格式要求写得越显式越好
  （「不要 markdown 代码块、不要解释」）。

## 八、本地结果一定要校验

省 token 的代价是质量。2B/9B 会：不守格式（偶尔包一层 markdown 代码块）、胡编事实、
漏字段、对同类问题给出前后不一致的答案。回执已经把格式类异常挑出来了，剩下这几条靠人：

- **事实类内容** → 只当草稿，回主模型或人工过一遍
- **抽样** → 几十条里抽 3–5 条人眼看一下，比全量盲信划算得多
- **解析失败的** → 重跑（`--resume`）或降级处理，别静默放过

## 九、启动 llama-server

**第一步永远是先查有没有已经在跑的**，重复启动会抢显存：

```bash
curl -s -m 2 http://127.0.0.1:8080/health   # {"status":"ok"} 就说明已就绪，直接用
```

启动 / 切换都用同一个命令（**幂等**，**默认 2B**）：

```bash
bash C:/Users/caill/.claude/skills/local-ai/scripts/start.sh           # 2B MiniCPM5，~85–107 tok/s，128K ctx
bash C:/Users/caill/.claude/skills/local-ai/scripts/start.sh 9b        # 9B-Distill，~55 tok/s，32K ctx
bash C:/Users/caill/.claude/skills/local-ai/scripts/stop.sh            # 收工：停掉并等显存回收
# Git Bash 别名（~/.bashrc）：llama = 2B，llama9 = 9B
# Windows CMD 用 start.bat / stop.bat（参数同上）
```

> `scripts` 目录本身已在用户 PATH 里，所以 `start.sh` / `stop.sh` / `llama` / `llama9` 都可以直接敲。

`start.sh` 已经在跑目标模型就 `[复用]` 不重启；跑着别的才先停后启。所以它同时是「启动」和「切换」，
不需要先手动查、也不需要先手动杀。

> ⚠️ **`start.sh` / `start.bat` 是前台阻塞进程**（内部 `exec llama-server`），它会一直占着终端。
> 在 Bash 工具里必须**后台启动**，否则会把当前调用卡死：
> 用 `run_in_background` 参数，或 `nohup bash .../start.sh > /tmp/llama.log 2>&1 &`。
> 启动后 `sleep` 几秒再 `curl /health` 确认就绪。

确认真的上了 GPU：`llama-server.exe --list-devices` → 应显示 `CUDA0: NVIDIA GeForce RTX 5060 Laptop GPU`。
确认实际加载的是哪个模型：`curl -s http://127.0.0.1:8080/v1/models`。

> **服务端默认开 4 个 slot**（`n_slots = 4`，auto 决定），这就是 `llama_batch.py` 默认并发 4 的依据。
> 启动时改过 `-np/--parallel` 的话，把 `-j` 对齐到那个数才有意义。

## 实测性能（2026-09-10 复测，b10883 / CUDA 13.3）

**MiniCPM5-2B Q8_0**（`-ngl 99`, `-c 131072`, KV q8_0）：

| 指标 | 实测 |
| --- | --- |
| decode（短输出 ~50 tok） | ~107 tok/s |
| decode（长输出 1500 tok） | ~85 tok/s |
| prefill | ~330 tok/s（冷启动）/ 1181 tok/s（前缀缓存命中） |
| 加载 | 约 2s（页缓存热）｜VRAM 6514 MiB / 8151 |

**Qwen3.8-9B-Distill Q4_K_M**（`-ngl 99`, KV q8_0）：

| `-c` | decode | prefill | VRAM |
| --- | --- | --- | --- |
| **32768（默认）** | **~55 tok/s** | ~172 tok/s | 整卡约 6.9 GB（含桌面） |
| 262144（256K 上限） | ~37 tok/s | — | 7561 MiB / 8151（近满） |

> 256K 比 32K 慢约 35%（55 → 37）：KV cache 几乎占满显存，日志会报
> `failed to fit params ... n_gpu_layers already set to 99`，部分层被挤到 CPU。
>
> ⚠️ **decode 随当前上下文长度衰减**：上下文到 ~15K 时实测约 **43 tok/s**（pi agent 真实负载）。
> 上表是短上下文（几百 tokens）的数字。
>
> 测量提示：**别用单次请求、也别在刚强杀过 server 后立即测** —— 显存未完全释放时部分层会被挤到 CPU，
> 读数能差一倍以上（曾在同样参数下测到 23 tok/s 的假值）。判断是否真上 GPU 请用 `--list-devices`，别靠速度猜。

## 注意事项

- **思考控制走请求级参数（重要）**：两个模型都是 thinking 模型，**默认开思考**。关闭思考要在
  **请求体**里传 `"chat_template_kwargs": {"enable_thinking": false}` —— 这是唯一有效的机制，
  两个脚本的 `--no-think` 已内置。实测代价对比（同一中文改写请求）：**关思考 8 tokens /
  开思考 158–300 tokens**。简单改写、分类、抽取、**所有批量任务**都建议关；推理、代码、多步任务留开。
- ⚠️ **服务端参数全部无效，不用再试**：`--reasoning off`、`--reasoning-budget 0`、
  `--chat-template-kwargs '{"enable_thinking":false}'` 在本机 build(b10883) 上实测**均不生效**
  （各 5/5 次仍在思考）；连 `--chat-template` / `--chat-template-file` 覆盖模板也不生效。
  根因是 llama.cpp 上游 bug：[PR #22336](https://github.com/ggml-org/llama.cpp/pull/22336) 至今 **OPEN 未合并**。
  **换 build 之前先复测，别假设新版本就好了。**
- **`content` 为空的兜底**：thinking 模型可能把内容全放进 `reasoning_content`；两个脚本都已处理
  （优先取 `content`，为空时回落 `reasoning_content`）。
- **必须用 b10883**：9B-Distill 是 `qwen35` 架构（含 `ssm.*` / Gated DeltaNet 张量），b10883 之前的
  llama.cpp 不认。MiniCPM5-2B 是普通 `llama` 架构，对版本不敏感。
- **GPU 生效判定**：别只看速度猜。`llama-server.exe --list-devices` 能看到 `CUDA0: ...` 才算真上 GPU；
  否则会**静默退回纯 CPU**（不报错、日志里连一行 CUDA 都没有，只是慢 10 倍）。
- **CUDA 版本**：本机为 CUDA 13（`cublas64_13.dll` / `cudart64_13.dll`），驱动 592.01。
  不要把 CUDA 12 版的 llama.cpp 构建混进来 —— 缺 `cublas64_12.dll` 会静默退回 CPU。
- **冷启动**：MiniCPM 约 2s、9B 约 4s（mmap 到 D 盘、页缓存热时）；强杀关闭即可，无后台驻留。
- **上下文**：显存只有 8G，KV cache 开太大会把速度打回去（见上表）。默认值已按显存调好。
- **端口**：默认 8080，可用脚本第二参数或 `--port` 修改；批量脚本可用环境变量
  `LLAMA_SERVER_URL` 指定完整端点。
- **温度**：MiniCPM 官方推荐 temp 1.0 / top_p 0.95；9B-Distill 官方推荐 temp 0.6 / top_p 0.95 / top_k 20。
- **不负责的**：视觉/OCR/音频 → mimo 或 `docling`；无 mmproj 文件，两个模型均**纯文本**。
