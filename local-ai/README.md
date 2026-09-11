# local-ai — 8GB 笔记本显卡上的本地模型层

> 在 **RTX 5060 Laptop 8GB** 上跑本地大模型，用 llama.cpp CUDA 加速，
> 把「批量小活」从主模型上下文里搬走：省 token、可离线、保隐私。
>
> 技能说明见 [`SKILL.md`](SKILL.md)；本文件讲**怎么装、装什么、以及 8GB 显存怎么用满但不撑爆**。

---

## 一、为什么一切选型都从「8GB」开始

这台机器是 **Lenovo 83LT 笔记本**：AMD Ryzen 9 8945HX（16C/32T）+ **NVIDIA RTX 5060 Laptop 8GB**
（GB206 / Blackwell / `sm_120` / CC 12.0）+ 32GB DDR5。

**笔记本 8GB 显存是本技能所有设计决策的唯一约束。** 服务端参数、模型规格、上下文长度、
并发数、量化级别 —— 没有一个是可以随便调的，全都得先过一遍显存账本。

### 1.1 显存账本（实测，`nvidia-smi`）

`nvidia-smi` 报的是**整卡占用**，包含桌面、浏览器、Windows 合成器等。

| 配置 | 整卡占用 | 余量 / 8151 MiB | 说明 |
| --- | --- | --- | --- |
| **2B Q8_0，128K ctx** | **6514 MiB** | ~1637 MiB | 日常默认，余量最舒服 |
| **9B Q4_K_M，32K ctx** | **~6900 MiB** | ~1250 MiB | pi agent / 复杂任务 |
| 9B Q4_K_M，256K ctx | 7561 MiB | ~590 MiB ⚠️ | **近满，速度掉 35%** |

> **256K 那次是反面教材**：KV cache 几乎占满显存（7561 / 8151 MiB，余量 ~590 MiB），
> decode 从 55 tok/s 掉到 37 tok/s —— **不报错，只是慢**。
> **8GB 卡上不要贪上下文**，默认值（2B → 128K / 9B → 32K）已经是按显存算过的。
>
> ⚠️ **别把 `failed to fit params ... n_gpu_layers already set to 99` 当成「掉 CPU」。**
> 它是 auto-fit 例程的 **WARN** —— 因为用户显式钉了 `-ngl`（本机脚本一律 `-ngl 99`），
> 它放弃自动分配、按用户值继续。实测 vl8 出现这条时照样 `offloaded 37/37 layers`。
> 正确判据是 **`offloaded N/N layers`** 与 **`--list-devices` 的 `CUDA0:`**。

**多模态四个模型（2026-09-11 实测整卡占用）**：

| 配置 | 整卡占用 | 余量 / 8151 MiB | 说明 |
| --- | --- | --- | --- |
| **vl4** Qwen3-VL-4B Q4_K_M | **6956 MiB** | ~1195 MiB | 视觉默认 |
| **vl8** Qwen3-VL-8B Q4_K_M | **7711 MiB** | ~440 MiB ⚠️ | 只在细粒度判别时用（见下） |
| **OCR** Unlimited-OCR（bf16） | **7782 MiB** | ~370 MiB ⚠️ | 权重 6.7 GB，贴边 |

`asr`（Qwen3-ASR-1.7B Q8_0，权重约 4.6 GB）未实测。这四个**同样受「一次只跑一个模型」约束** ——
切换走 `start.sh`，OCR 走 `ocr/run.sh`（它会先 `stop.sh` 腾显存）。详见 [`SKILL.md`](SKILL.md) 第十节。

> ⚠️ **`vl4` 不能拿来做细粒度判别。** 实测同一张图换个问法结论就翻（横版 A4 图问「是不是
> 手机截图」答「是」；问「属于哪一类」答「证件」）。凡是要拿结论当事实用的二值/闭集判断，
> **直接上 `vl8`**。理由与实测数据见 [`SKILL.md`](SKILL.md) 第十节。

### 1.2 两个模型怎么选出来的

