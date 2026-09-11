# 本机多模态能力扩展 — 设计文档

**日期**：2026-09-11
**范围**：在 `local-ai` 技能中新增视觉、语音识别、文档 OCR 三条本地能力路径
**状态**：待实施

---

## 1. 背景与目标

### 现状

本机的本地模型层（`local-ai` 技能）目前只覆盖纯文本：

- `llama-server`（llama.cpp b10883 / CUDA 13.3）加载单个 GGUF
- 两个模型：MiniCPM5-2B（默认）、Qwen3.8-9B-Distill
- 调用路径：`llama_chat.py`（单次）、`llama_batch.py`（批量 + 回执）、pi（本地 agent）
- 显存硬约束：RTX 5060 Laptop，8151 MiB 总量，桌面常驻约 1243 MiB

而所有多模态任务（图像/音频/文档）目前**全部外发**到 mimo 云 API 或走 `docling`。

### 目标

新增三条本地多模态路径，覆盖隐私敏感的资料：

| 能力 | 模型 | 解决的问题 |
|---|---|---|
| 视觉理解 | Qwen3-VL-4B / 8B | 图片内容理解、截图、图表 |
| 语音识别 | Qwen3-ASR-1.7B | 会议录音、访谈转写 |
| 文档 OCR | baidu/Unlimited-OCR | 扫描件、复杂版面、公式表格 |

### 驱动因素

**隐私 —— 资料不出本机。** 这一条决定了本设计的全部取舍：

- 量化精度优先于显存节省（在能装下的前提下选更高质量的档位）
- 全链路本地、可断网，不引入任何联网调用
- 信任边界尽量收敛到官方来源，第三方来源需显式知情

---

## 2. 决策记录

以下决策已在设计对话中逐条确认：

| # | 决策点 | 结论 |
|---|---|---|
| D1 | 驱动因素 | 隐私优先，资料不出本机 |
| D2 | VL 尺寸 | 4B + 8B 都下载，按需切换 |
| D3 | OCR 显存策略 | 保精度，跑前腾显存（bf16 原样跑） |
| D4 | ASR 模型来源 | 社区现成 GGUF |
| D5 | ASR 量化组合 | Q8_0 模型 + BF16 mmproj |
| D6 | 触发策略 | 自动优先本地，本地扛不动时回退 mimo |
| D7 | 入口范围 | 单次 + 批量都做 |
| D8 | 架构路线 | 路线 A：llama.cpp 主干 + Python OCR 特例 |
| D9 | 脚本组织 | 扩展现有脚本，不新建 |
| D10 | venv 位置 | `D:/models/venvs/unlimited-ocr/` |
| D11 | 敏感判定 | 显式标注优先 + 按内容类型自动判断（合同/证件/简历直接本地） |
| D12 | 视频 | 保留 mimo（本地无视频能力） |

### 路线 A 的核心思路

5 个模型里有 4 个能跑在同一个 `llama-server` 上，只有 OCR 是异类。因此：

- **能复用的最大化复用** —— `stop.sh` 的显存回收轮询、`llama_batch.py` 的回执机制、OpenAI 兼容 API 全部原样沿用
- **必须特殊的严格隔离** —— OCR 关在独立 venv 里，不污染系统 Python 3.14 环境

这与本机既有的 `.venv-docling` 是同一个模式。

**被否决的方案**：

- *全 Python 统一栈* —— VL 在 bfloat16 下需要 8 GB 以上，8 GB 卡直接跑不动；且现有 `start.sh` / `stop.sh` / 显存调度规则全部作废，代价不对等。
- *分两阶段（先 VL+ASR，OCR 另做一轮）* —— 用户明确要三个都做，且 OCR 大概率是隐私场景的核心。

---

## 3. 模型清单

### 3.1 下载清单（尺寸均为实测）

| 别名 | 文件 | 大小 | 来源 | 许可 |
|---|---|---|---|---|
| **vl4** | `Qwen3VL-4B-Instruct-Q4_K_M.gguf` | 2497 MB | `Qwen/Qwen3-VL-4B-Instruct-GGUF` | Apache-2.0 |
| | `mmproj-Qwen3VL-4B-Instruct-F16.gguf` | 836 MB | 同上 | |
| **vl8** | `Qwen3VL-8B-Instruct-Q4_K_M.gguf` | 5028 MB | `Qwen/Qwen3-VL-8B-Instruct-GGUF` | Apache-2.0 |
| | `mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf` | 752 MB | 同上 | |
| **asr** | `Qwen3-ASR-1.7B-Q8_0.gguf` | 2165 MB | `JamePeng2023/Qwen3-ASR-1.7B-GGUF`（社区） | Apache-2.0 |
| | `mmproj-Qwen3-ASR-1.7b-BF16.gguf` | 642 MB | 同上 | |
| **ocr** | `baidu/Unlimited-OCR` 全仓库（权重 6673 MB + 代码与资源） | ~6800 MB | 百度官方 | MIT |

