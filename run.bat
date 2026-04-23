@echo off
title Cyber Sentry AI - Lanceur
echo ===================================================
echo      LANCEMENT DE CYBER SENTRY AI (POC)
echo ===================================================

:: 1. Verification et creation de l'environnement virtuel
if not exist ".venv\Scripts\activate" (
    echo [INFO] Creation de l'environnement virtuel Python...
    python -m venv .venv
)

:: 2. Activation de l'environnement
echo [INFO] Activation de l'environnement...
call .venv\Scripts\activate

:: 3. Installation des dependances
echo [INFO] Verification des dependances (cela peut prendre un instant)...
python -m pip install -r requirements.txt > NUL 2>&1

:: 4. Programmation de l'ouverture du navigateur
:: Ouvre une invite invisible qui attend 3 secondes puis lance l'URL
start /b cmd /c "timeout /t 3 > NUL && start http://127.0.0.1:8000"

:: 5. Lancement du serveur Web
echo [INFO] Demarrage du serveur FastAPI...
echo [INFO] Appuyez sur CTRL+C pour quitter.
echo ===================================================
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

pause