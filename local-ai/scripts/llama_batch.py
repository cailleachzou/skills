#!/usr/bin/env python3
"""本地 LLM 批量调用 —— 把 N 条任务并发打到 llama-server (CUDA GPU)。

适合「很多条互不依赖的小任务」：批量改写、逐条分类、逐条抽取字段、批量摘要。
单次调用请用 llama_chat.py；本脚本的价值在于**并发**。

为什么并发有效（本机实测，MiniCPM5-2B / RTX 5060 Laptop / n_slots=4）:
    串行      84 tok/s
    并发 2   125 tok/s
    并发 4   169 tok/s   ← 默认值，约等于串行的 2 倍吞吐
    并发 8   178 tok/s   ← 超过 slot 数，收益基本没了

    服务端默认 n_slots=4（auto），所以 -j 默认也是 4。如果你启动 server 时改过
    -np/--parallel，把它对齐到这个数才有意义 —— 超过 slot 数的并发只是排队。

用法:
    py -3 llama_batch.py tasks.txt                      # 每行一条 prompt
    py -3 llama_batch.py tasks.jsonl -o out.jsonl -j 4 --no-think
    py -3 llama_batch.py tasks.txt --system "只输出翻译结果，不要解释"

输入格式（-f auto 时自动探测：首行能解析成 JSON 对象 → jsonl，否则 text）:
    text  : 每行一条 prompt（空行跳过）
    jsonl : {"id": "任意标识", "prompt": "必填", "system": "可选", "max_tokens": 100,
             "temperature": 0.3}
            只有 prompt 必填，其余字段按需覆盖全局默认值。

输出：JSONL，每条一行，**保持输入顺序**（并发完成顺序会乱，已重排）:
    {"index": 0, "id": "0", "prompt": "...", "result": "...",
     "completion_tokens": 42, "elapsed": 1.8, "error": null}

    result 为 null 且 error 非空 = 这条失败了（其余照常执行，不会整批中断）。

回执（给主模型「整体看一下」用）:
    跑完自动在输出文件旁边写一份 <out>.report.md（out.jsonl → out.report.md），内含
    条数/成功/失败、异常清单（失败、空结果、原样回显、带代码块围栏、JSON 解析失败、过短）、
    抽样几条、以及 **server 实际加载的模型名**。
    主模型只读这份回执就够了，**不要**把全量 out.jsonl 读进上下文 —— 那等于把省下的
    token 又原样花回去，还比自己做更慢。

思考控制（重要，同 llama_chat.py）:
    两个模型都是 thinking 模型，**默认开思考**。批量任务多是改写/分类/抽取这类
    不需要推理的活，加 --no-think 能省 90% token（实测同一改写请求：关思考 8 tokens
    / 开思考 158~300 tokens）。
    开关只能走请求级 chat_template_kwargs —— server 启动参数实测全部无效
    （llama.cpp 上游 bug，PR #22336 未合并）。

断点续跑:
    跑到一半挂了，重跑时加 --resume，会读已有输出文件、跳过已完成的行，
    只补没跑完的，最后合并成一个完整有序的文件。
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

SERVER_URL = os.environ.get("LLAMA_SERVER_URL",
                            "http://127.0.0.1:8080/v1/chat/completions")


def _pick_text(message: dict) -> str:
    """取正文；content 为空时回落 reasoning_content。"""
    return (message.get("content") or "").strip() or \
           (message.get("reasoning_content") or "").strip()


def _detect_format(path: str) -> str:
    """首行能解析成 JSON 对象就是 jsonl，否则按纯文本行处理。"""
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                return "jsonl" if isinstance(obj, dict) else "text"
            except json.JSONDecodeError:
                return "text"
    return "text"


def _load_tasks(path: str, fmt: str) -> list:
    if fmt == "auto":
        fmt = _detect_format(path)

    tasks = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f):
            if not line.strip():
                continue
            if fmt == "jsonl":
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    sys.exit(f"[错误] 第 {lineno+1} 行不是合法 JSON: {e}")
                if not obj.get("prompt"):
                    sys.exit(f"[错误] 第 {lineno+1} 行缺少 prompt 字段")
                tasks.append(obj)
            else:
                tasks.append({"prompt": line.rstrip("\n")})
    if not tasks:
        sys.exit(f"[错误] 没有读到任何任务：{path}")
    return tasks


def _load_done(path: str) -> dict:
    """读已有输出，返回 {index: record}，供 --resume 跳过。"""
    done = {}
    if not path or not os.path.exists(path):
        return done
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # 上次写到一半被打断的残行，忽略
            if rec.get("error") is None:
                done[rec["index"]] = rec
    return done


def _call(task: dict, index: int, opts) -> dict:
    """单条调用：超时/报错都记进 error 字段，不抛出去打断整批。"""
    prompt = task["prompt"]
    payload = json.dumps({
        "model": "local",
        "messages": ([{"role": "system", "content": task.get("system") or opts.system}]
                     if (task.get("system") or opts.system) else []) +
                    [{"role": "user", "content": prompt}],
        "max_tokens": task.get("max_tokens", opts.max_tokens),
        "temperature": task.get("temperature", opts.temperature),
        "chat_template_kwargs": {"enable_thinking": bool(opts.think)},
    }).encode("utf-8")

    last_err = None
    for attempt in range(opts.retries + 1):
        req = urllib.request.Request(
            SERVER_URL, data=payload, headers={"Content-Type": "application/json"})
        t = time.time()
        try:
            with urllib.request.urlopen(req, timeout=opts.timeout) as resp:
                data = json.load(resp)
            usage = data.get("usage", {})
            return {
                "index": index,
                "id": task.get("id", str(index)),
                "prompt": prompt,
                "result": _pick_text(data["choices"][0]["message"]),
                "completion_tokens": usage.get("completion_tokens", 0),
                "elapsed": round(time.time() - t, 2),
                "error": None,
            }
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            if attempt < opts.retries:
                time.sleep(1.5)  # 多半是瞬时排队/超时，退一步再试

    return {"index": index, "id": task.get("id", str(index)), "prompt": prompt,
            "result": None, "completion_tokens": 0, "elapsed": None, "error": last_err}


def _report_path(out_path: str) -> str:
    """out.jsonl → out.report.md；别的名字直接追加 .report.md。"""
    if out_path.lower().endswith(".jsonl"):
        return out_path[: -len(".jsonl")] + ".report.md"
    return out_path + ".report.md"


def _probe_model() -> str:
    """探测 server 实际加载的模型名。

    llama-server 一次只装一个模型、且**忽略请求体里的 model 字段**，所以这才是
    「这批活到底是谁跑的」的真相 —— 「想跑 2B 结果挂着 9B」这类错误在这里一眼可见。
    """
    url = SERVER_URL.split("/v1/")[0].rstrip("/") + "/v1/models"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.load(resp)
        # server 报的是 GGUF 全路径，回执里只留文件名就够认人了
        ids = [os.path.basename(str(m["id"]).replace("\\", "/"))
               for m in data.get("data", []) if m.get("id")]
        return ", ".join(ids) if ids else "(server 未报告模型名)"
    except Exception as e:
        return f"(探测失败: {type(e).__name__})"


def _unfence(text: str) -> str:
    """剥掉 markdown 代码块围栏，好判断里面到底是不是合法 JSON。"""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def _anomalies(rec: dict, global_system: str) -> list:
    """给单条结果打异常标签；返回空列表 = 看着正常。"""
    if rec.get("error"):
        return ["失败"]

    text = (rec.get("result") or "").strip()
    if not text:
        return ["空结果"]

    tags = []
    if len(text) < 3:
        tags.append("过短")
    if text == (rec.get("prompt") or "").strip():
        tags.append("原样回显")
    if text.startswith("```"):
        tags.append("带代码块围栏")

    # 任务里提到 JSON，结果就该能 parse —— 这是最常见的「看着成功、其实废了」
    hint = f"{rec.get('system') or global_system or ''} {rec.get('prompt') or ''}".lower()
    if "json" in hint:
        try:
            json.loads(_unfence(text))
        except json.JSONDecodeError:
            tags.append("JSON 解析失败")
    return tags


def _clip(text, limit: int = 120) -> str:
    """回执里的单行摘要：压掉换行、超长截断。"""
    s = " ".join(str(text or "").split())
    return s if len(s) <= limit else s[:limit] + "…"


def _write_report(out_path: str, ordered: list, args, elapsed: float) -> str:
    """把回执写到输出文件旁边，返回路径。

    这是「主模型整体看一下」的全部输入 —— 故意压到几十行，好让它不必碰全量结果。
    """
    path = _report_path(out_path)
    by_index = {r["index"]: r for r in ordered}
    tagged = [(r["index"], _anomalies(r, args.system)) for r in ordered]
    tagmap = dict(tagged)
    bad = [(i, tags) for i, tags in tagged if tags]
    failed = [i for i, tags in tagged if "失败" in tags]
    total_tok = sum(r.get("completion_tokens") or 0 for r in ordered)

    # 抽样：首 / 中 / 尾，外加第一条异常 —— 覆盖面够，又不至于让主模型读全量
    picks, seen = [], set()
    if ordered:
        for i in (ordered[0]["index"], ordered[len(ordered) // 2]["index"], ordered[-1]["index"]):
            if i not in seen:
                seen.add(i)
                picks.append(i)
    if bad and bad[0][0] not in seen:
        picks.append(bad[0][0])

    out = [
        f"# 批量回执 — {os.path.basename(out_path)}",
        "",
        f"- 生成：{datetime.now():%Y-%m-%d %H:%M}",
        f"- 输入：{args.input}（{len(ordered)} 条）",
        f"- 输出：{out_path}　← 全量结果在这里，按需再读，别整个读进来",
        f"- **server 实际模型**：{_probe_model()}",
        f"- 并发 {args.jobs} ｜ thinking {'on' if args.think else 'off'} ｜ "
        f"{elapsed:.1f}s ｜ {total_tok} tok ｜ {total_tok / elapsed if elapsed else 0:.1f} tok/s",
        "",
        "## 计数",
        "",
        f"总 **{len(ordered)}** ｜ 成功 {len(ordered) - len(failed)} ｜ "
        f"失败 **{len(failed)}** ｜ 异常 **{len(bad)}**",
        "",
        "## 异常清单",
        "",
    ]

    if not bad:
        out.append("无。")
    else:
        out += ["| index | 标签 | 摘要 |", "| --- | --- | --- |"]
        for i, tags in bad[:20]:
            rec = by_index[i]
            out.append(f"| {i} | {'/'.join(tags)} | {_clip(rec.get('error') or rec.get('result'))} |")
        if len(bad) > 20:
            out.append(f"| … |  | 其余 {len(bad) - 20} 条见 {out_path} |")
    out.append("")

    out += ["## 抽样", ""]
    for i in picks:
        rec = by_index[i]
        tags = tagmap.get(i) or []
        label = "异常: " + "/".join(tags) if tags else "正常"
        out.append(f"- **#{i}**（{label}）{_clip(rec.get('result') or rec.get('error'))}")
    out.append("")

    # 连接类失败和「模型答得不好」是两回事，别给出误导性的建议
    conn_marks = ("URLError", "Timeout", "timeout", "ConnectionReset", "RemoteDisconnected")
    all_conn = bool(failed) and all(
        any(m in (by_index[i].get("error") or "") for m in conn_marks) for i in failed
    )

    advice = []
    if all_conn:
        advice.append("失败全是连接类错误 —— 先确认 server 在跑："
                      "`curl -s http://127.0.0.1:8080/health`；刚切过模型的话等几秒再试。")
    elif failed:
        advice.append(f"失败 {len(failed)} 条：修好后加 `--resume` 只补这些，不用整批重跑。")
    if {t for _, tags in bad for t in tags} & {"原样回显", "JSON 解析失败", "带代码块围栏"}:
        advice.append("格式类异常多半是 prompt 没给 one-shot 示例 —— 见 SKILL.md「写 prompt 的实测经验」。")
    if len(bad) > len(ordered) * 0.3 and not all_conn:
        advice.append("异常率超过三成，先改 prompt 小批量试跑，别急着全量重来。")
    if not advice:
        advice.append("无异常，可进落地闸门：低风险自动落地，覆盖/外发/不可逆的先确认。")
    out += ["## 建议", ""] + [f"- {a}" for a in advice] + [""]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return path


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    p = argparse.ArgumentParser(
        description="本地 LLM 批量并发调用（llama-server / CUDA GPU）",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", help="任务文件：每行一条 prompt，或 JSONL（含 id/prompt/system）")
    p.add_argument("-o", "--output",
                   help="输出 JSONL 路径（默认 <input>.out.jsonl；- 表示打到 stdout）。"
                        "跑完会在旁边写一份 <输出>.report.md 回执")
    p.add_argument("-j", "--jobs", type=int, default=4,
                   help="并发度（默认 4，匹配 server 默认 n_slots=4）")
    p.add_argument("-f", "--input-format", choices=["auto", "text", "jsonl"], default="auto")
    p.add_argument("-s", "--system", help="全局 system 提示（JSONL 里可逐条覆盖）")
    p.add_argument("-n", "--max-tokens", type=int, default=512, help="默认最大生成 token 数")
    p.add_argument("-t", "--temperature", type=float, default=0.7, help="默认温度")
    p.add_argument("--no-think", action="store_true",
                   help="关闭思考（推荐用于批量改写/分类/抽取，省 90%% token）")
    p.add_argument("--timeout", type=float, default=300, help="单条超时秒数（默认 300）")
    p.add_argument("--retries", type=int, default=1, help="单条失败重试次数（默认 1）")
    p.add_argument("--resume", action="store_true",
                   help="跳过输出文件中已成功的行，只补没跑完的")
    args = p.parse_args()

    args.think = not args.no_think
    out_path = args.output or (args.input + ".out.jsonl")

    tasks = _load_tasks(args.input, args.input_format)
    done = _load_done(out_path) if (args.resume and out_path != "-") else {}
    todo = [(i, t) for i, t in enumerate(tasks) if i not in done]

    if args.resume and done:
        print(f"[续跑] 已有 {len(done)} 条完成，本次补跑 {len(todo)} 条", file=sys.stderr)
    if not todo:
        print("[完成] 没有需要跑的任务", file=sys.stderr)
        todo = []

    if len(todo) >= 10 and args.think:
        print("[提示] 批量任务通常是改写/分类/抽取，加 --no-think 可省约 90% token",
              file=sys.stderr)

    # 9B 不并发：它的 KV 是 4 个 slot 共享的一个 32K 池子（kv_unified），
    # 开并发只会互相挤。规格见 SKILL.md「一、本机一次只跑一个模型」。
    if args.jobs > 1 and "9B" in _probe_model():
        print("[警告] server 上跑的是 9B —— 9B 不能并发（KV 是 4 slot 共享的一个 32K 池子）。"
              "改用 -j 1，或先切到 2B（start.sh）再批量跑", file=sys.stderr)

    print(f"[开始] {len(todo)} 条任务，并发 {args.jobs}，thinking="
          f"{'on' if args.think else 'off'} → {out_path}", file=sys.stderr)

    results = dict(done)
    t0 = time.time()
    done_n = 0
    try:
        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futures = [ex.submit(_call, t, i, args) for i, t in todo]
            for fut in futures:
                rec = fut.result()
                results[rec["index"]] = rec
                done_n += 1
                flag = "ERR" if rec["error"] else "ok "
                print(f"  [{done_n}/{len(todo)}] {flag} #{rec['index']} "
                      f"{rec['completion_tokens']}tok", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n[中断] 正在写出已完成的部分…", file=sys.stderr)

    ordered = [results[i] for i in sorted(results)]
    out_stream = sys.stdout if out_path == "-" else open(out_path, "w", encoding="utf-8")
    try:
        for rec in ordered:
            out_stream.write(json.dumps(rec, ensure_ascii=False) + "\n")
    finally:
        if out_path != "-":
            out_stream.close()

    failed = sum(1 for r in ordered if r.get("error"))
    total_tok = sum(r.get("completion_tokens") or 0 for r in ordered)
    el = time.time() - t0
    print(f"[完成] {len(ordered)} 条（失败 {failed}）｜{total_tok} tok ｜"
          f"{el:.1f}s ｜{total_tok/el if el else 0:.1f} tok/s → {out_path}",
          file=sys.stderr)
    if failed:
        print(f"[提示] {failed} 条失败，结果里 error 字段有原因；"
              f"修好后用 --resume 只补这些", file=sys.stderr)

    if out_path != "-":
        try:
            report = _write_report(out_path, ordered, args, el)
            print(f"[回执] {report}（主模型读这份就够，别读全量 JSONL）", file=sys.stderr)
        except Exception as e:
            print(f"[警告] 回执生成失败：{type(e).__name__}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
