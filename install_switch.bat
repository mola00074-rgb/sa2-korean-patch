@echo off
chcp 65001 > nul
setlocal
set "GAME=C:\Program Files (x86)\Steam\steamapps\common\Sonic Adventure 2"
echo 소닉 어드벤처 2 한글 패치 (스위치 Pro 컨트롤러 표기)
echo.
set /p "INPUT=게임 폴더 경로 (그냥 Enter = %GAME%): "
if not "%INPUT%"=="" set "GAME=%INPUT%"
where py > nul 2>&1 && (set "PY=py -3") || (set "PY=python")
%PY% "%~dp0tools\patch.py" --install "%GAME%" --controller switch
echo.
pause
