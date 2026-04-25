from fastapi import APIRouter, Query
from backend.app.models.password_models import PasswordRequest
from backend.app.services.password_services import analyse_password, generate_secure_password

router = APIRouter()

@router.post("/test-password")
async def test_password(data: PasswordRequest):
    return analyse_password(data.password, data.model_type)

@router.get("/generate-password")
async def get_generated_password(
    mode: str = Query("chunked_password", description="Mode de génération: 'chunked_password' ou 'diceware'")
):
    # La fonction retourne maintenant un dictionnaire (password, ai_score, ai_feedback, etc.)
    result = generate_secure_password(mode=mode)
    return result