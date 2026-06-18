"""用户认证 API"""
from fastapi import APIRouter, HTTPException
from app.models.user import UserRegisterRequest, UserLoginRequest, UserProfile, UserProfileUpdate
from app.core.dependencies import get_current_user
from app.service.auth_service import register_user, login_user, get_user_profile, update_user_profile

router = APIRouter(prefix="/api/auth", tags=["用户认证"])


@router.post("/register")
async def register(req: UserRegisterRequest):
    try:
        user = await register_user(req.username, req.email, req.password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(req: UserLoginRequest):
    try:
        result = await login_user(req.username, req.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout():
    # token 黑名单为可选功能，此处预留
    return {"message": "已退出登录"}
