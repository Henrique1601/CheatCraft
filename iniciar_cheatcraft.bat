@echo off
title CheatCraft Studio - Launcher & Mod Generator
color 0B
echo ========================================================
echo          CheatCraft STUDIO // LAUNCHER & MODDER
echo ========================================================
echo.
echo Iniciando CheatCraft Desktop...
echo.
python launcher.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Falha ao iniciar CheatCraft.
    pause
)
