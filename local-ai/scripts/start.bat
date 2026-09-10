@echo off
REM local-ai start / switch script (Windows)
REM Usage: start.bat [minicpm^|9b] [port]      (default: minicpm, i.e. 2B)
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
REM NOTE: the thinking toggle is NOT here. Both models are thinking models, but
REM disabling thinking must be done PER-REQUEST via chat_template_kwargs (see
REM llama_chat.py). The server-side --reasoning off / --reasoning-budget 0 /
REM --chat-template-kwargs are all measured BROKEN on this build (b10883) --
REM an unfixed upstream llama.cpp bug (PR #22336, still open).
REM
REM NOTE: no parenthesised blocks below -- an unescaped ")" inside an if(...)
REM block silently terminates it early (that bug shipped once; see git log).

setlocal enabledelayedexpansion
set LLAMA_DIR=C:\Users\caill\tools\llama-cpp\cuda-b10883
set MODEL_MINICPM=D:\models\gguf\minicpm5-2b\MiniCPM5-2B-Q8_0.gguf
set MODEL_9B=D:\models\gguf\qwen3.8-9b-distill\Qwen3.8-9B-Q4_K_M.gguf
set HERE=%~dp0

set MODEL_TYPE=%1
if "%MODEL_TYPE%"=="" set MODEL_TYPE=minicpm

set PORT=%2
if "%PORT%"=="" set PORT=8080

if "%MODEL_TYPE%"=="9b" goto :start_9b
if "%MODEL_TYPE%"=="minicpm" goto :start_minicpm
goto :usage

:usage
echo Usage: start.bat [minicpm^|9b] [port]
echo   minicpm - MiniCPM5-2B Q8 GPU full offload, 128K ctx [default; batch / long text / concurrency]
echo   9b      - Qwen3.8-9B-Distill GPU full offload, 32K ctx [pi agent / hard tasks / code]
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

:maybe_switch
REM --- what is currently serving? (empty = nothing) ---
set BODY=
set RUNNING=
for /f "delims=" %%i in ('curl -s -m 3 http://127.0.0.1:%PORT%/v1/models 2^>nul') do set BODY=%%i
if "!BODY!"=="" goto :launch
echo !BODY! | findstr /C:"MiniCPM" >nul && set RUNNING=minicpm
echo !BODY! | findstr /C:"9B-Q4_K_M" >nul && set RUNNING=9b

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
"%LLAMA_DIR%\llama-server.exe" -m "%TARGET%" -ngl 99 --host 127.0.0.1 --port %PORT% -c %CTX% --jinja --cache-type-k q8_0 --cache-type-v q8_0 %EXTRA%
