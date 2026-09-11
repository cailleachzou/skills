@echo off
REM local-ai start / switch script (Windows)
REM Usage: start.bat [minicpm^|9b^|vl4^|vl8^|asr] [port]      (default: minicpm, i.e. 2B)
REM
REM Git Bash users have the aliases:  llama = 2B,  llama9 = 9B  (see ~/.bashrc).
REM
REM Idempotent: reuses the running server if it already serves the target model;
REM otherwise stops it first (waiting for VRAM to come back) and starts the target.
REM
REM NOTE: llama-server loads ONE model at a time and IGNORES the request "model"
REM field, so switching = restarting this script. Don't flip-flop for single
REM tasks -- pick one per round of work (see SKILL.md "一").
REM
REM NOTE: the thinking toggle is NOT here. Only the two TEXT models (minicpm / 9b)
REM are thinking models; vl4 / vl8 / asr are Instruct / transcription models with
REM no thinking mode. Disabling thinking must be done PER-REQUEST via
REM chat_template_kwargs (see llama_chat.py). The server-side --reasoning off /
REM --reasoning-budget 0 / --chat-template-kwargs are all measured BROKEN on this
REM build (b10883) -- an unfixed upstream llama.cpp bug (PR #22336, still open).
REM
REM NOTE: no parenthesised blocks below -- an unescaped ")" inside an if(...)
REM block silently terminates it early (that bug shipped once; see git log).

setlocal enabledelayedexpansion
set LLAMA_DIR=C:\Users\caill\tools\llama-cpp\cuda-b10883
set MODEL_MINICPM=D:\models\gguf\minicpm5-2b\MiniCPM5-2B-Q8_0.gguf
set MODEL_9B=D:\models\gguf\qwen3.8-9b-distill\Qwen3.8-9B-Q4_K_M.gguf
set MODEL_VL4=D:\models\gguf\qwen3-vl-4b\Qwen3VL-4B-Instruct-Q4_K_M.gguf
set MMPROJ_VL4=D:\models\gguf\qwen3-vl-4b\mmproj-Qwen3VL-4B-Instruct-F16.gguf
set MODEL_VL8=D:\models\gguf\qwen3-vl-8b\Qwen3VL-8B-Instruct-Q4_K_M.gguf
set MMPROJ_VL8=D:\models\gguf\qwen3-vl-8b\mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf
set MODEL_ASR=D:\models\gguf\qwen3-asr-1.7b\Qwen3-ASR-1.7B-Q8_0.gguf
set MMPROJ_ASR=D:\models\gguf\qwen3-asr-1.7b\mmproj-Qwen3-ASR-1.7b-BF16.gguf
set MMPROJ_ARG=
set HERE=%~dp0

set MODEL_TYPE=%1
if "%MODEL_TYPE%"=="" set MODEL_TYPE=minicpm

set PORT=%2
if "%PORT%"=="" set PORT=8080

if "%MODEL_TYPE%"=="9b" goto :start_9b
if "%MODEL_TYPE%"=="minicpm" goto :start_minicpm
if "%MODEL_TYPE%"=="vl4" goto :start_vl4
if "%MODEL_TYPE%"=="vl8" goto :start_vl8
if "%MODEL_TYPE%"=="asr" goto :start_asr
goto :usage

:usage
echo Usage: start.bat [minicpm^|9b^|vl4^|vl8^|asr] [port]
echo   minicpm - MiniCPM5-2B Q8 GPU full offload, 128K ctx [default; batch / long text / concurrency]
echo   9b      - Qwen3.8-9B-Distill GPU full offload, 32K ctx [pi agent / hard tasks / code]
echo   vl4     - Qwen3-VL-4B Q4_K_M + mmproj F16, 16K ctx [vision, default vision model]
echo   vl8     - Qwen3-VL-8B Q4_K_M + mmproj Q8_0, 8K ctx [vision fallback; only ~440 MiB VRAM left]
echo   asr     - Qwen3-ASR-1.7B Q8_0 + mmproj BF16, 32K ctx [speech transcription]
echo.
echo Git Bash aliases:  llama = 2B,  llama9 = 9B
echo Idempotent: reuses the server if it already serves the target model.
echo Thinking toggle: llama_chat.py [on by default; --no-think to disable]
exit /b 1

:start_9b
set TARGET=%MODEL_9B%
set BANNER=[START] Qwen3.8-9B-Distill GPU full offload, 32K ctx shared by 4 slots, ~55 tok/s
set EXTRA=--temp 0.6 --top-p 0.95 --top-k 20
set CTX=32768
goto :maybe_switch

:start_minicpm
set TARGET=%MODEL_MINICPM%
set BANNER=[START] MiniCPM5-2B Q8 GPU full offload, 128K ctx shared by 4 slots, ~85-107 tok/s [default]
set EXTRA=--temp 1.0 --top-p 0.95
set CTX=131072
goto :maybe_switch

:start_vl4
set TARGET=%MODEL_VL4%
set MMPROJ_ARG=--mmproj "%MMPROJ_VL4%"
set BANNER=[START] Qwen3-VL-4B GPU full offload, 16K ctx (vision)
set EXTRA=--temp 0.7 --top-p 0.8
set CTX=16384
goto :maybe_switch

:start_vl8
set TARGET=%MODEL_VL8%
set MMPROJ_ARG=--mmproj "%MMPROJ_VL8%"
set BANNER=[START] Qwen3-VL-8B GPU full offload, 8K ctx (vision, fallback)
set EXTRA=--temp 0.7 --top-p 0.8
set CTX=8192
goto :maybe_switch

:start_asr
set TARGET=%MODEL_ASR%
set MMPROJ_ARG=--mmproj "%MMPROJ_ASR%"
set BANNER=[START] Qwen3-ASR-1.7B GPU full offload, 32K ctx (speech)
set EXTRA=--temp 0.0
set CTX=32768
goto :maybe_switch

:maybe_switch
REM --- what is currently serving? (empty = nothing) ---
set BODY=
set RUNNING=
for /f "delims=" %%i in ('curl -s -m 3 http://127.0.0.1:%PORT%/v1/models 2^>nul') do set BODY=%%i
if "!BODY!"=="" goto :launch
echo !BODY! | findstr /C:"MiniCPM" >nul && set RUNNING=minicpm
echo !BODY! | findstr /C:"9B-Q4_K_M" >nul && set RUNNING=9b
echo !BODY! | findstr /C:"Qwen3VL-4B" >nul && set RUNNING=vl4
echo !BODY! | findstr /C:"Qwen3VL-8B" >nul && set RUNNING=vl8
echo !BODY! | findstr /C:"Qwen3-ASR-1.7B" >nul && set RUNNING=asr

if "!RUNNING!"=="%MODEL_TYPE%" (
    echo [reuse] %PORT% already serves %MODEL_TYPE%, not restarting
    exit /b 0
)
if not "!RUNNING!"=="" (
    echo [switch] %PORT% serves !RUNNING! -- stopping it first
    call "%HERE%stop.bat" %PORT%
)

:launch
echo %BANNER%
"%LLAMA_DIR%\llama-server.exe" -m "%TARGET%" %MMPROJ_ARG% -ngl 99 --host 127.0.0.1 --port %PORT% -c %CTX% --jinja --cache-type-k q8_0 --cache-type-v q8_0 %EXTRA%
