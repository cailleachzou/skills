# CCTV CAD 覆盖图生成 — 设计文档

**日期**：2026-07-01
**作者**：DUDU & Cailleach
**状态**：Draft

## 概述

基于 ezdxf 实现的摄像机覆盖范围平面图自动生成工具，作为 `cli-anything` 子技能集成。

输入摄像机参数（焦距、像素、传感器、安装高度、俯角、朝向），输出 DXF 格式平面图，包含 DORI 分层覆盖扇形、盲区标注和距离刻度。

## 背景

现有 `cctv-focal-distance-tool`（焦距×像素×距离选型工具）提供立面图可视化，展示垂直方向覆盖。本工具补充平面图视角，展示水平方向覆盖范围，用于弱电安防项目方案设计。

## 需求

### 输入

命令行参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--focal` | 4 | 焦距 (mm)：2.8 / 4 / 6 / 8 / 12 |
| `--pixels` | 4mp | 像素：2mp / 4mp / 8mp |
| `--sensor` | 1/2.8 | 传感器尺寸：1/3 ~ 2/3 |
| `--height` | 3.0 | 安装高度 (m) |
| `--tilt` | auto | 俯角 (°)，auto 按焦距推荐值 |
| `--direction` | 0 | 摄像机朝向角度 (°)，0=右，90=上，180=左，270=下 |
| `--output` | - | 输出 DXF 路径 |
| `--dry-run` | false | 显示计算参数但不生成文件 |
| `--no-dori` | false | 去掉 DORI 分层 |
| `--no-blindspot` | false | 去掉盲区标注 |

### 输出

DXF 文件，平面俯视图（Z=0），包含：

1. 摄像机位置圆点 + 方向箭头
2. 覆盖扇形（水平 FOV 为张角）
3. DORI 分层同心弧（I/R/O/D 颜色）
4. 距离刻度标记
5. 盲区三角（摄像机后方红色填充）
6. 参数引线标注

### 图层结构

| 图层名 | 颜色 | 内容 |
|--------|------|------|
| `CAMERA` | 白色 | 摄像机位置点 + 图标 |
| `FOV` | 青色 | 视场角边界线 |
| `DORI-I` | 红色 | 辨识区域 (250 px/m) |
| `DORI-R` | 橙色 | 识别区域 (125 px/m) |
| `DORI-O` | 黄色 | 观察区域 (62 px/m) |
| `DORI-D` | 绿色 | 探测区域 (25 px/m) |
| `BLINDSPOT` | 红色 | 盲区三角形 |
| `ANNOTATION` | 灰色 | 距离刻度 + 参数标注 |

## 计算公式

复用现有选型工具公式：

```
水平视场角  H-FOV = 2 × arctan(Sensor_W / (2 × f))
垂直视场角  V-FOV = 2 × arctan(Sensor_H / (2 × f))
DORI 距离   D = (H_Pixels × f) / (Sensor_W × DORI_px/m)
盲区深度    B = H / tan(α + V-FOV/2)
```

DORI 像素密度标准：

| 等级 | px/m | 用途 |
|------|------|------|
| I 辨识 | 250 | 人脸入库比对 |
| R 识别 | 125 | 人脸/车牌识别 |
| O 观察 | 62 | 行为分析 |
| D 探测 | 25 | 入侵检测 |

传感器尺寸映射：

| 传感器 | 宽 (mm) |
|--------|---------|
| 1/3" | 4.8 |
| 1/2.8" | 5.12 |
| 1/2.7" | 5.3 |
| 1/2.5" | 5.76 |
| 1/2" | 6.4 |
| 1/1.8" | 7.18 |
| 1/1.7" | 7.6 |
| 2/3" | 8.8 |

## 架构

### 文件结构

```
cli-anything/sub-skills/cctv-cad/
├── SKILL.md
└── scripts/
    ├── draw_coverage.py     ← 主脚本
    └── constants.py         ← 传感器/DORI 常量
```

### 模块职责

- `constants.py`：传感器尺寸表、DORI 标准、默认俯角映射
- `draw_coverage.py`：参数解析 → 计算 → DXF 生成

### 依赖

- ezdxf（已安装）
- 无新依赖

## DXF 生成逻辑

1. 创建 DXF 文档，设置单位为米
2. 按图层结构创建图层
3. 计算参数：
   - 水平 FOV → 扇形张角
   - DORI 距离 → 4 段弧半径
   - 盲区深度 → 三角形尺寸
4. 绘制实体：
   - 扇形弧线（LWPOLYLINE 或 ARC）
   - 盲区三角（HATCH 填充）
   - 刻度线 + 文字
   - 参数标注（MTEXT）
5. 保存 DXF

## 用法示例

```bash
# 基本用法
python scripts/draw_coverage.py \
  --focal 4 --pixels 4mp --sensor 1/2.8 \
  --height 3.0 --tilt 30 --direction 0 \
  --output camera_A1.dxf

# 简洁模式（无 DORI 和盲区）
python scripts/draw_coverage.py \
  --focal 6 --pixels 8mp --sensor 1/1.8 \
  --height 5.0 --direction 90 \
  --no-dori --no-blindspot \
  --output camera_B2.dxf

# 预览参数
python scripts/draw_coverage.py \
  --focal 4 --pixels 4mp --sensor 1/2.8 \
  --height 3.0 --dry-run
```

## 错误处理

| 错误 | 处理 |
|------|------|
| 焦距不在支持列表 | 提示支持值：2.8/4/6/8/12 |
| 像素格式错误 | 提示：2mp/4mp/8mp |
| 传感器尺寸不支持 | 提示支持范围：1/3 ~ 2/3 |
| 输出路径不可写 | 报错 + 建议检查路径 |
| ezdxf 未安装 | `pip install ezdxf` |

## 参考

- [cctv-focal-distance-tool](C:\git-project\安防监控知识)
- [IEC 62676-4 DORI 标准]
- 现有 dwg 技能：`cli-anything/sub-skills/dwg/SKILL.md`
