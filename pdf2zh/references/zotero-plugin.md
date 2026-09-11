# Zotero PDF2zh 插件

> ⚠️ **本节全部是上游口径，本机未实测。**
> 本机**没有**安装 Zotero，也没有装本插件的服务端。以下内容摘自
> `https://github.com/guaguastandup/zotero-pdf2zh`（v4.1.7，2026-08-27 快照）
> 与官方文档站 `https://zotero-pdf2zh.github.io`。**装之前请以官方文档为准。**
> 官方文档更新很快，本文件可能已过时。

## 是什么

在 Zotero 里直接调用 **pdf2zh** 或 **pdf2zh_next** 翻译 PDF 附件，保留公式与排版，并提供双语对照、裁剪阅读、批量翻译。

仓库：`guaguastandup/zotero-pdf2zh`（v4.1.7，6.2k star，支持 Zotero 7/8/9/10）。

**与本技能 CLI 部分的关系**：同一个翻译引擎的两个入口。插件的服务端是**另一套独立安装**，和本机的 `C:\Users\caill\.local\bin\pdf2zh.exe` 互不影响、互不依赖。

## 安装（上游步骤）

1. **服务端**：克隆/下载仓库后启动，默认端口 **8890**：

   ```bash
   # 上游 README 的启动方式（Windows）
   python server.py --port 8890 --config config.json
   ```

2. **插件**：从 Releases 下载 `.xpi`，在 Zotero 里「工具 → 插件 → 从文件安装」。

3. 在插件设置页把 **Python Server IP** 指向服务端，点旁边的「检查连接」验证连通性。

> 上游 README 明确提示：**插件和服务端要同时更新**，版本不匹配会出问题。

## 配置翻译服务（关键：两步，缺一不可）

1. **「LLM API 配置管理」** 区域点「新增」，填服务配置。同一服务可加多个配置，但**只能激活其中一个**。
2. 在页面顶部的 **「翻译服务」下拉菜单里选中**你要用的服务。

> ⚠️ 上游原话：**仅添加 API 配置不会生效，必须完成第二步选择服务。**

反过来，**免费服务**（如 `bing` / `google` / `siliconflowfree`）不需要自己配 API key。

## 接本地 2B 模型

插件里的 **`openaliked`** 就是「OpenAI 兼容端点」选项（注意拼写：插件 UI 写 `openaliked`，**少一个 `i`**；CLI 的服务名是 `openailiked`）。

在本机已有的 llama-server（`local-ai` 技能启动，默认 `127.0.0.1:8080`）基础上填：

| 字段 | 值 |
|------|-----|
| URL | `http://127.0.0.1:8080/v1` |
| API Key | 随意填（本地端点不校验） |
| Model | 任意标签，如 `minicpm5-2b` |

> ⚠️ 同 CLI 的坑：llama-server **忽略请求体里的 `model` 字段**，这个 Model 名只是标签；URL **必须带 `/v1`**。

## 插件自带的服务名（UI 口径）

| 插件 UI 服务名 | 说明 |
|----------------|------|
| `siliconflowfree` | 免费，**仅支持 pdf2zh_next 引擎**；限流，可能漏译 |
| `bing` / `google` | 免费机器翻译；**有限流**，失败就把并发数降到 2 及以下重试 |
| `openaliked` | **任意 OpenAI 兼容端点**（含本地 llama.cpp / vLLM / LM Studio） |
| `silicon` | 硅基流动；URL 填 `https://api.siliconflow.cn/v1`（**删掉后缀** `completions` 之类） |
| `zhipu` | 智谱；免费额度并发建议 ≤ 6 |
| `aliyunDashScope` | 通义；用「LLM API 配置管理」里的默认模型选项 |
| `deepseek` | 推荐 `deepseek-v4-flash`；默认关闭思考 |

## 两个引擎的配置差异

| | pdf2zh（老） | pdf2zh_next（新） |
|---|---|---|
| 配置文件 | `config.json` | `config.toml` |
| 服务数 | 多 | 多，且独有 `siliconflowfree` |

## 排错（上游口径）

| 现象 | 处理 |
|------|------|
| 检查连接失败 | 服务端没起 / 端口不对 / 防火墙 |
| 翻译失败或漏译 | 先看 API 是否超限（终端报错或服务商后台）；免费服务（bing/google）多为限流，切换更稳定的服务 |
| 段落缺失 | 翻译失败时程序会用原文替代。先排查 API 是否正常；pdf2zh_next 可在 LLM 配置的**额外参数**里开对应服务的 `*_enable_json_mode`（如 `openai_enable_json_mode`，**默认关闭**） |
| 生成文件过大 / 某次失败 | 尝试开启「兼容模式」（非必要不开） |

> 额外参数名需与 config 文件字段一致；v4.1.7 起可在「LLM API 配置管理」点「添加参数」从下拉选择。