| | **MiniCPM5-2B Q8_0**（默认） | **Qwen3.8-9B-Distill Q4_K_M** |
| --- | --- | --- |
| 权重文件 | 2.68 GB | 5.78 GB（5502 MiB） |
| 磁盘位置 | `D:\models\gguf\minicpm5-2b\` | `D:\models\gguf\qwen3.8-9b-distill\` |
| 默认上下文 | **131072（128K）** | **32768（32K）** |
| decode 实测 | ~85–107 tok/s | ~55 tok/s（32K） |
| Git Bash 别名 | `llama` | `llama9` |
| 定位 | 批量、长文本、并发、**pi agent 多步闭环** | 代码、长链推理这类真难的活 |

**为什么 2B 反而当默认？** 不是"降级备用"。它有 tool use（pi 拿它跑 agent 成立），
有 128K 上下文，覆盖面其实比 9B 更广；而且省下的 3GB 显存全给了 KV 池 ——
**8GB 卡上，上下文宽度比参数量更稀缺**。

**量化级别的选择也是显存逼出来的：**

- **2B 用 Q8_0 而不是 Q4** —— 权重才 2.68GB，8GB 装得绰绰有余。
  小模型对量化损失敏感，**装得下就用高精度**，别为省 1.3GB 换来塌缩式输出。
- **9B 用 Q4_K_M** —— 5.78GB 是 8GB 卡上的甜蜜点。往上 Q5_K_M（~6.8GB）权重就吃掉整卡，
  KV 没地方放；往下 Q3 质量开始明显掉。
- **KV cache 一律 `q8_0`**（`--cache-type-k q8_0 --cache-type-v q8_0`）——
  KV 占显存的一半左右，量化它等于白赚一倍上下文。

### 1.3 8GB 大概能装多大的模型

> 下述为**经验估算**（权重 = 文件大小，KV 随上下文线性增长），实际以 `nvidia-smi` 实测为准。

| 模型规模 | Q4_K_M 权重 | 8GB 上可行性 |
| --- | --- | --- |
| 2B–4B | 1.5–2.5 GB | ✅ 宽松，可上 Q8_0 + 128K ctx |
| **7B–9B** | **4.5–6 GB** | ✅ **上限区间**，Q4_K_M + 32K ctx，余量紧 |
| 12B–14B | 7–9 GB | ❌ 权重就爆了，或只能极小 ctx + 大量层跑 CPU |
| 30B+ | 18 GB+ | ❌ 免谈（MoE 例外，但本机未验证） |

**结论：8GB 的可用区间是 7B–9B @ Q4_K_M，且上下文要克制。** 这就是本技能的配置边界。

### 1.4 Blackwell 的硬门槛：必须 CUDA 13

RTX 5060 Laptop 是 **Blackwell（`sm_120` / CC 12.0）**，需要 **CUDA 12.8+** 的编译产物。

- 本机用 **CUDA 13.3** 预编译包（`b10883`）。
- **混进 CUDA 12 版的 llama.cpp 会静默退回纯 CPU** —— 缺 `cublas64_12.dll`，
  不报错、日志里连一行 CUDA 都没有，只是**慢 10 倍**。
- 该构建目录**自带** `cudart64_13.dll` / `cublas64_13.dll` / `cublasLt64_13.dll`，
  CUDA 13 runtime 已含，**不需要**另外下 cudart zip。
- ⚠️ **必须用 `b10883` 或更新**：9B-Distill 是 `qwen35` 架构（含 `ssm.*` / Gated DeltaNet 张量），
  更早的 llama.cpp 不认这个架构，加载直接失败。（2B 是普通 `llama` 架构，对版本不敏感。）

---

## 二、依赖清单

### ✅ 必须安装

| 依赖 | 本机版本 | 作用 | 怎么装 |
| --- | --- | --- | --- |
| **NVIDIA 驱动** | 592.01 | CUDA 13 + Blackwell 支持的地基 | NVIDIA 官网 / GeForce Experience |
| **llama.cpp（CUDA 13.x 预编译包）** | `b10883` | 推理引擎本体 | 下载 `llama-b10883-bin-win-cuda-13.3-x64.zip`，解压到<br>`C:\Users\caill\tools\llama-cpp\cuda-b10883\` |
| **GGUF 模型 ×2** | 见 §1.2 | 模型权重 | 放到 `D:\models\gguf\<模型名>\`（**建议放 D 盘**，合计 ~8.5GB） |
| **Python** | 3.14.7 | 跑 `llama_chat.py` / `llama_batch.py` | 系统已装，用 `py -3` 调用 |
| **curl** | Windows 自带 | `start.sh`/`stop.sh` 探测 server 状态 | 无需安装 |
| **nvidia-smi** | 驱动自带 | `stop.sh` 轮询显存回收 | 无需安装 |

> ⚠️ **Python 侧零第三方依赖。** 两个脚本只用标准库
> （`argparse` / `json` / `sys` / `time` / `os` / `urllib.request` / `concurrent.futures` / `datetime`），
> **没有 `requests`、没有 `openai`、没有 PyTorch**。所以不需要 venv、不需要 pip install。
> 这是刻意的：推理在 C++ 里做，Python 只是薄薄的 HTTP 客户端。

### 🔧 可选（按需）

| 依赖 | 本机版本 | 作用 | 怎么装 |
| --- | --- | --- | --- |
| **Git Bash** | Git 2.55.0 (MSYS2) | 跑 `.sh` 脚本；别名 `llama` / `llama9` | Git for Windows 自带 |
| **pi CLI** | 0.85.1 | 本地 agent 层（自己读写文件、多步闭环） | `npm i -g @earendil-works/pi-coding-agent` |

`pi` 的 provider 配置在 `~/.pi/agent/models.json`：

```jsonc
{
  "providers": {
    "llamacpp": {
      "baseUrl": "http://localhost:8080/v1",
      "api": "openai-completions",
      "apiKey": "no-key",
      "models": [
        { "id": "qwen3.8-9b-distill", "contextWindow": 32768,  "cost": { "input": 0, "output": 0 } },
        { "id": "minicpm5-2b",        "contextWindow": 131072, "cost": { "input": 0, "output": 0 } }
      ]
    }
  }
}
```

> ⚠️ `~/.pi/agent/settings.json` 的 `packages` 必须保持**清空**。
> 装了 `pi-subagents` 这类编排扩展会让小模型陷入**死循环**（实测 400s+ 零产出 vs. 清空后 11s）。
> 详见 [`SKILL.md`](SKILL.md) 用法 3。

### ❌ 刻意不装

| 不装 | 为什么 |
| --- | --- |
| **ollama** | 2026-09-10 已彻底卸载 —— 多一层进程、多占一份显存，直连 llama-server 更快更可控 |
| **PyTorch / transformers（装进系统 Python）** | 文本推理全在 llama.cpp（C++）里，不需要 Python 推理栈。OCR 栈确实要 torch + transformers，但**刻意隔离在独立 venv**（`D:\models\venvs\unlimited-ocr`），不污染系统 Python |

> **mmproj（视觉投影）原先在这张表里** —— 2026-09-11 起 `vl4` / `vl8` / `asr` 各自带一个，
> 视觉与音频已能**全本地**跑，不再需要回退 `mimo` 或 `docling`。见 [`SKILL.md`](SKILL.md) 第十节。

---

## 三、从零装一遍（复现步骤）

```bash
# 1. 确认驱动和显卡就位 —— 必须能看到 CUDA0
"C:/Users/caill/tools/llama-cpp/cuda-b10883/llama-server.exe" --list-devices
#    期望输出: CUDA0: NVIDIA GeForce RTX 5060 Laptop GPU
#    ⚠️ 看不到 CUDA0 = 已经静默退回 CPU，别继续往下走

