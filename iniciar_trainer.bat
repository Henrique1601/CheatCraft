@echo off
title Spider-Man Trainer Launcher
color 0C
echo ========================================================
echo        SPIDER-MAN REMASTERED - TRAINER LAUNCHER
echo ========================================================
echo.
echo Iniciando o Trainer Pro em segundo plano...
echo Hotkeys disponiveis no Numpad (Num 1 a Num 6).
echo.
python main_trainer.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Ocorreu uma falha ao iniciar o Trainer.
    echo Verifique se instalou os pacotes com: pip install -r requirements.txt
    pause
)
