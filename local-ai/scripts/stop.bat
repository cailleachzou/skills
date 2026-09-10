@echo off
REM Stop the local llama-server and wait for it to actually go away.
REM Usage: stop.bat [port]
REM
REM Why wait: the driver reclaims VRAM with a delay. Starting a new model too
REM soon makes llama.cpp spill layers to CPU -- no error, just ~10x slower
REM (see SKILL.md "实测性能").
REM
REM Run this when a round of local work is done: the server never exits on its
REM own and holds ~6-7 GB of VRAM in the background.

setlocal
set PORT=%1
if "%PORT%"=="" set PORT=8080

tasklist /FI "IMAGENAME eq llama-server.exe" 2>nul | findstr /I "llama-server" >nul
if errorlevel 1 (
    echo [stop] no llama-server running
    exit /b 0
)

echo [stop] terminating llama-server...
taskkill /F /IM llama-server.exe /T >nul 2>&1

REM wait up to ~20s for the process to disappear
for /l %%i in (1,1,20) do (
    tasklist /FI "IMAGENAME eq llama-server.exe" 2>nul | findstr /I "llama-server" >nul
    if errorlevel 1 goto :gone
    REM full path: from Git Bash, bare "timeout" resolves to MSYS coreutils
    "%SystemRoot%\System32\timeout.exe" /t 1 /nobreak >nul 2>&1
)

echo [WARN] llama-server still alive after 20s 1>&2
exit /b 1

:gone
REM extra beat for the driver to hand the VRAM back
"%SystemRoot%\System32\timeout.exe" /t 2 /nobreak >nul 2>&1
echo [stop] done
exit /b 0
