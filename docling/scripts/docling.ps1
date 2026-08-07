# docling.ps1 — Docling CLI wrapper
# 用途：固化本机必需环境变量（torch 2.13 在 Windows 无 MSVC 时 inductor 报错），
#       并自动加上 16GB 内存友好的默认参数。
# 用法：docling.ps1 convert report.pdf --to md --output ./out/
#       （透传所有参数给 docling convert）

param([Parameter(ValueFromRemainingArguments = $true)][string[]]$DoclingArgs)

$ErrorActionPreference = "Stop"

# --- 必需：禁用 torch inductor / dynamo 编译 ---
# torch 2.13 在 Windows 上默认启用 inductor，会尝试用 MSVC cl.exe 编译。
# 本机无 MSVC → 报 `InvalidCxxCompiler: Compiler: cl is not found`。
# 这两个变量必须设置，否则转换必然失败。
$env:TORCH_COMPILE_DISABLE = "1"
$env:TORCHINDUCTOR_DISABLE = "1"

$Docling = "C:\Users\59620\.venv-docling\Scripts\docling.exe"

if (-not (Test-Path $Docling)) {
    Write-Error "docling CLI 未找到: $Docling`n请先运行: uv venv ~/.venv-docling --python 3.12 && uv pip install --python ~/.venv-docling docling"
    exit 1
}

# 透传参数；若是 convert 子命令，自动追加 16GB 内存友好默认参数（除非已显式指定）
$OutArgs = @($DoclingArgs)
if ($OutArgs.Count -gt 0 -and $OutArgs[0] -eq "convert") {
    $hasBatchSize = $DoclingArgs | Where-Object { $_ -like "--page-batch-size*" }
    $hasThreads   = $DoclingArgs | Where-Object { $_ -like "--num-threads*" }
    if (-not $hasBatchSize) { $OutArgs += "--page-batch-size", "2" }
    if (-not $hasThreads)   { $OutArgs += "--num-threads", "4" }
}

& $Docling @OutArgs
exit $LASTEXITCODE
