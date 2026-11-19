@echo off
chcp 65001 > nul
cd /d "%~dp0"
call venv\Scripts\activate.bat
set "FOLDER=%~1"
if "%FOLDER%"=="" (
  echo output 안의 릴스 폴더를 이 파일 위로 끌어다 놓으세요.
  set /p FOLDER=폴더 경로: 
)
python reels.py upload "%FOLDER%"
pause