**合计磁盘约 18.7 GB**（D 盘可用 466 GB，不构成约束）。

### 3.2 量化选择的依据

- **VL 必须 Q4_K_M**：F16 的 4B 要 8051 MB、Q8_0 的 8B 要 8710 MB，均超出可用显存。Q4_K_M 是唯一能装进 8 GB 的档位 —— 这是约束，不是偏好。
- **VL-4B 配 F16 mmproj，VL-8B 配 Q8_0 mmproj**：mmproj 负责图像编码，直接影响识别质量。4B 显存宽裕，用 F16 保质量；8B 权重已达 5028 MB，只能退到 Q8_0 抢出约 400 MB。
- **ASR 用 Q8_0 + BF16 mmproj**：1.7B 的模型量化收益极小 —— 从 BF16 全套（4712 MB）压到 Q4 全套（1503 MB）也只省 3.2 GB，而 ASR 根本不吃这么多显存。**这里量化换来的只有质量风险，没有收益。** BF16 mmproj 是必须的：音频投影器的量化版本有已知的质量退化。
- **OCR 用官方 bf16 原样**：对应 D3。

### 3.3 落盘路径

```
D:/models/gguf/qwen3-vl-4b/          {模型.gguf, mmproj.gguf}
D:/models/gguf/qwen3-vl-8b/          {模型.gguf, mmproj.gguf}
D:/models/gguf/qwen3-asr-1.7b/       {模型.gguf, mmproj.gguf}
D:/models/unlimited-ocr/             整个模型仓库（含自定义建模代码）
D:/models/venvs/unlimited-ocr/       Python 3.12 虚拟环境
```

**OCR 放在 `D:/models/` 下而非 `gguf/` 子目录**：它是一整个带 Python 代码的仓库（`modeling_unlimitedocr.py` / `deepencoder.py` 等），不是单个 GGUF。路径语义上区分开，避免日后误以为它能塞进 `llama-server`。

---

## 4. 显存调度

### 4.1 核心约束

现有的硬规则「**一次只跑一个模型**」是本设计的地基 —— 它让 8 GB 显存可以轮流服务 6 个模型，只要切换时正确回收显存。

### 4.2 模型矩阵

```
start.sh   minicpm │ 9b │ vl4 │ vl8 │ asr     ← 全部走 llama-server
ocr/       Python venv（transformers bf16）     ← 独立，跑前必须先 stop.sh
```

### 4.3 显存预算

可用显存 = 8151 − 桌面 1243 ≈ **6908 MB**。

| 别名 | 权重 + mmproj | KV 配置 | KV 占用 | 合计 | 余量 |
|---|---|---|---|---|---|
| `minicpm` 2B | 2680 MB | 128K / q8_0 | ~3.8 GB | ~6.5 GB | 现有，不动 |
| `9b` | 5502 MB | 32K / q8_0 | ~1.4 GB | ~6.9 GB | 现有，不动 |
| **`vl4`** | 2497 + 836 = 3333 MB | **16K / q8_0** | ~1.1 GB | **~4.5 GB** | 宽裕 |
| **`vl8`** | 5028 + 752 = 5780 MB | **8K / q8_0** | ~0.6 GB | **~6.4 GB** | 只剩 ~500 MB |
| **`asr`** | 2165 + 642 = 2807 MB | **32K / q8_0** | ~1.8 GB | **~4.6 GB** | 宽裕 |
| **`ocr`** | 6672 MB（bf16） | R-SWA，KV 恒定 | 极小 | **~6.9 GB** | 贴边 |

> KV 占用为估算值，依据各模型层数 / KV 头数 / head_dim 推算（VL-4B 与 VL-8B 约 144 KB/token，ASR 约 112 KB/token，均按 bf16 计，q8_0 KV 减半）。

### 4.4 上下文长度的依据

- **vl4 开 16K、vl8 只开 8K** —— 视觉模型被**图像 token** 消耗，不是文本。Qwen3-VL 一张常规图约 1000+ token（估算，实际随分辨率变化），多图或高分辨率还要翻倍。vl8 权重已占 5780 MB，8K 是其不出问题的上限。
- **asr 开 32K** —— 为**长录音**预留。1 小时中文语音转成文本约 1.5–2 万 token，32K 才能一次装下不截断。
- 全部沿用现有的 `--cache-type-k q8_0 --cache-type-v q8_0`，KV 直接减半。

