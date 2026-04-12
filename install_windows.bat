@echo off
:: ─────────────────────────────────────────
::  AetherAI — Script d'installation Windows
:: ─────────────────────────────────────────

echo.
echo ==================================================
echo   AetherAI — Installation Windows
echo ==================================================
echo.

set INSTALL_DIR=C:\AetherAI

:: 1. Vérifie Python
echo - Verification Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   Python non trouve. Installe-le depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 2. Crée le dossier
echo - Creation du dossier %INSTALL_DIR%...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\aether_images" mkdir "%INSTALL_DIR%\aether_images"
if not exist "%INSTALL_DIR%\aether_videos" mkdir "%INSTALL_DIR%\aether_videos"

:: 3. Copie les fichiers depuis le dossier courant
echo - Copie des fichiers...
for %%f in (aether.py aether_tui.py first_run.py detect.py memory.py cowork.py imagine.py imagine_video.py setup_local.py discord_bot.py requirements.txt) do (
    if exist "%%f" (
        copy /Y "%%f" "%INSTALL_DIR%\%%f" >nul
        echo   Copie : %%f
    ) else (
        echo   Manquant : %%f
    )
)

:: 4. Crée le venv
echo - Creation du venv...
cd /d "%INSTALL_DIR%"
python -m venv venv

:: 5. Installe les dépendances
echo - Installation des dependances...
call venv\Scripts\activate
pip install --upgrade pip -q
pip install -r requirements.txt

:: 6. Crée les launchers .bat
echo - Creation des launchers...

echo @echo off > "%INSTALL_DIR%\AetherAI.bat"
echo cd /d C:\AetherAI >> "%INSTALL_DIR%\AetherAI.bat"
echo call venv\Scripts\activate >> "%INSTALL_DIR%\AetherAI.bat"
echo python aether.py >> "%INSTALL_DIR%\AetherAI.bat"
echo pause >> "%INSTALL_DIR%\AetherAI.bat"

echo @echo off > "%INSTALL_DIR%\AetherTUI.bat"
echo cd /d C:\AetherAI >> "%INSTALL_DIR%\AetherTUI.bat"
echo call venv\Scripts\activate >> "%INSTALL_DIR%\AetherTUI.bat"
echo python aether_tui.py >> "%INSTALL_DIR%\AetherTUI.bat"
echo pause >> "%INSTALL_DIR%\AetherTUI.bat"

echo.
echo ==================================================
echo   Installation terminee !
echo.
echo   Lance AetherAI.bat     pour le terminal classique
echo   Lance AetherTUI.bat    pour l'interface TUI
echo ==================================================
echo.
pause
