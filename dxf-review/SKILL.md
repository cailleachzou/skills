---
name: dxf-review
description: |
  DXF/DWG 视觉复查工具 — 渲染预览、多模态对比、自动验证。
  当用户需要检查 DXF 生成质量、对比原图、或进行视觉验证时触发。
  触发词：视觉复查、预览、DXF检查、对比原图、渲染看下。
---

# DXF Visual Review — 视觉复查流程

DXF/DWG 文件的渲染、预览、多模态对比、自动验证工具链。

## 工作流程

```
1. 生成 DXF/DWG
2. 渲染为 PNG 预览
3. 多模态读取对比（原图 vs 生成图）
4. 自动验证（尺寸、图层、闭合性）
5. 输出复查报告
```

## 命令

### `review render` — 渲染 DXF 为 PNG

```bash
python scripts/dxf_visual_review.py render INPUT.dxf [--output OUTPUT.png] [--dpi 150] [--size 10]
```

**参数：**
- `INPUT.dxf` — 输入 DXF 文件
- `--output` — 输出 PNG 路径（默认：<input>_review.png）
- `--dpi` — 分辨率（默认：150）
- `--size` — 图形尺寸英寸（默认：10）

**示例：**
```bash
python scripts/dxf_visual_review.py render flange.dxf
python scripts/dxf_visual_review.py render flange.dxf --output preview.png --dpi 200
```

### `review compare` — 多模态对比原图

```bash
python scripts/dxf_visual_review.py compare INPUT.dxf REFERENCE.png [--prompt "对比描述"]
```

**参数：**
- `INPUT.dxf` — 生成的 DXF 文件
- `REFERENCE.png` — 原始参考图片
- `--prompt` — 对比提示词（默认：对比这两个图，找出差异）

**功能：**
1. 渲染 DXF 为 PNG
2. 调用多模态 API 分析差异
3. 输出结构化对比报告

**示例：**
```bash
python scripts/dxf_visual_review.py compare flange.dxf original.png
python scripts/dxf_visual_review.py compare flange.dxf original.png --prompt "检查尺寸和角度是否正确"
```

### `review validate` — 自动验证

```bash
python scripts/dxf_visual_review.py validate INPUT.dxf [--spec spec.json]
```

**参数：**
- `INPUT.dxf` — 输入 DXF 文件
- `--spec` — 规格文件（JSON 格式，可选）

**验证项：**
- 实体数量与类型
- 闭合性检查
- 图层完整性
- 尺寸范围

**示例：**
```bash
python scripts/dxf_visual_review.py validate flange.dxf
python scripts/dxf_visual_review.py validate flange.dxf --spec flange_spec.json
```

### `review full` — 完整复查流程

```bash
python scripts/dxf_visual_review.py full INPUT.dxf [--reference REFERENCE.png] [--spec spec.json]
```

**功能：**
1. 渲染 PNG
2. 自动验证
3. 多模态对比（如果提供参考图）
4. 输出完整复查报告

**示例：**
```bash
python scripts/dxf_visual_review.py full flange.dxf --reference original.png
```

## 多模态能力

### 图片读取

```bash
python scripts/dxf_visual_review.py read-image IMAGE.png [--prompt "描述内容"]
```

**支持格式：** PNG, JPG, JPEG, BMP, WebP, GIF

**示例：**
```bash
python scripts/dxf_visual_review.py read-image original.png --prompt "提取图中的尺寸标注"
python scripts/dxf_visual_review.py read-image screenshot.png --prompt "识别所有文字"
```

### 音频/视频（通过 MiMo API）

音频和视频分析通过 Xiaomi MiMo API 处理（需配置 `MIMO_API_KEY` 环境变量）。

## 复查报告格式

```markdown
# DXF 复查报告

## 基本信息
- 文件：flange.dxf
- 生成时间：2026-07-07 13:10:00

## 渲染预览
![预览](flange_review.png)

## 自动验证
- ✅ 实体数量：17（10 圆，6 线，1 弧）
- ✅ 闭合性：所有轮廓闭合
- ✅ 图层：OUTLINE, HOLE, CENTER
- ⚠️ 警告：缺少 DIMENSION 图层

## 多模态对比
**原图：** 圆形法兰盘，四个耳片
**生成图：** 基本一致，角度偏移 30°

**差异：**
1. 耳片位置：原图在 30°+30°，生成在 0°/90°/180°/270°
2. 缺少过渡圆角 R5

## 建议
1. 调整耳片角度为 30° 和 330°
2. 添加 R5 过渡圆角
```

## 依赖

- **ezdxf** — DXF 读取与渲染
- **matplotlib** — PNG 渲染
- **Playwright** — 浏览器预览（可选）
- **mimo（可选多模态分析）** — `compare` / `read-image` 子命令调用
  `mimo-v2.5` 量计 API，凭据读环境变量 `MIMO_API_KEY`（sk- 开头）、
  `MIMO_BASE_URL`（默认 `https://api.xiaomimimo.com/v1`）、`MIMO_MODEL`。
  未设置密钥时自动降级为"手动对比"提示，不影响 render/validate。

## 常见问题

### Q: 中文显示为方框？
A: matplotlib 字体问题，使用 `matplotlib.font_manager` 指定中文字体：
```python
import matplotlib.font_manager as fm
font_path = fm.findfont(fm.FontProperties(family='SimHei'))
```

### Q: 渲染太慢？
A: 降低 DPI 或使用 `--size` 参数减小输出尺寸。

### Q: 如何批量复查？
A: 使用 shell 循环：
```bash
for f in *.dxf; do
  python scripts/dxf_visual_review.py full "$f" --reference "${f%.dxf}.png"
done
```
