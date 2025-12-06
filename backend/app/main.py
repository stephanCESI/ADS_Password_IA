from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.responses import FileResponse
from backend.app.routers import password
from backend.app.utils.dataset_loader import (
    create_weak_passwords_csv,
    create_strong_passwords_csv,
    create_labeled_dataset,
    create_processed_dataset
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = BASE_DIR / "frontend" / "static"
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(TEMPLATES_DIR / "index.html")

app.include_router(password.router)

def main():
    if not (BASE_DIR / "datasets" / "processed" / "passwords_processed.csv").exists():
        print("Génération du dataset en cours...")
        create_weak_passwords_csv()
        create_strong_passwords_csv()
        create_labeled_dataset()
        create_processed_dataset()
    else:
        print("Dataset déjà présent. Démarrage rapide.")

if __name__ == "__main__":
    main()