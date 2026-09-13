#!/usr/bin/env python3
"""重打 webapp-testing 的 Windows 进程树终止补丁。

背景
----
`with_server.py` 用 `shell=True` 起服务器，收服务器时调 `process.terminate()`。
在 Windows 上 `shell=True` 意味着命令跑在 `cmd.exe` 里，`terminate()` 只能杀掉这层
shell，真正干活的 `python.exe`（或 node.exe）会变成孤儿进程、继续占着端口——而脚本
照样打印 "All servers stopped"，具有误导性。

补丁内容（两处）
---------------
1. 加 `import os`
2. `finally` 块里 `process.terminate()` 之前插入分支：`os.name == "nt"` 时改用
   `taskkill /F /T /PID`，杀掉整棵进程树

为什么需要重打
-------------
该文件位于插件市场目录
`~/.claude/plugins/marketplaces/anthropic-agent-skills/skills/webapp-testing/scripts/`，
**`claude plugin update` 会覆盖它**。更新 example-skills 后重跑本脚本即可。

用法
----
    py -3 reapply-webapp-testing-win-patch.py [with_server.py 路径]

幂等：已打过补丁时直接退出 0，不重复改。行尾无关（CRLF/LF 均可），且保留原文件的行尾风格。
"""

import os
import sys

DEFAULT = os.path.join(
    os.path.expanduser("~"),
    ".claude", "plugins", "marketplaces", "anthropic-agent-skills",
    "skills", "webapp-testing", "scripts", "with_server.py",
)

# 已打补丁的标记
MARKER = "taskkill"

IMPORT_OLD = "import argparse\n"
IMPORT_NEW = "import argparse\nimport os\n"

TERMINATE_OLD = """            try:
                process.terminate()
                process.wait(timeout=5)
"""

TERMINATE_NEW = """            try:
                # On Windows the server runs under a shell (cmd.exe) because the
                # command is started with shell=True. terminate()/kill() would only
                # kill that shell, orphaning the real server process and leaving the
                # port occupied. Kill the whole process tree instead.
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    process.terminate()
                process.wait(timeout=5)
"""


def main():
    # Windows 控制台默认 cp1252，中文提示会在 print 时抛 UnicodeEncodeError；
    # 而文件此时已经写完，退出码却是 1，具有误导性。显式转 UTF-8。
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    if not os.path.isfile(path):
        print(f"错误：找不到文件 {path}")
        return 1

    raw = open(path, "rb").read().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")  # 归一化，后续匹配与行尾无关

    if MARKER in text:
        print(f"已是打过补丁的状态，无需处理：{path}")
        return 0

    for label, needle in (("import os", IMPORT_OLD), ("terminate 块", TERMINATE_OLD)):
        n = text.count(needle)
        if n != 1:
            print(f"错误：{label} 匹配到 {n} 处（应为 1 处）——上游文件结构已变，请人工核对。")
            return 1

    text = text.replace(IMPORT_OLD, IMPORT_NEW).replace(TERMINATE_OLD, TERMINATE_NEW)
    open(path, "wb").write(text.replace("\n", newline).encode("utf-8"))
    print(f"补丁已应用（行尾 {newline!r}）：{path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
