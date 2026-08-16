@echo off
setlocal

where uv >nul 2>&1
if %ERRORLEVEL% equ 0 (
  uv %*
  exit /b %ERRORLEVEL%
)

if exist "%USERPROFILE%\.local\bin\uv.exe" (
  "%USERPROFILE%\.local\bin\uv.exe" %*
  exit /b %ERRORLEVEL%
)

if exist "%LOCALAPPDATA%\uv\uv.exe" (
  "%LOCALAPPDATA%\uv\uv.exe" %*
  exit /b %ERRORLEVEL%
)

for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-*") do (
  if exist "%%D\Scripts\uv.exe" (
    "%%D\Scripts\uv.exe" %*
    exit /b %ERRORLEVEL%
  )
)

echo uv not found. Install: https://docs.astral.sh/uv/getting-started/installation/
echo   powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 ^| iex"
exit /b 1
