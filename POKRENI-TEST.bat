@echo off
chcp 65001 >nul
title MP3 Skidac - pokretanje
cd /d "%~dp0app"

where python >nul 2>nul
if errorlevel 1 (
  echo Python nije instaliran. Instaliram ga...
  winget install -e --id Python.Python.3.12 --scope user --accept-source-agreements --accept-package-agreements
  echo.
  echo Python je instaliran. Zatvori ovaj prozor i ponovo pokreni POKRENI-TEST.bat
  pause
  exit /b
)

echo Instaliram potrebne dijelove...
python -m pip install -U --quiet pywebview

if not exist "yt-dlp.exe" (
  echo Skidam yt-dlp...
  curl -L -s -o yt-dlp.exe https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe
)

set FF=0
if exist "ffmpeg.exe" set FF=1
where ffmpeg >nul 2>nul && set FF=1
if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe" set FF=1
if "%FF%"=="0" (
  echo Instaliram FFmpeg...
  winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
)

echo Pokrecem MP3 Skidac...
start "" pythonw mp3_skidac.py
