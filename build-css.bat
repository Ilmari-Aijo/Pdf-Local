@echo off
rem Compiles styles\input.css (Tailwind v4) into static\app.css. Runs locally, no Node needed.
rem   build-css.bat          build once (minified)
rem   build-css.bat --watch  rebuild whenever a file is saved
cd /d "%~dp0"
if not exist "tools\tailwind\tailwindcss.exe" (
  echo Missing tools\tailwind\tailwindcss.exe
  echo Download it from https://github.com/tailwindlabs/tailwindcss/releases/tag/v4.3.5
  echo ^(file tailwindcss-windows-x64.exe, renamed to tailwindcss.exe^)
  exit /b 1
)
if /i "%~1"=="--watch" (
  "tools\tailwind\tailwindcss.exe" -i styles\input.css -o static\app.css --watch
) else (
  "tools\tailwind\tailwindcss.exe" -i styles\input.css -o static\app.css --minify
)
