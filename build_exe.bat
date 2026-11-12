@echo off
title CheatCraft Studio - Build Standalone EXE
color 0E
echo ========================================================
echo       BUILD STANDALONE EXECUTABLE (CHEATCRAFT)
echo ========================================================
echo.
echo Compilando aplicacao nativa para Windows (dist/CheatCraft_Studio)...
echo.
python -m PyInstaller CheatCraft.spec --noconfirm
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   BUILD CONCLUIDO COM SUCESSO!
    echo   Executavel disponivel em: dist\CheatCraft_Studio\CheatCraft_Studio.exe
    echo ========================================================
) else (
    echo.
    echo [ERRO] Ocorreu uma falha durante o build.
)
pause
