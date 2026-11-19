@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo === 릴스 자동화 설치 ===
where python > nul 2>&1
if errorlevel 1 (
  echo [오류] 파이썬이 없어요. https://www.python.org/downloads/ 에서 설치하세요.
  echo        설치 첫 화면에서 "Add python.exe to PATH" 를 꼭 체크하세요.
  pause
  exit /b 1
)
if not exist venv python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo [오류] 설치에 실패했어요. 위 메시지를 확인하세요.
  pause
  exit /b 1
)
if not exist .env copy .env.example .env > nul
echo.
echo 설치 완료! 메모장이 열리면 API 키를 넣고 저장하세요.
notepad .env
python reels.py check
pause