### 4.5 vl8 的定位

vl8 是三个新模型中显存最贴边的一个（余量约 500 MB）。**它被定位为备用而非并列选项**：默认走 vl4，只有 4B 明显不足时才切过来。若实际运行溢出到 CPU，退路是把 ctx 降到 4K。

### 4.6 OCR 的调度

OCR 不归 `llama-server` 管，`start.sh` 的幂等逻辑覆盖不到它。给它一条显式前置流程：

```
跑 OCR  →  先 stop.sh（轮询等显存真的回落）  →  激活 venv  →  推理  →  释放
```

`stop.sh` 现有逻辑是「轮询显存直到真的掉下来」而非 `sleep` 固定秒数 —— OCR 这种贴边场景对显存残留最敏感，这段逻辑直接复用。

---

## 5. 脚本与调用层

### 5.1 脚本组织（D9：扩展而非新建）

现有 `llama_chat.py` / `llama_batch.py` 里最有价值的是**回执机制、并发、重试、`--resume`**。新建成等于把这些重写一遍，而加可选字段是向后兼容的 —— 现有纯文本用法一行都不用改。

### 5.2 `start.sh` 改动

新增三个模型分支：

```bash
bash start.sh vl4      # 视觉-4B（默认视觉模型）
bash start.sh vl8      # 视觉-8B（备用）
bash start.sh asr      # 语音识别
```

三个分支均为：

```
llama-server.exe -m <模型.gguf> --mmproj <mmproj.gguf> -ngl 99 \
  --host 127.0.0.1 --port <port> -c <ctx> --jinja \
  --cache-type-k q8_0 --cache-type-v q8_0
```

ctx 按 §4.3 表定。

**必须同步扩展 `running_model()` 的匹配** —— 现有实现靠匹配 `/v1/models` 返回的字串判断当前加载的模型：

```bash
case "$body" in
  *MiniCPM*)    echo minicpm ;;
  *9B-Q4_K_M*)  echo 9b ;;
  *)            echo unknown ;;   ← 新模型全部落到这里
esac
```

若不扩展，切换时会把「已经是目标模型」误判为 `unknown`，白白重启一次并丢掉前缀缓存。**这是本次实现最容易踩的坑。**

`start.bat` 需同步（Windows CMD 入口同样要能启动新模型）。

### 5.3 调用层改动清单

```
local-ai/scripts/
├── start.sh        加 vl4 / vl8 / asr 分支 + running_model 匹配扩展   [改]
├── start.bat       同步 CMD 入口                                      [改]
├── stop.sh         完全不动                                            [不改]
├── llama_chat.py   加 --image / --audio（可选参数，向后兼容）          [改]
└── llama_batch.py  JSONL 加 image / audio 字段                         [改]

local-ai/ocr/                                                           [新增]
├── run.sh          stop.sh → 激活 venv → 推理 → 释放
├── ocr.py          transformers 推理封装（含 PDF 逐页处理）
└── requirements.txt 固定版本（torch 2.10.0 / transformers 4.57.1 等）
```

> 注意目录区分：`local-ai/ocr/` 是**代码**（本仓库内，随技能版本管理），`D:/models/unlimited-ocr/` 是**权重**（见 §3.3，含自定义建模代码的模型仓库）。两者名字相近但职责不同。

### 5.4 API 格式

`llama-server` 的 `/v1/chat/completions` 支持 OpenAI 格式的多模态 content：

- **图像**：`{"type": "image_url", "image_url": {"url": "data:image/png;base64,<B64>"}}`
- **音频**：`{"type": "input_audio", "input_audio": {"data": "<B64>", "format": "wav"}}`

⚠️ 音频输入被 llama.cpp 官方标记为 **highly experimental**。若大文件出现异常，退路是启动时加 `--no-mmproj-offload`（音频编码器退回 CPU）。

### 5.5 调用长相

```bash
# 单张图
py -3 .../scripts/llama_chat.py --image photo.jpg "图里有什么"

# 批量：JSONL 每条绑定自己的文件
py -3 .../scripts/llama_batch.py scans.jsonl -o out.jsonl -j 4 --no-think
#   {"id":"p1","prompt":"转成 markdown","image":"page_001.png"}

# 长录音
py -3 .../scripts/llama_chat.py --audio meeting.wav "转写并分段落"

# OCR（独立栈）
bash .../ocr/run.sh --pdf contract.pdf --out ./out/
```

