---
name: "cli-anything-pdf2zh"
description: "CLI harness for the PDFMathTranslate Windows EXE — translate PDFs (with layout preserved) from scripts and AI agents. Ships with a MiniMax translator patch that adds a new OpenAI-compatible service to the bundled pdf2zh.exe."
---

# cli-anything-pdf2zh

> Translate PDFs from scripts / agents. Wraps `pdf2zh.exe` (PDFMathTranslate)
> and adds a **MiniMax** translator via a one-shot patch into the bundled
> `build/site-packages/pdf2zh/`.

The harness **calls the real software** (the `pdf2zh.exe` bundled with
PDFMathTranslate) for all translation. It does not reimplement the
translator pipeline in Python. The MiniMax engine is added by patching
`translator.py`, `pdf2zh.py`, and `converter.py` inside the bundled
site-packages (idempotent — `.harness.bak` backups are written).

---

## When to use

Use this CLI when you need to:

* Translate a PDF (or batch of PDFs) from a script / agent
* Switch between 23+ translation services (Google, OpenAI, DeepL,
  MiniMax, …) without touching the pdf2zh GUI
* Inspect a PDF's page count / size / validity before translating
* Inspect the SQLite translation cache (`~/.cache/pdf2zh/cache.v1.db`)
* Read / write the JSON translator config (`~/.config/PDFMathTranslate/`)
* Drive the EXE's MCP server from a script

Do **not** use this for editing the translated PDF, OCR, or anything
beyond the bundled PDFMathTranslate surface — those are out of scope.

---

## Installation

```bash
# 1. PDFMathTranslate (the real software) — already installed at
#    C:\Program Files\pdf2zh\build\pdf2zh.exe on this host.
#    Verify: cli-anything-pdf2zh services list
#
# 2. The harness
cd "C:/Program Files/pdf2zh/agent-harness"
pip install -e .
#
# 3. Install the MiniMax translator patch + set the API key
#    (minimax is the default service — required for out-of-the-box translation)
cli-anything-pdf2zh patch install
cli-anything-pdf2zh config set-key minimax MINIMAX_API_KEY <key>
cli-anything-pdf2zh config set-key minimax MINIMAX_BASE_URL https://api.minimaxi.com/v1
cli-anything-pdf2zh config set-key minimax MINIMAX_MODEL MiniMax-Text-01
#
#    To use a different service, pass --service <name> (e.g. --service google
#    for the no-key-needed fallback).
```

To uninstall the harness:
```bash
pip uninstall cli-anything-pdf2zh
cli-anything-pdf2zh patch uninstall   # restores the original translator.py
```

---

## Command groups

| Group | Subcommands | Purpose |
|-------|-------------|---------|
| `info`      | —               | PDF page count, size, validity |
| `translate` | —               | Translate one or more PDFs |
| `batch`     | —               | Translate every PDF in a directory |
| `services`  | `list`, `show`  | Catalog of 23 translation services |
| `config`    | `list`, `get`, `set`, `delete`, `set-key`, `show-translator` | Read/write `~/.config/PDFMathTranslate/config.json` |
| `inspect`   | —               | Detailed PDF inspection (alias of `info` with more fields) |
| `cache`     | `summary`, `list`, `clear` | Query/clear the SQLite translation cache |
| `patch`     | `status`, `install`, `uninstall` | Manage the MiniMax translator patch |
| `mcp`       | —               | Launch the EXE's MCP server (passthrough) |
| `repl`      | —               | Default when no subcommand is given |

**Global flags:** `--json` (machine-readable output, every command supports it),
`--exe PATH` (override the EXE path), `--quiet` (suppress non-essential output).

---

## Quick examples

### One-shot translation

```bash
# English → Chinese, MiniMax (the default — needs API key configured)
cli-anything-pdf2zh translate paper.pdf -o out/

# English → Japanese, MiniMax, explicit
cli-anything-pdf2zh translate paper.pdf -o out/ --service minimax --lang-in en --lang-out ja

# Google fallback (no API key needed)
cli-anything-pdf2zh translate paper.pdf -o out/ --service google

# Translate pages 1-3 only
cli-anything-pdf2zh translate book.pdf -o out/ --pages 1-3

# Batch
cli-anything-pdf2zh batch ./pdfs/ -o ./out/
```

### JSON output (for agents)

```bash
cli-anything-pdf2zh --json services list
# [
#   {"name": "google", "kind": "free", "key": "no", "desc": "Google Translate (web endpoint)"},
#   ...
#   {"name": "minimax", "kind": "key", "key": "yes", "desc": "MiniMax (added by harness patch)"}
# ]

cli-anything-pdf2zh --json translate paper.pdf -o out/
# {
#   "mono_pdf": "...\\paper-mono.pdf",
#   "dual_pdf": "...\\paper-dual.pdf",
#   "exit_code": 0,
#   "duration_s": 12.4,
#   "inputs": ["paper.pdf"],
#   ...
# }
```

### Interactive REPL (default)

```bash
$ cli-anything-pdf2zh
◆  cli-anything-pdf2zh  v0.1.0  (PDFMathTranslate harness)

  Commands: help, status, services, use <svc>, lang <in> <out>, pdf <path>,
            out <path>, translate, save [path], open <path>, patch-install,
            version, exit

pdf2zh> pdf paper.pdf
  ✓ current_pdf = paper.pdf
pdf2zh> out ./translated
  ✓ output_dir = ./translated
pdf2zh> use minimax
  ✓ service = minimax
pdf2zh> lang en zh
  ✓ lang = en -> zh
pdf2zh> translate
  ✓ mono: ./translated/paper-mono.pdf  dual: ./translated/paper-dual.pdf
pdf2zh> save my-translation.json
  ✓ saved my-translation.json
pdf2zh> exit
  Bye.
```

