@echo off
title Cyber Sentry AI - Lanceur
echo ===================================================
echo      LANCEMENT DE CYBER SENTRY AI (POC)
echo ===================================================

:: 1. Verification de Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou n'est pas dans le PATH.
    pause
    exit /b
)

:: 2. Verification et creation de l'environnement virtuel
if not exist ".venv\Scripts\activate" (
    echo [INFO] Creation de l'environnement virtuel Python...
    python -m venv .venv
)

:: 3. Activation de l'environnement
echo [INFO] Activation de l'environnement...
call .venv\Scripts\activate

:: 4. Installation des dependances
echo [INFO] Verification des dependances...
python -m pip install --upgrade pip > NUL
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERREUR] L'installation des dependances a echoue. Verifiez votre connexion internet.
    pause
    exit /b
)

:: 5. Programmation de l'ouverture du navigateur
start /b cmd /c "timeout /t 5 > NUL && start http://127.0.0.1:8000"

:: 6. Lancement du serveur Web
echo [INFO] Demarrage du serveur FastAPI...
echo [INFO] Interface accessible sur http://127.0.0.1:8000
echo [INFO] Appuyez sur CTRL+C pour quitter.
echo ===================================================
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

pause