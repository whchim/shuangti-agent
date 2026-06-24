"""用户认证 API"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.user import (
    UserRegisterRequest, UserLoginRequest, ChangePasswordRequest,
)
from app.core.dependencies import get_current_user
from app.service.auth_service import (
    register_user, login_user, change_password,
)

router = APIRouter(prefix="/api/auth", tags=["用户认证"])


@router.post("/register")
async def register(req: UserRegisterRequest):
    try:
        user = await register_user(req.username, req.email or "", req.password)
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
    return {"message": "已退出登录"}


@router.post("/change-password")
async def change_password_endpoint(
    req: ChangePasswordRequest, user: dict = Depends(get_current_user),
):
    try:
        await change_password(user["user_id"], req.old_password, req.new_password)
        return {"message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
