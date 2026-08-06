<#
.SYNOPSIS
    PDF OCR → Markdown 转换工具 (marker-pdf)
.DESCRIPTION
    使用 marker-pdf 将 PDF 文件转换为 Markdown，保留布局/表格/公式。
    替代 Umi-OCR 的 PDF→文本流程。
.EXAMPLE
    .\pdf2md.ps1 -FilePath "C:\docs\scan.pdf"
    .\pdf2md.ps1 -FilePath "C:\docs\scan.pdf" -OutputDir "C:\output"
    .\pdf2md.ps1 -FilePath "C:\docs\scan.pdf" -Pages "0,1-3,5"
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$FilePath,

    [string]$OutputDir = "",

    [string]$Pages = "",

    [switch]$ForceOcr,

    [switch]$DisableImages
)

$MarkerPy = "C:\Users\59620\.venv-marker\Scripts\python.exe"
$MarkerExe = "C:\Users\59620\.venv-marker\Scripts\marker.exe"

# Validate input
if (-not (Test-Path $FilePath)) {
    Write-Error "文件不存在: $FilePath"
    exit 1
}

$ext = [System.IO.Path]::GetExtension($FilePath).ToLower()
if ($ext -ne ".pdf") {
    Write-Error "仅支持 PDF 文件，当前: $ext"
    exit 1
}

# Prepare temp working directory
$tempDir = Join-Path $env:TEMP "marker_$(Get-Random)"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Copy PDF to temp dir (marker expects a folder input)
Copy-Item $FilePath -Destination $tempDir -Force

# Determine output directory
if (-not $OutputDir) {
    $OutputDir = [System.IO.Path]::GetDirectoryName($FilePath)
}

# Build marker command args
$markerArgs = @(
    $tempDir,
    "--output_format", "markdown",
    "--output_dir", $OutputDir
)

if ($Pages) {
    $markerArgs += "--page_range"
    $markerArgs += $Pages
}

if ($ForceOcr) {
    $markerArgs += "--mode"
    $markerArgs += "balanced"
}

if ($DisableImages) {
    $markerArgs += "--disable_image_extraction"
}

# Run marker
Write-Host "→ 正在转换: $FilePath" -ForegroundColor Cyan
Write-Host "→ 输出目录: $OutputDir" -ForegroundColor Gray

# surya/llama.cpp 后端必需环境变量（缺失则报 llama-server binary not found）
$env:LLAMA_CPP_BINARY = "C:\Users\59620\.models\llama-x64\llama-server.exe"
$env:SURYA_GGUF_LOCAL_MODEL_PATH = "C:\Users\59620\.models\surya\surya-2.gguf"
$env:SURYA_GGUF_LOCAL_MMPROJ_PATH = "C:\Users\59620\.models\surya\surya-2-mmproj.gguf"

& $MarkerExe @markerArgs

# Find and rename output
$pdfName = [System.IO.Path]::GetFileNameWithoutExtension($FilePath)
$mdFile = Join-Path $OutputDir "$pdfName.md"

if (Test-Path $mdFile) {
    Write-Host "→ 完成: $mdFile" -ForegroundColor Green
} else {
    # marker may output to a subfolder
    $found = Get-ChildItem -Path $OutputDir -Filter "$pdfName.md" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        Write-Host "→ 完成: $($found.FullName)" -ForegroundColor Green
    } else {
        Write-Warning "未找到输出文件，请检查 $OutputDir"
    }
}

# Cleanup temp dir
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
