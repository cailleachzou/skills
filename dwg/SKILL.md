---
name: dwg
description: |
  DWG 图纸操作 —— 转换（DWG↔DXF）、提取文字、翻译回填。
  当用户需要处理 DWG/DXF 图纸时使用：转换格式、提取文字、英译中/中译英图纸翻译、图纸文字识别、批量操作 CAD 文件。
  触发词：DWG、DXF、CAD、图纸、翻译、转换、提取文字、_ZH。
---

# DWG 操作 — 转换 / 提取 / 翻译

DWG 图纸一站式操作：**ODA File Converter**（DWG↔DXF 无损双向转换）+ **ezdxf**（文字提取/回填）+ **对话翻译**（主模型/子代理，无需 MIMO、无需 AutoCAD）。

## 能力

| 命令 | 功能 |
|------|------|
| `convert` | DWG↔DXF 双向转换（按扩展名自动判断方向） |
| `extract` | DXF 提取全部文字 → JSON 清单 + 待译原文 txt |
| `apply` | 按译文 JSON 回填 → `_ZH.dxf` |
| `convert-back` | 翻译后 DXF → DWG（`_ZH.dwg`） |
| `translate` | **一步到位**：DWG → 待译清单（中间 DXF 自动清理） |
| `apply-back` | **一步到位**：DWG + 译文JSON → `_ZH.dwg`（中间 DXF 自动清理） |
| `check` | 环境自检 |

## 工作流（翻译图纸，Agent 执行）

```
① convert  DWG → DXF
② extract  DXF → texts.json + unique_texts.txt（去重待译原文）
③ 翻译     Agent 在对话中翻译 unique_texts.txt（或调 MIMO）
           译文格式: JSON 对象 {原文: 译文}
④ apply    DXF + 译文 JSON → _ZH.dxf
⑤ convert-back  _ZH.dxf → _ZH.dwg
```

**Agent 操作要点**：
- 每步用 subagent 执行脚本命令，减少主上下文污染
- 步骤③翻译量较大时，开子代理（`worker`）翻译后返回 JSON
- 回填按 `{原文: 译文}` 精确匹配，**原文必须与提取清单完全一致**（含空格/大小写）
- 公司名/编号/代号等无需翻译的，译文保持原文即可（或从清单中剔除）

## 命令

用系统 Python（`py -3`，已装 ezdxf 1.4.4），**不要用裸 `python`**。

```
py -3 "C:\Users\caill\.pi\agent\skills\dwg\scripts\dwg.py" check
py -3 "C:\Users\caill\.pi\agent\skills\dwg\scripts\dwg.py" convert "输入.dwg"
py -3 "C:\Users\caill\.pi\agent\skills\dwg\scripts\dwg.py" extract "输入.dxf"
py -3 "C:\Users\caill\.pi\agent\skills\dwg\scripts\dwg.py" apply "输入.dxf" "译文.json"
py -3 "C:\Users\caill\.pi\agent\skills\dwg\scripts\dwg.py" convert-back "输入_ZH.dxf"
```

**示例（完整翻译，一步到位，无中间 DXF 残留）**：
```
py -3 ...dwg.py translate "C:\xx\input.dwg"        # → input_待译.txt（去重待译清单）
# Agent 翻译 input_待译.txt → translations.json  {"原文":"译文", ...}
py -3 ...dwg.py apply-back "C:\xx\input.dwg" "C:\xx\translations.json"  # → input_ZH.dwg
```
中间 DXF 全程在临时目录，命令结束后自动清理，用户只看到输入 DWG 和输出 `_ZH.dwg`。

**分步示例（想保留中间文件时）**：
```
py -3 ...dwg.py convert "C:\xx\input.dwg"          # → input.dxf
py -3 ...dwg.py extract "C:\xx\input.dxf"          # → 输出目录 texts.json / unique_texts.txt
# Agent 翻译 unique_texts.txt → translations.json  {"原文":"译文", ...}
py -3 ...dwg.py apply "C:\xx\input.dxf" "C:\xx\translations.json"   # → input_ZH.dxf
py -3 ...dwg.py convert-back "C:\xx\input_ZH.dxf"  # → input_ZH.dwg
```

## 依赖

| 依赖 | 说明 |
|------|------|
| Python 3 + ezdxf | `py -3`（ezdxf 1.4.4 已装；缺则 `py -3 -m pip install ezdxf`） |
| ODA File Converter | `C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe`（已装）。免费，ODA 官网下载 |
| 翻译引擎 | 无固定依赖：默认对话/子代理翻译；也可配 MIMO（`mimo-v2.5`）或本地 llama.cpp |

## 已知问题与排查

- **ODA 转换失败**：输出目录会出现 `*.err` 文件，内容含具体报错行号。多为 DXF 编码混乱（GBK/UTF-8 混合）或实体结构损坏。先 `extract` 看能否读取，或先经 ezdxf 重存规范化编码再转换。
- **回填命中率低**：译文原文与清单不一致（多余空格/换行/大小写）。用 `texts.json` 的 `text` 字段逐字复制，不要手打。
- **图纸没文字**：`extract` 报"未提取到任何文本"，说明纯图形图纸。
- **AutoCAD 兼容性**：ODA 产出 ACAD2018 格式 DWG，AutoCAD 2008+ 可开。需要旧版本改 `dwg.py` 顶部 `ACAD_VERSION`（ACAD2004/2007/2010/2013/2018）。

## For AI Agents

- 固定用 `py -3` 调用 `C:\Users\caill\.pi\agent\skills\dwg\scripts\dwg.py`。
- 翻译步骤优先开 `subagent`（worker）执行：把 `unique_texts.txt` 内容交给子代理翻译，返回 JSON 对象。
- 大文件转换 ODA 耗时 10-60 秒；`convert`/`convert-back` 用后台运行并检查产物大小 >0。
- 产出 `_ZH.dwg` 后建议渲染对比原图验收（可用 mimo 多模态对比截图）。
- 本 skill 由 dwg-translate 重构而来：转换弃用 AutoCAD COM（宽容吞错导致坏文件），改用 ODA（严格校验、报错明确）；翻译弃用 MIMO 依赖，改为对话/子代理。
