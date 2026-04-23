from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from backend.app.routers import password

# --- CONFIGURATION CHEMINS ---
BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = BASE_DIR / "frontend" / "static"
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"

# --- INITIALISATION API ---
app = FastAPI(title="Cyber Sentry AI - Password Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTAGE DES FICHIERS STATIQUES ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- ROUTES ---
@app.get("/")
def serve_index():
    return FileResponse(TEMPLATES_DIR / "index.html")

app.include_router(password.router)