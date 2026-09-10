@echo off
REM local-ai interactive chat (Windows)
REM Thin wrapper around llama_chat.py so the single-turn logic lives in one place.
REM Usage: chat.bat [--no-think] [system_prompt]
REM
REM Thinking is ON by default; add --no-think for trivial tasks to save tokens.
REM Requires a running llama-server:  start.bat          (default = 2B)
REM                                   start.bat 9b       (9B)

setlocal enabledelayedexpansion
chcp 65001 >nul

set "SCRIPT=%~dp0llama_chat.py"
set "THINK_ARG="
set "SYSTEM_PROMPT=你是一个有用的AI助手，简洁明了地回答问题。"

if "%~1"=="--no-think" (
    set "THINK_ARG=--no-think"
    shift
)
if not "%~1"=="" set "SYSTEM_PROMPT=%~1"

echo === local-ai 交互对话 ===
echo 输入问题，按 Enter 发送。输入 'exit' 或 'quit' 退出。
if not defined THINK_ARG echo （思考已开启；要省 token 请用：chat.bat --no-think）
echo.

:loop
set "user_input="
set /p "user_input=> "
if /i "!user_input!"=="exit" goto :end
if /i "!user_input!"=="quit" goto :end
if "!user_input!"=="" goto :loop

py -3 "%SCRIPT%" %THINK_ARG% -s "%SYSTEM_PROMPT%" "!user_input!"
echo.
goto :loop

:end
echo 再见！