### Inspect / cache

```bash
cli-anything-pdf2zh info paper.pdf
cli-anything-pdf2zh --json cache summary
cli-anything-pdf2zh cache list --engine minimax --limit 10
cli-anything-pdf2zh cache clear --engine minimax
```

### MiniMax patch

```bash
cli-anything-pdf2zh patch status
cli-anything-pdf2zh patch install         # adds MiniMax class to translator.py,
                                          # registers it in pdf2zh.py + converter.py
cli-anything-pdf2zh patch uninstall       # restores from .harness.bak backups
```

---

## Agent guidance

### Default service

* `minimax` is the default for both `translate` and `batch` (and the REPL
  `Session` defaults to it). Override with `--service <name>` if you need
  Google / OpenAI / DeepL / etc.
* `minimax` requires the patch installed and the API key configured (see
  Installation step 3). If the key is missing, the EXE raises
  `ValueError: ...` — the harness exits 1.

### Auto-fallback chain

* If the **default** service (`minimax`) fails (non-zero exit), the
  harness automatically retries once with the next service in
  `DEFAULT_FALLBACK_CHAIN` (currently `google`, the only key-free
  fallback). This way an unset API key degrades to a working translation
  instead of a hard failure.
* Auto-fallback only kicks in for the default service. If the user
  explicitly picked `--service openai` (or any non-default), the failure
  is reported as-is — silently swapping the engine behind their back
  would be more confusing than the original error.
* The result dict carries four extra fields when fallback ran:
  * `fallback_used: bool`
  * `fallback_from: str` — the service that failed (e.g. `"minimax"`)
  * `fallback_to: str` — the service actually used (e.g. `"google"`)
  * `fallback_reason: str` — last 300 chars of the first attempt's
    stdout+stderr, so you can see why it failed
* In human output the user sees a `⚠ minimax failed — fell back to
  google` warning line before the success/error block. In JSON output
  the same info is in the result fields.

### Output discipline

* Every command supports `--json`. The harness never prints colours or
  spinners in JSON mode.
* Output is one of:
  * A single JSON object (most commands)
  * A JSON array (`services list`)
  * A path string (`pdf2zh.exe --version`)
* Errors are emitted as `{"error": "..."}` on stdout, **not** mixed into
  data. Exit code is non-zero on failure.

### Resolving the EXE

The harness looks for the EXE in this order:

1. `--exe PATH` (explicit override)
2. `$PDF2ZH_EXE_PATH` env var
3. `shutil.which("pdf2zh")`
4. `C:\Program Files\pdf2zh\build\pdf2zh.exe` (canonical install)
5. Sibling `build/pdf2zh.exe` relative to the harness package (dev mode)

If none of these work, the harness exits with a clear install-instructions
message.

### Translator envs

`config set-key <service> <KEY> <value>` writes to
`~/.config/PDFMathTranslate/config.json` under `translators[N].envs`. The
EXE picks these up on the next run. Secret values (keys containing
`KEY`, `TOKEN`, or `SECRET`) are **masked** in `config show-translator`
output — even in `--json` mode — so they don't leak into agent
transcripts.

The MiniMax translator expects:

| Env | Default | Required |
|-----|---------|----------|
| `MINIMAX_API_KEY` | — | yes |
| `MINIMAX_BASE_URL` | `https://api.minimaxi.com/v1` | no |
| `MINIMAX_MODEL` | `MiniMax-Text-01` | no |

### Idempotency

* `patch install` is a no-op if already installed
* `patch uninstall` is a no-op if not installed
* `translate` and `batch` always write to a fresh `*-mono.pdf` / `*-dual.pdf`
  pair; pre-existing files are overwritten

### Failure modes

* Network down → `translate` exits 1, `stderr_tail` is captured
* Missing API key → EXE raises `ValueError`, harness exits 1
* Wrong service name → EXE raises `ValueError: Unsupported translation service`
* Cache file corrupt → `cache summary` returns 0 rows + `note` field

### When the EXE isn't installed

`find_pdf2zh_exe` raises a `RuntimeError` with clear instructions. The
unit tests don't fail — they skip — if the EXE is missing.

---

## Filesystem locations

| What | Where |
|------|-------|
| EXE | `C:\Program Files\pdf2zh\build\pdf2zh.exe` |
| Bundled python | `C:\Program Files\pdf2zh\build\runtime\` |
| Bundled site-packages | `C:\Program Files\pdf2zh\build\site-packages\` |
| Edited by patch | `…\site-packages\pdf2zh\translator.py` |
| Edited by patch | `…\site-packages\pdf2zh\pdf2zh.py` |
| Edited by patch | `…\site-packages\pdf2zh\converter.py` |
| Backups written by patch | `<file>.harness.bak` next to each |
| ONNX model cache | `~/.cache/babeldoc/` |
| Translation cache (SQLite) | `~/.cache/pdf2zh/cache.v1.db` |
| Translator config (JSON) | `~/.config/PDFMathTranslate/config.json` |

---

## Security

* Never commit `~/.config/PDFMathTranslate/config.json` — it contains
  API keys. Add it to your global `.gitignore`.
* The harness's `config show-translator` masks secrets. Use it to verify
  what was stored without leaking the value.
* The MiniMax patch makes a backup of each file it edits
  (`<file>.harness.bak`). `patch uninstall` restores from these.
