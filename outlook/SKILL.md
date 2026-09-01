---
name: outlook
description: 通过 PowerShell COM 直连经典 Outlook 操作日历与邮件——添加/查询/修改/删除日程、列出文件夹树、列出/读取邮件、创建/修改/删除邮件草稿。当用户提到 Outlook、日历、日程、会议、待办提醒、邮件、收件箱、草稿、写信、安排时间等场景时务必使用,即使没明确说"Outlook"。本技能不依赖 MCP 服务器(MCP 的 outlook 在本机连接不稳定),直接调用本地 COM,且能自动拉起 Outlook,无需预先手动打开。
---

# Outlook 操作(COM 直连)

通过 `scripts/outlook.ps1` 操作本机经典 Outlook(Windows)。**不需要手动打开 Outlook**——COM 会自动拉起进程;若 Outlook 忙(启动/同步中)拒绝调用,脚本带重试自动处理。

## 调用方式

```bash
powershell -ExecutionPolicy Bypass -File "C:\Users\caill\.pi\agent\skills\outlook\scripts\outlook.ps1" -Action <动作> [参数...]
```

> ⚠️ 文件必须保持 **UTF-8 带 BOM** 编码。编辑过脚本后请重新加 BOM(否则 Windows PowerShell 5.1 会把中文按 GBK 解析导致乱码):
> `powershell -Command "$t=[IO.File]::ReadAllText('<脚本路径>',[Text.Encoding]::UTF8); [IO.File]::WriteAllText('<脚本路径>',$t,(New-Object Text.UTF8Encoding $true))"`

## 动作一览

### 日程
| 动作 | 说明 | 示例参数 |
|------|------|---------|
| `add-calendar` | 添加日程 | `-Subject 主题 -Start "2026-09-15 09:00" -End "2026-09-15 11:00" [-Location 地点] [-Body 备注] [-AllDay] [-ReminderMinutes 15]` |
| `list-calendar` | 查询日历 | `-DateFrom "2026-09-01 00:00" -DateTo "2026-09-30 00:00"` |
| `update-calendar` | 修改日程 | `-EntryId <id> -Subject ... [-Start ...] [-End ...] [-Location ...] [-Body ...]` |
| `delete-calendar` | 删除日程 | `-EntryId <id>` |

**全天日程**:加 `-AllDay`,`-Start`/`-End` 传日期即可(如 `-Start "2026-09-15" -End "2026-09-15"`,End 与 Start 同日会自动顺延一天)。

### 邮件
| 动作 | 说明 | 示例参数 |
|------|------|---------|
| `list-folders` | 列出整个文件夹树 | (无参数) |
| `list-mails` | 列出邮件 | `[-Folder 文件夹名] [-UnreadOnly] [-Limit 50]`(Folder 默认 Inbox,支持中文名:收件箱/草稿/已发送 等) |
| `get-mail` | 读取邮件或草稿全文 | `-EntryId <id>`(输出发件人、收件人、时间、附件清单、正文) |
| `create-draft` | 新建草稿(不发送) | `-To "a@x.com","b@x.com" [-Cc ...] [-Bcc ...] -Subject 主题 [-Body 正文] [-AttachmentPaths "C:\a.pdf"]` |
| `update-draft` | 修改草稿 | `-EntryId <id> [-Subject ...] [-Body ...] [-To ...] [-AttachmentPaths ...]` |
| `delete-draft` | 删除草稿 | `-EntryId <id>` |

## 关键注意事项

1. **正文一律走 HTMLBody,勿改回 Body**:本机 COM 实例下 `MailItem.Body` 属性写入/读回会损坏非 ASCII 文本(出现 `�` U+FFFD 与内容重复),脚本已自动把纯文本包装成 HTMLBody,经实测中文完全无损。
2. **EntryID 引用**:`list-calendar` / `list-mails` 输出的 EntryID 可直接用于后续 `get`/`update`/`delete`。
3. **时间格式**:`"yyyy-MM-dd HH:mm"`,中文系统可直接解析。
4. **多收件人**:`-To "a@x.com","b@x.com"`(逗号分隔多个)。
5. **删除操作**:只删除传入 EntryID 的那一项,按主题名确认后再执行。

## 使用示例

**用户:帮我在 Outlook 加一个 9 月中旬做前端面板的日程**
```
-Action add-calendar -Subject "做前端面板及管理端配线架" -Start "2026-09-15 09:00" -End "2026-09-15 11:00"
```

**用户:我今天有哪些日程?**
```
-Action list-calendar -DateFrom "2026-08-11 00:00" -DateTo "2026-08-12 00:00"
```

**用户:看看收件箱有什么未读**
```
-Action list-mails -UnreadOnly -Limit 20
```

**用户:给某人起草一封邮件**
```
-Action create-draft -To "someone@corp.com" -Subject "主题" -Body "正文内容"
```
