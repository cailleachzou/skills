---
name: cctv-cad
description: 摄像机覆盖范围 CAD 平面图生成工具。输入焦距/像素/传感器/安装高度等参数，自动输出 DXF 格式平面覆盖图，包含 DORI 分层扇形、盲区标注、距离刻度。触发词：画覆盖图、CAD摄像机覆盖、cctv coverage、摄像机平面图、点位覆盖、生成覆盖范围图。
type: cli-sub
---

# CCTV CAD 覆盖图生成

摄像机覆盖范围平面图自动生成工具 — 输入参数，输出 DXF。

## Prerequisites

- **ezdxf** — `pip install ezdxf`

## Commands

### `draw coverage` — 生成覆盖范围图

```bash
python scripts/draw_coverage.py --focal 4 --pixels 4mp --sensor 1/2.8 --height 3.0 --direction 0 --output camera_A1.dxf
```

**Parameters:**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--focal` | 4 | 焦距 (mm)：2.8/4/6/8/12 |
| `--pixels` | 4mp | 像素：2mp/4mp/8mp |
| `--sensor` | 1/2.8 | 传感器尺寸：1/3 ~ 2/3 |
| `--height` | 3.0 | 安装高度 (m) |
| `--tilt` | auto | 俯角 (°)，auto 按焦距推荐 |
| `--direction` | 0 | 朝向角度：0=右 90=上 180=左 270=下 |
| `--output` | - | 输出 DXF 路径 |
| `--dry-run` | false | 显示计算参数 |
| `--no-dori` | false | 去掉 DORI 分层 |
| `--no-blindspot` | false | 去掉盲区 |

**Examples:**

```bash
# 基本用法
python scripts/draw_coverage.py --focal 4 --pixels 4mp --sensor 1/2.8 --height 3.0 --direction 0 --output camera_A1.dxf

# 预览参数
python scripts/draw_coverage.py --focal 6 --pixels 8mp --sensor 1/1.8 --height 5.0 --dry-run

# 简洁模式
python scripts/draw_coverage.py --focal 4 --pixels 4mp --sensor 1/2.8 --no-dori --no-blindspot --output simple.dxf
```

## Output

DXF 文件包含以下图层：

| 图层 | 颜色 | 内容 |
|------|------|------|
| CAMERA | 白色 | 摄像机位置点 + 方向箭头 |
| FOV | 青色 | 视场角边界线 |
| DORI-I | 红色 | 辨识区域 (250 px/m) |
| DORI-R | 橙色 | 识别区域 (125 px/m) |
| DORI-O | 黄色 | 观察区域 (62 px/m) |
| DORI-D | 绿色 | 探测区域 (25 px/m) |
| BLINDSPOT | 红色 | 盲区三角形 |
| ANNOTATION | 灰色 | 距离刻度 + 参数标注 |

## DORI 标准

| 等级 | px/m | 用途 |
|------|------|------|
| I 辨识 | 250 | 人脸入库比对 |
| R 识别 | 125 | 人脸/车牌识别 |
| O 观察 | 62 | 行为分析 |
| D 探测 | 25 | 入侵检测 |

## For AI Agents

使用 `--dry-run` 验证参数再生成文件。传感器尺寸和 DORI 标准复用 cctv-focal-distance-tool 数据。
