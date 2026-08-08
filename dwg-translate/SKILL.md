---
name: dwg-translate
description: |
  DWG 电气图纸英译中 — AutoCAD COM 直连 DWG，提取全部文字，MIMO 批量翻译，回填后转回 *_ZH.dwg。
  当用户需要把外文（英文）DWG 电气图纸翻译成中文、翻译 CAD 图纸里的文字、或一键产出中文版 DWG 时触发。
  触发词：翻译、DWG、DXF、CAD、图纸、中文、电气、英文图纸、图纸翻译、_ZH。
---

# DWG Translate — 图纸英译中

输入英文（外文）DWG 电气图纸 → 中文 `*_ZH.dwg`。全程 5 步，用 **AutoCAD COM 直连**（DWG↔DXF 转换，AEC 对象完整保留）+ **ezdxf**（文字提取/回填）+ **MIMO**（批量翻译）。

## 工作流程

1. **DWG → DXF**：AutoCAD COM 打开 DWG，`SaveAs` 格式 25（ac2004 DXF）。AEC 专有对象（RoofSlab、Tablestyle、MLEADERSTYLE 等）完整保留，不会像 LibreDWG 那样丢失。
2. **文字提取**：ezdxf 读 DXF → Excel（11 列：序号|原文|译文|实体类型|空间|图层|X/Y/Z坐标|高度|旋转角度）。覆盖模型空间 + 布局 + 块定义 + INSERT 嵌套 ATTRIB。
3. **批量翻译**：MIMO API（mimo-v2.5）并发 6 请求，含缺失补译循环。175 条约 102 秒。
4. **回填到 DXF**：ezdxf 按 `{原文: 译文}` 内容匹配统一替换 TEXT/MTEXT/ATTDEF/ATTRIB（公司名/编号/代号自动保留不译）。
5. **DXF → DWG**：AutoCAD COM 打开翻译后 DXF，`SaveAs` 格式 24（ac2004 DWG）→ `*_ZH.dwg`。

## 命令

用独立 venv 的 Python 调用脚本（不要用裸 `python`）：

### 环境自检

```
C:\Users\59620\cad-translate-cli\.venv\Scripts\python.exe "C:\Users\59620\.claude\skills\dwg-translate\scripts\translate_dwg.py" --check
```

检查四项：venv 导入 / 运行时配置含 API key / AutoCAD 可连 / 输出目录可写。

### 一键翻译

```
C:\Users\59620\cad-translate-cli\.venv\Scripts\python.exe "C:\Users\59620\.claude\skills\dwg-translate\scripts\translate_dwg.py" "输入.dwg" [选项]
```

**参数：**

| 参数 | 说明 |
|------|------|
| `"输入.dwg"` | 必填，输入 DWG 路径 |
| `--output-dir DIR` | 输出目录（默认：与输入同目录） |
| `--target-language zh` | 目标语言（默认：读配置，zh） |
| `--keep` | 保留中间文件（DXF/Excel/翻译文件） |
| `--check` | 只做环境自检，不翻译 |

**示例：**
```
...python.exe ...translate_dwg.py "C:\Users\59620\Desktop\xxx.dwg" --keep
```
输出：`C:\Users\59620\Desktop\xxx_ZH.dwg` + 翻译 Excel。

## 依赖

| 依赖 | 说明 |
|------|------|
| **独立 venv** | `C:\Users\59620\cad-translate-cli\.venv\Scripts\python.exe`（Python 3.14，已装 ezdxf/pandas/pywin32/openpyxl/pydantic-settings） |
| **AutoCAD 2027** | ProgID `AutoCAD.Application.26`，exe `C:\Program Files\Autodesk\AutoCAD 2027\acad.exe`。**首次使用必须手动打开一次 AutoCAD** 完成 COM 注册与许可证初始化，之后脚本可自动启动 |
| **MIMO_API_KEY** | 已写入 `C:\Users\59620\.config\cli-anything-cad\config.json`（`llm.primary.api_key`） |
| **运行时配置** | 同上 config.json：`target_language=zh`、`translation_mode=replace`、`batch_size=12`、`parallel_count=6`、`model=mimo-v2.5` |

## 常见问题

- **Q: AutoCAD 连接失败 / Server execution failed？**
  A: 脚本已自动用 PowerShell `Start-Process` 启动 acad.exe 并轮询等待（最多 120 秒）。若仍失败，手动打开一次 AutoCAD 2027 完成初始化后重试。

- **Q: 输出中文乱码？**
  A: 本链路全程经 AutoCAD COM 读写，编码由 AutoCAD 保持，不会乱码。若自行用 ezdxf 加工 DXF 后乱码，保存前须设置 `doc.encoding`（GBK/`$DWGCODEPAGE` 一致性，参考旧 dwg 技能踩坑）。

- **Q: 翻译漏词 / 译文缺失？**
  A: MIMO 补译循环已兜底，未命中的保留原文。查看 `--keep` 保留的 Excel 译文列可人工补译后再走 `run_apply`。

- **Q: 想保留中间文件？**
  A: 加 `--keep`，工作目录在 `<output-dir>\dwg_translate_<随机>\`。

- **Q: 图纸没文字（纯图形）？**
  A: 脚本会检测提取文本数为 0 并报错。

## For AI Agents

- 调用固定用独立 venv Python（`C:\Users\59620\cad-translate-cli\.venv\Scripts\python.exe`），**不要用裸 `python`**。
- 先跑 `--check` 确认环境，再执行翻译。
- 大文件翻译耗时 1-3 分钟，用 `run_in_background` 后台运行；结束检查 `*_ZH.dwg` 是否存在且 >0 字节。
- 产出 `*_ZH.dwg` 后建议用 **dxf-review** 技能渲染对比原图验收（多模态对比）。
- 若要只做其中某一步，可直接调用项目 CLI（`cad-translate pipeline convert/extract/translate-excel/apply`）。
- 项目根目录：`C:\Users\59620\cad-translate-cli`（注意：已从桌面迁移到用户目录，勿用旧路径）。
