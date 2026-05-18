---
name: email-eml
description: 生成 .eml 邮件文件。当用户提到"生成邮件"、"创建 eml"、"写邮件"、"发邮件"、".eml"时触发。支持：指定收件人(To)、主题(Subject)、正文（签名部分由用户手动添加）。
---

## 工作流程

```
1. 询问用户：收件人(To)、主题(Subject)、正文(Body，不含签名)
2. 拷贝模板 File.eml 到当前目录
3. 用 Edit 工具替换占位符
4. 完成，告知用户路径
```

## 步骤 1 — 询问

| 字段 | 说明 | 示例 |
|------|------|------|
| **To** | 收件人邮箱 | `someone@company.com` |
| **Subject** | 邮件主题 | `RE: 项目报价确认` |
| **Body** | 正文（不含签名，手动添加） | 多行文本 |

> 签名由用户手动在 Outlook 中添加，不要写在 Body 里。

## 步骤 2 — 拷贝模板

模板路径：
```
C:\Users\59620\.claude\skills\email-eml\templates\File.eml
```

拷贝到当前工作目录，文件名由用户指定（如 `Tendo - JYM报价.eml`）。

## 步骤 3 — 替换占位符

用 Edit 工具执行 3 次替换（`replace_all: true`）：

**替换 1 — 收件人：**
```
old: To: {{TO}}
new: To: {实际收件人邮箱}
```

**替换 2 — 主题：**
```
old: Subject: {{SUBJECT}}
new: Subject: {实际主题}
```

**替换 3 — 正文（两处）：**

3a. text/plain 部分：
```
old: {{BODY_PLAIN}}
new: {正文内容，每行直接写}
```

3b. text/html 部分：
```
old: {{BODY_HTML}}
new: {正文HTML版，\n\n 替换为 <br><br>，\n 替换为 <br>}
```

**正文格式规范：**
- 纯文本直接写，`\n` 视为换行
- 不需要写签名（由用户在 Outlook 中手动添加）

## 步骤 4 — 完成

告知用户：
- 输出文件路径
- 建议用 Outlook 打开，在签名区手动添加个人签名后发送

---

## 常用联系人

| 姓名 | 邮箱 | 备注 |
|------|------|------|
| 待添加 | 待添加 | — |

---

## 限制

- 暂不支持附件（v1.0）
- 签名由用户在 Outlook 中手动添加
- 编码 UTF-8（与正文无缝兼容）