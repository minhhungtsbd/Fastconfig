@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ========================================
rem   FastConfigVPS - Build Script (PyQt5)
rem ========================================

rem Base settings
pushd "%~dp0"
set "BASE_DIR=%CD%"
set "APP_NAME=FastConfigVPS_v3.1"
set "MAIN_PY=FastConfigVPS.py"
set "ICON_PNG=app_icon.png"
set "ICON_ICO=app_icon.ico"

echo [INFO] Working dir: %BASE_DIR%
echo.

echo [STEP 0] Ensure build dependencies (PyInstaller, Pillow)...
py -m pip install --upgrade pip >nul 2>&1
py -m pip install --upgrade pyinstaller pillow || (
  echo [ERROR] Failed to install required packages. >&2
  exit /b 1
)
echo Done.
echo.

echo [STEP 1] Cleaning old build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
for %%F in ("%APP_NAME%.spec") do if exist "%%~fF" del /f /q "%%~fF"
if exist "__pycache__" rmdir /s /q "__pycache__"
echo Done.
echo.

echo [STEP 2] Convert PNG to ICO (for EXE icon)...
if not exist "%ICON_PNG%" (
  echo [ERROR] PNG icon not found: %ICON_PNG% >&2
  exit /b 1
)
if not exist "%ICON_ICO%" (
  echo   - Creating %ICON_ICO% from %ICON_PNG% ...
  if exist "%BASE_DIR%\convert_icon.py" (
    py "%BASE_DIR%\convert_icon.py" || (
      echo [ERROR] Failed to create ICO from PNG. >&2
      exit /b 1
    )
  ) else (
    rem Fallback: inline Python command (quoted) to avoid batch parenthesis issues
    py -c "from PIL import Image; from pathlib import Path; b=Path(r'%BASE_DIR%'); img=Image.open(b/'%ICON_PNG%').convert('RGBA'); img.save(b/'%ICON_ICO%', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(24,24),(16,16)])" || (
      echo [ERROR] Failed to create ICO from PNG. >&2
      exit /b 1
    )
  )
) else (
  echo   - %ICON_ICO% exists, skipping conversion.
)
echo Done.
echo.

echo [STEP 3] Building %APP_NAME%.exe with PyInstaller (spec)...
rem Đảm bảo file spec chính xác trước khi build
if not exist "%BASE_DIR%\FastConfigVPS.spec" (
  echo [ERROR] Spec file not found: %BASE_DIR%\FastConfigVPS.spec >&2
  echo        Please keep FastConfigVPS.spec in the project root. >&2
  exit /b 1
)
py -m PyInstaller --clean --noconfirm "%BASE_DIR%\FastConfigVPS.spec"
if errorlevel 1 (
  echo [ERROR] PyInstaller build failed. >&2
  exit /b 1
)
echo.

echo [STEP 4] Build result
if exist "dist\%APP_NAME%.exe" (
  echo [SUCCESS] %APP_NAME%.exe created successfully.
  echo         Path: %BASE_DIR%\dist\%APP_NAME%.exe
  echo.
  echo Tip: If File Explorer doesn't show the new icon immediately, refresh or reopen the window.
  echo.
) else (
  echo [ERROR] Output EXE not found. >&2
  exit /b 1
)

echo ========================================
echo   Build process completed!
echo ========================================
popd
exit /b 0
