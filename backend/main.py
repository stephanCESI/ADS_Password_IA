from fastapi import FastAPI
from fastapi import Body
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Autoriser le front local à faire des requêtes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"]
)

# GET pour la page principale
@app.get("/")
def index():
    return FileResponse(os.path.join("frontend", "index.html"))

# Pydantic model
class PasswordRequest(BaseModel):
    password: str

# POST endpoint
@app.api_route("/test-password", methods=["POST"])
async def test_password(data: PasswordRequest = Body(...)):
    pw = data.password
    return {
        "length": len(pw),
        "has_digit": any(c.isdigit() for c in pw),
        "has_upper": any(c.isupper() for c in pw),
        "has_lower": any(c.islower() for c in pw),
        "has_special": any(not c.isalnum() for c in pw)
    }
