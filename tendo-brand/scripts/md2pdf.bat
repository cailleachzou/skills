@echo off
REM Convert MD to PDF with Tendo branded header
REM Usage: md2pdf.bat input.md [output_dir]
REM
REM Features:
REM   - Auto-generates config if not exists
REM   - Converts Obsidian image syntax ![[...]] to standard markdown ![](...)
REM   - Renames files with spaces to remove spaces

setlocal

set SCRIPT_DIR=%~dp0
set SKILL_DIR=%SCRIPT_DIR%..

if "%~1"=="" (
    echo Usage: md2pdf.bat input.md [output_dir]
    exit /b 1
)

set INPUT_FILE=%~1
set OUTPUT_DIR=%~2
if "%OUTPUT_DIR%"=="" set OUTPUT_DIR=%cd%

REM Generate config if not exists
if not exist "%OUTPUT_DIR%\md2pdf-config.js" (
    echo Generating Tendo PDF config...
    python "%SCRIPT_DIR%gen_md2pdf_config.py" "%OUTPUT_DIR%"
)

REM Create temp file with standard image syntax
set TEMP_FILE=%OUTPUT_DIR%\%~n1_pdf.md
powershell -Command "$c = Get-Content '%INPUT_FILE%' -Raw; $c = $c -replace '!\[\[([^\]]+)\]\]', '![]($1)'; $c | Set-Content '%TEMP_FILE%' -Encoding UTF8"

REM Rename images with spaces (if any)
for %%f in ("%OUTPUT_DIR%\Pasted image *.png") do (
    set "newname=%%~nf"
    set "newname=!newname:Pasted image =img-!"
    rename "%%f" "!newname!.png" 2>nul
)

REM Convert MD to PDF
echo Converting %INPUT_FILE% to PDF...
md-to-pdf "%TEMP_FILE%" --config-file "%OUTPUT_DIR%\md2pdf-config.js"

REM Rename output PDF to match input filename
if exist "%OUTPUT_DIR%\%~n1_pdf.pdf" (
    del "%OUTPUT_DIR%\%~n1.pdf" 2>nul
    ren "%OUTPUT_DIR%\%~n1_pdf.pdf" "%~n1.pdf"
)

REM Cleanup temp files
del "%TEMP_FILE%" 2>nul
del "%OUTPUT_DIR%\md2pdf-config.js" 2>nul
del "%OUTPUT_DIR%\tendo-style.css" 2>nul
rmdir /s /q "%OUTPUT_DIR%\unpacked_ref" 2>nul

echo Done: %OUTPUT_DIR%\%~n1.pdf
endlocal