### 5.6 回执机制

`llama_batch.py` 跑完仍生成 `<out>.report.md`，含条数 / 失败 / 异常清单 / 抽样 / server 实际模型名。**多模态不改这套机制**，只新增两类异常：`文件读不到`、`音频解码失败`。

OCR 是独立栈，需自行产出一份同格式的回执。

---

## 6. 文档与边界

### 6.1 冲突的现状

| 文件 | 现写法 | 冲突点 |
|---|---|---|
| `~/.claude/CLAUDE.md` | 「遇图片/视频/音频**必须**走 mimo API」 | 与隐私决策直接冲突 |
| `local-ai/SKILL.md` | 「不负责的：视觉/OCR/音频 → mimo 或 docling」 | 把新能力挡在门外 |
| `skills/README.md` | 无多模态条目 | 项目规范要求技能增删改同步 |

### 6.2 改写后的规则

**默认走本地：**

- 文档 OCR、PDF／扫描件解析 → `ocr`
- 音频转写 → `asr`
- 图片理解、批量图片处理 → `vl4`
- 标记为敏感的资料 → 一律本地，不出本机

**回退 mimo：**

- **视频** —— 本地无视频模型，硬缺口（D12）
- 高质量开放式视觉推理（复杂图表分析、多图对比推理）
- 本地返回空结果 / 明显幻觉 / 连续失败

**敏感判定（D11）**：显式标注优先；同时按内容类型自动判断 —— 合同、证件、简历这类直接走本地。

### 6.3 docling 与 Unlimited-OCR 的分工

两者功能重叠，不写清楚会变成两条路做同一件事：

- **docling** → 文字型文档（PDF/DOCX/PPTX/XLSX 中本身就是文本的），快、准、结构化好
- **Unlimited-OCR** → 扫描件、复杂版面、公式/表格、需一次性解析的长文档

判定规则：**文档里有字可选 → docling；是扫描图 → OCR**。

### 6.4 改动清单

```
~/.claude/CLAUDE.md                  改「必须走 mimo」条    [改]
~/.claude/skills/local-ai/SKILL.md   加「多模态」章节 + 改边界  [改]
~/.claude/skills/README.md           同步技能说明与依赖        [改]
~/.claude/skills/local-ai/evals/     补多模态测试用例          [改]
```

---

## 7. 风险与未决

| 风险 | 影响 | 缓解 |
|---|---|---|
| OCR 显存贴边（6672 / 6908 MB） | 可能溢出到 CPU，速度骤降 | 跑前 stop.sh + 关占用显存的程序；接受变慢；必要时再评估量化 |
| vl8 余量仅 ~500 MB | 同样可能溢出 | 定位为备用；退路是 ctx 降到 4K |
| ASR 音频输入标记 experimental | 大文件可能失败 | `--no-mmproj-offload` 退路；长录音分段 |
| 社区 GGUF 来源（JamePeng2023） | 信任边界外移 | 已知情接受；GGUF 为纯权重+模板，风险低于 OCR 的 `trust_remote_code` |
| OCR 需 `trust_remote_code=True` | 执行仓库内自定义代码 | 百度官方 MIT 许可；已知情接受 |

> 曾经讨论过的「跨仓库混搭」风险（Q4 模型配另一仓库的 BF16 mmproj）**已规避**：ASR 的模型与 mmproj 同取自 JamePeng2023，不做跨仓库组合。

**未决**：无。所有决策点已在 §2 记录。

---

## 8. 验收标准

实施完成后，以下每一条都要有实际运行证据：

1. **四个新路径各自跑出正确结果** —— vl4 / vl8 / asr / ocr 各验证一条真实输入
2. **显存不溢出** —— 每个模型启动后 `nvidia-smi` 确认无层被挤到 CPU（对照 `--list-devices` 与启动日志）
3. **切换幂等** —— 连续两次 `start.sh vl4`，第二次必须打印 `[复用]` 而非重新加载
4. **批量回执正常** —— 多模态批量跑完生成 `<out>.report.md`，含 server 实际模型名
5. **纯文本用法未破坏** —— 现有 `llama_chat.py` / `llama_batch.py` 的文本用法回归通过
6. **文档同步** —— CLAUDE.md / SKILL.md / README.md 三处边界描述一致，无残留冲突

---

## 附：一句话总结

用**一个已经在用的显存调度规则**（一次只跑一个模型）和**一套已经在用的调用/回执机制**，把 6 个模型装进 8 GB 显存 —— 4 个跑在 llama.cpp 主干上，OCR 作为唯一例外隔离在独立 venv 里。
