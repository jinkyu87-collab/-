@echo off
chcp 65001 > nul
cd /d "%~dp0"
call venv\Scripts\activate.bat
set /p TOPIC=릴스 주제를 입력하세요: 
set /p UP=인스타그램에 바로 올릴까요? (y/n): 
if /i "%UP%"=="y" (
  python reels.py make "%TOPIC%" --upload
) else (
  python reels.py make "%TOPIC%"
)
explorer output
pause
