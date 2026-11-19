@echo off
chcp 65001 > nul
cd /d "%~dp0"
call venv\Scripts\activate.bat
set "SCRIPT=%~1"
if "%SCRIPT%"=="" (
  echo scripts 폴더의 대본 txt 파일을 이 파일 위로 끌어다 놓으세요.
  echo 또는 대본 파일 이름을 입력하세요. 예: scripts\01_장애인분담금.txt
  set /p SCRIPT=대본 파일: 
)
set /p UP=인스타그램에 바로 올릴까요? (y/n): 
if /i "%UP%"=="y" (
  python reels.py make --script "%SCRIPT%" --upload
) else (
  python reels.py make --script "%SCRIPT%"
)
explorer output
pause
