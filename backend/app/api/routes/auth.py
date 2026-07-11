from fastapi import APIRouter
from app.models.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest):
    user = {
        "name": body.email.split("@")[0],
        "frn": "",
        "initials": body.email[:2].upper(),
        "firm": "",
    }
    return {"token": "demo-token", "user": user}


@router.post("/logout")
async def logout():
    return {"ok": True}


@router.get("/me")
async def me():
    return {"user": None}
