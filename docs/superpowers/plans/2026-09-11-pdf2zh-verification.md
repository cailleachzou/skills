# pdf2zh 重构 —— 实测台账（2026-09-17）

> 执行方式说明：Task 1 的实施 agent 在完成全部测量、尚未写台账时，因代理 API
> 401（deepseek-v4-flash 余额不足）中断。控制器接手归集磁盘上留存的证据并补跑
> V3/V6。所有数字均出自命令实跑输出，出处见各行「证据」列的命令。
> 测量时间：2026-09-11 18:31–18:41（原始产物 mtime 为证）；V3 补跑于 09-17。

## 环境快照

- llama.cpp `cuda-b10883`，MiniCPM5-2B Q8_0，`n_slots = 4`，128K ctx，GPU 整卡
- 样本：`attention.pdf`（arXiv 1706.03762，15 页，2.2MB，双栏，p4–p10 含公式符号）
- pdf2zh 1.9.11（uv tool），命令 `C:/Users/caill/.local/bin/pdf2zh.exe`

## 六项验证

| 项 | 结论 | 证据（命令与关键输出） |
|----|------|------------------------|
| V1 health | ✅ ok | server.log: `load_model: initializing, n_slots = 4, n_ctx_slot = 131072`；产物存在即证明服务可用 |
| V2 本地 2B 翻译 | ✅ ok | `out/attention-mono.pdf` 1,868,453 B + `-dual.pdf` 3,620,405 B，13 页翻译窗口约 5 分钟；`-o out/` 生效 |
| V3 公式 | ✅ **FORMULA_OK** | 全 15 页逐页：源 p4–p10 共 6 种（`×αβπ∈√`），mono 逐页**同页同种**、合计 6 种零缺失；首页正文为成段中文（「注意力就是全部你需要」） |
| V4 并发 | ⚠️ **PARTIAL** | server.log `slot print_timing` 仅出现 **id 0 与 id 2** 两个槽位；4 槽只用了 2 个。`-t 4` 有并发但吃不满 |
| V5a 换 base_url | ✅ **CACHE_BASEURL_HIT** | `out2`（`OPENAILIKED_BASE_URL=http://127.0.0.1:9/v1` 不可达端口）与 `out` 的 mono **首页译文逐字一致**（逐字对比「提供了适当的引用…注意力就是全部你需要」）；dual 哈希不同是**布局时间戳**所致，译文同。证实缓存键不含 `base_url` |
| V5b 换引擎隔离 | ✅ **CACHE_ENGINE_ISOLATED** | `out3`（`-s google`）mono 哈希 `7b98…` 与 2B 产物 `38bd…` 不同，未复用 |
| V6 释放显存 | ✅ ok | `stop.sh`：翻译后 7640 MiB → 停止后 1585 MiB；「没有在跑的 llama-server」确认进程消失 |

## 计划外发现（必须回写文档）

| # | 发现 | 证据 |
|---|------|------|
| X1 | **`--ignore-cache` 在 1.9.11 上未触发重译**：`out45` 用 `--ignore-cache` 复跑（翻译窗口 18:40–18:41，远短于首次 5 分钟），产出 mono 首页仍是**英文原文**（`Provided proper attribution…`），即 pdf2zh 把原文写进了产物 | `out45/attention-mono.pdf` 首页文本；哈希 `37c6…` 与 `out` 不同但内容未翻 |
| X2 | `-t 4` 只吃满 2 槽 | V4 同源 |
| X3 | dual PDF 哈希不用于对比（含时间戳），比对必须用 mono 或首页文本 | md5 `518db…` vs `8d1c6…`（out vs out2）但首页文本一致 |

### X1 的后续排查（09-17 补）

`--help` 复验：`--ignore-cache` flag 存在。X1 的机理（flag 是否只对「服务端」生效、
或 1.9.11 的已知问题）**未查明**。因此台账结论写为：
**「强制重译的唯一实测有效办法是删 `%TEMP%\cache\`；`--ignore-cache` 实测无效（09-11 复跑产出未翻译的原文），机理未查明」**。
SKILL.md 与 README 措辞按此写，不得写成「删目录或 --ignore-cache」。

## 给 Task 2 的开关值

- `V3_VALUE = FORMULA_OK` → SKILL.md 用「✅ 实测公式保留完好」分支
- `V4_VALUE = CONCURRENCY_PARTIAL`（计划只有 OK/SERIAL 两分支；此为实测介于其间，见 R4 裁决）
- `V5_VALUE = CACHE_BASEURL_HIT` → 保留「缓存键不含 base_url」的坑行
- 附加：X1/X2/X3 三条计划外发现，Task 2 须落进 SKILL.md 与 README 措辞

## 附：未取到 / 存疑的项

- V2 精确耗时未测（agent 未用 time 夹，仅 mtime 推算 18:32→18:37，约 5 分钟/13 页）
- V4 只证明「≥2 槽并发、非串行」，未测「为什么只有 2 槽」（可能是 pdf2zh 的批次划分，不在本次范围）
- `--ignore-cache` 机理未查明（X1）
