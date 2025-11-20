from fastapi import APIRouter
from ..models.password_models import PasswordRequest
from ..services.password_services import analyse_password

router = APIRouter()

@router.post("/test-password")
async def test_password(data: PasswordRequest):
    return analyse_password(data.password)
