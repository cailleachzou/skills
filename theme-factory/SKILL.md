---
name: theme-factory
description: Toolkit for styling artifacts with a theme. These artifacts can be slides, docs, reportings, HTML landing pages, etc. There are 10 pre-set themes with colors/fonts that you can apply to any artifact that has been creating, or can generate a new theme on-the-fly.
license: Complete terms in LICENSE.txt
---


# 主题工厂技能

本技能提供一套精心策划的专业字体与配色主题集合，每个主题都包含精心挑选的色板和字体搭配方案。选择主题后，即可应用于任何产出的文件。

## 目的

为演示文稿幻灯片或其他文件应用统一、专业的视觉样式。每个主题包含：
- 带有十六进制色值的统一配色方案
- 适合标题和正文的互补字体搭配
- 适用于不同场景和受众的鲜明视觉特征

## 使用说明

为幻灯片或其他文件应用样式：

1. **展示主题样例**：展示 `theme-showcase.pdf` 文件，让用户能够直观地看到所有可用主题。请勿对其进行任何修改，仅供查看。
2. **询问选择**：询问用户希望将哪个主题应用于当前文件
3. **等待确认**：获取用户对所选主题的明确确认
4. **应用主题**：用户选定主题后，将该主题的配色和字体应用于文件

## 可用主题

以下 10 个主题均在 `theme-showcase.pdf` 中有展示：

1. **Ocean Depths（深海蓝）** — 专业沉静的海事主题
2. **Sunset Boulevard（日落大道）** — 温暖活力的日落色彩
3. **Forest Canopy（森林树冠）** — 自然质朴的大地色调
4. **Modern Minimalist（现代极简）** — 简洁当代的灰度风格
5. **Golden Hour（黄金时刻）** — 浓郁温暖的秋季配色
6. **Arctic Frost（极地霜白）** — 清冷凛冽的冬日主题
7. **Desert Rose（沙漠玫瑰）** — 柔和雅致的灰调色调
8. **Tech Innovation（科技革新）** — 大胆现代的科技美学
9. **Botanical Garden（植物园）** — 清新生动的有机色彩
10. **Midnight Galaxy（午夜星河）** — 戏剧深邃的宇宙色调

## 主题详情

每个主题均在 `themes/` 目录下有完整定义，包含：
- 带有十六进制色值的统一配色方案
- 适合标题和正文的互补字体搭配
- 适用于不同场景和受众的鲜明视觉特征

## 应用流程

选定主题后：
1. 从 `themes/` 目录读取对应的主题文件
2. 在整个文件中一致地应用指定的配色和字体
3. 确保适当的对比度和可读性
4. 在所有页面保持主题的视觉一致性

## 创建自定义主题

如果现有主题均不适用，可以创建自定义主题。根据提供的需求，生成一个与上述主题风格相近的新主题。为主题取一个能描述字体/色彩组合的名称。根据用户提供的简要描述，选择合适的配色和字体。生成主题后，展示给用户审阅确认。确认后，按照上述流程应用主题。