# 2. 确认显存基线（空载时应该只有桌面占用，几百 MiB）
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv

# 3. 放好模型文件
ls -la "D:/models/gguf/minicpm5-2b/MiniCPM5-2B-Q8_0.gguf"        # 2.68 GB
ls -la "D:/models/gguf/qwen3.8-9b-distill/Qwen3.8-9B-Q4_K_M.gguf" # 5.78 GB

# 4. 启动（默认 2B）—— 在 Bash 工具里必须后台跑，见下方警告
bash C:/Users/caill/.claude/skills/local-ai/scripts/start.sh

# 5. 等几秒，确认就绪
curl -s http://127.0.0.1:8080/health          # {"status":"ok"}
curl -s http://127.0.0.1:8080/v1/models       # 核对实际加载的模型
```

> ⚠️ **`start.sh` / `start.bat` 是前台阻塞进程**（内部 `exec llama-server`），会一直占着终端。
> 在 Bash 工具里必须后台启动，否则会把当前调用卡死：
> 用 `run_in_background` 参数，或 `nohup bash .../start.sh > /tmp/llama.log 2>&1 &`。

### 把脚本指向你自己的环境

三个脚本里的绝对路径是**硬编码的**，换机器要么改脚本、要么建同样的目录：

| 变量 | 位置 | 当前值 |
| --- | --- | --- |
| `LLAMA_DIR` | `start.sh` / `start.bat` | `C:/Users/caill/tools/llama-cpp/cuda-b10883` |
| `MODEL_MINICPM` | `start.sh` / `start.bat` | `D:/models/gguf/minicpm5-2b/MiniCPM5-2B-Q8_0.gguf` |
| `MODEL_9B` | `start.sh` / `start.bat` | `D:/models/gguf/qwen3.8-9b-distill/Qwen3.8-9B-Q4_K_M.gguf` |

换模型时把这几个路径指到你的 GGUF 即可 —— 但**记得遵守 §1.3 的显存边界**：
8GB 卡上不要超过 9B @ Q4_K_M，上下文按 §1.1 的表给。

---

## 四、8GB 笔记本上的日常操作

### 4.1 一次只跑一个模型

`llama-server` 是**单模型进程**：一次只加载一个 GGUF，而且**忽略请求体里的 `model` 字段**。

- 选型是**轮次级**决策 —— 开工前看这一轮主要干什么，选一次跑到底。
- 切换 = 重启 server（加载 2–4s，**前缀缓存全丢**）。**不要为单条任务来回切。**
- 把这一轮所有该模型的活**攒在一起**跑完，再切。
- 单条 / 少量任务**不为它切模型** —— 有什么用什么。
- **要并发的任务、以及超过 32K 的单条任务，永远留在 2B** —— 9B 既不能并发，池子也只有 32K。

`start.sh` 本身就是幂等的，切换不用手动停：

```bash
bash C:/Users/caill/.claude/skills/local-ai/scripts/start.sh 9b   # 需要 9B 时才切
#   [复用] 已在跑目标模型 → 直接返回，不重启、不丢前缀缓存
#   [切换] 跑着别的 → 先 stop.sh（等显存真回收）再启
```

### 4.2 9B 不并发 —— 硬规则，不是偏好

要并发就切 2B。原因在于**KV 是共享池，不是每槽独享**：

启动日志写得很清楚：`n_slots = 4, n_ctx_slot = 32768, kv_unified = 'true'`。
`kv_unified` 意味着 4 个 slot 从**同一个 KV 池**里取，不是各拿一份 ——
`/slots` 会显示每槽 `n_ctx = 32768`，看着像 4 路各 32K，**其实不是**。

- 9B（`-c 32768`）：整池就是 32K，4 个 slot 共享它。
- 而且整卡也没余量了：实测 **6891 MiB / 8151**，其中模型权重本身占 5502 MiB，剩不到 1GB。
- 2B（`-c 131072`）：池子 128K、每槽 32K，没这个问题。

所以拿 9B 开并发，轻则互相挤、重则装不下。`llama_batch.py` 会在开跑前探测 server 上的模型，
跑着 9B 且 `-j > 1` 时直接警告，让你改 `-j 1` 或先切 2B。

并发实测（MiniCPM5-2B / `n_slots=4`，8 条任务）：

| 模式 | 墙钟 | 吞吐 |
| --- | --- | --- |
| 串行 | 3.0s | 84 tok/s |
| 并发 2 | 3.0s | 125 tok/s |
| **并发 4** | **2.0s** | **169 tok/s** ← 默认，约串行的 2 倍 |
| 并发 8 | 2.1s | 178 tok/s ← 超过 slot 数，收益基本没了 |

> **并发度对齐 `n_slots`（默认 4）才有意义**，超了只是排队。
> `llama_batch.py` 的 `-j` 默认就是 4 —— 但**只在 2B 上用**；server 跑着 9B 时脚本会警告。

### 4.3 收工必须 `stop.sh` —— 笔记本上尤其重要

`llama-server` **不会自己退出**，停在那儿就占着 **6–7GB 显存**，在 8GB 卡上等于把整台机器的
GPU 能力锁死。笔记本还额外付出**发热、风扇噪音、续航**的代价。

```bash
bash C:/Users/caill/.claude/skills/local-ai/scripts/stop.sh
```

`stop.sh` 杀进程后会**轮询显存直到真的回落**才返回，不是 `sleep` 固定秒数 ——
驱动回收显存有延迟，不等的话下次启动会有部分层掉到 CPU，**不报错只是慢十倍**。

> 一轮本地活干完、且没有后续任务时，就停掉它。尤其是用 `run_in_background` 起的那个 shell。

### 4.4 笔记本散热与功耗

- **插电跑**：电池模式下 GPU 会降频，实测速度打折；省电模式尤其明显。
- **跑模型时别同时开游戏 / 大型软件**：8GB 显存是共享的，被抢走 1GB 就可能触发层溢出到 CPU。
- **长批次任务注意机身温度**：16C CPU + 独显同时工作，垫高机身或加强散热有助于维持频率。
- **不用就停**：`stop.sh` 同时解决显存、发热、续航三个问题。

---

## 五、排障：8GB 卡上最容易踩的三个坑

| 症状 | 原因 | 怎么查 / 怎么修 |
| --- | --- | --- |
| **速度慢 10 倍，但不报错** | 静默退回纯 CPU（CUDA 版本不匹配 / 未释放的显存挤掉层 / `-ngl` 没生效） | `llama-server.exe --list-devices` 必须看到 `CUDA0:`。<br>**别靠速度猜**，也别在刚强杀过 server 后立即测 |
| **显存爆 / 部分层掉 CPU** | 上下文开太大（如 9B @ 256K）或并发超过 KV 池 | 看启动日志的 **`offloaded N/N layers`**（前后不等就是有层留在 CPU）；按 §1.1 的表回退 `-c`。⚠️ **不要用 `failed to fit params` 判断** —— 那只是「因 `-ngl` 被显式钉住而放弃自动分配」的告警，本机脚本一律 `-ngl 99`，它次次会误导 |
| **启动后加载失败 / 不认架构** | llama.cpp 版本太旧（9B 是 `qwen35` 架构，需 `b10883`+） | 换构建；**换 build 前先复测思考开关**（见 §6） |

**其他常见误判：**

- **`--model` 参数是标签，不是开关。** llama-server 忽略请求里的 model 字段；
  写 9B 但 server 跑着 2B，实际用的还是 2B，**不报错**。
  唯一闭环检查点：`curl /v1/models` 看实际加载的模型，或读 `llama_batch.py` 回执里的 server 模型名。
- **`start.sh` 显示 `[复用]` 不等于没生效** —— 那正是幂等设计，说明已经在跑目标模型。

---

## 六、本机构建上的已知限制（换 build 前必读）

### 思考开关只能在请求级做

两个模型都是 **thinking 模型，默认开思考**。关闭思考必须走**请求体**：

```json
"chat_template_kwargs": {"enable_thinking": false}
```

`llama_chat.py` / `llama_batch.py` 的 `--no-think` 已内置。代价对比（同一中文改写请求）：

> **关思考 8 tokens / 开思考 158–300 tokens** —— 省 90%+。

简单改写、分类、抽取、**所有批量任务**都建议关；推理、代码、多步 agent 任务留开。

⚠️ **服务端参数全部实测无效**（`b10883` 上各 5/5 次仍在思考）：
`--reasoning off`、`--reasoning-budget 0`、`--chat-template-kwargs '{...}'`，
连 `--chat-template` / `--chat-template-file` 覆盖模板也不生效。

根因是 llama.cpp 上游 bug：[PR #22336](https://github.com/ggml-org/llama.cpp/pull/22336) 至今 **OPEN 未合并**。
**换 build 之前先复测，别假设新版本就好了。**

### 其他

- **`content` 为空的兜底**：thinking 模型可能把内容全放进 `reasoning_content`；
  两个脚本都已处理（优先取 `content`，为空时回落 `reasoning_content`）。
- **加载时间**：MiniCPM 约 2s、9B 约 4s（mmap 到 D 盘、页缓存热时）；强杀关闭即可，无后台驻留。
- **端口**：默认 8080，可用脚本第二参数或 `--port` 修改；
  批量脚本可用环境变量 `LLAMA_SERVER_URL` 指定完整端点。
- **温度**：MiniCPM 官方推荐 temp 1.0 / top_p 0.95；9B-Distill 官方推荐 temp 0.6 / top_p 0.95 / top_k 20。
  抽取 / 分类类任务把温度压到 `-t 0.2`。

---

## 相关文档

- [`SKILL.md`](SKILL.md) — 技能全貌：派活三步法、三条派发路径、回执回流、prompt 实测经验
- [llama.cpp 官方仓库](https://github.com/ggml-org/llama.cpp) — 构建下载与参数文档
- `scripts/` — `start.sh` / `stop.sh` / `llama_chat.py` / `llama_batch.py` / `chat.sh`（+ `.bat` 版）

---

*最后更新：2026-09-10 · 对应技能版本 v6.2 · 硬件 RTX 5060 Laptop 8GB / 驱动 592.01 / llama.cpp b10883 (CUDA 13.3)*
