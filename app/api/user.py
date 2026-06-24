"""用户管理 API"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.user import (
    UserProfileUpdate, UserProfile,
    DeleteAccountRequest, ChangeUsernameRequest,
)
from app.core.dependencies import get_current_user
from app.service.auth_service import (
    get_user_profile, update_user_profile, delete_account, change_username,
)

router = APIRouter(prefix="/api/user", tags=["用户管理"])


@router.get("/profile", response_model=UserProfile)
async def get_profile(user: dict = Depends(get_current_user)):
    profile = await get_user_profile(user["user_id"])
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    return profile


@router.put("/profile", response_model=UserProfile)
async def update_profile(req: UserProfileUpdate, user: dict = Depends(get_current_user)):
    await update_user_profile(user["user_id"], req.email, req.nickname, req.avatar)
    profile = await get_user_profile(user["user_id"])
    return profile


@router.delete("/account")
async def delete_account_endpoint(
    req: DeleteAccountRequest, user: dict = Depends(get_current_user),
):
    try:
        await delete_account(user["user_id"], req.password)
        return {"message": "账号已注销"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/username")
async def change_username_endpoint(
    req: ChangeUsernameRequest, user: dict = Depends(get_current_user),
):
    try:
        await change_username(user["user_id"], req.new_username)
        return {"message": "用户名已更新", "username": req.new_username}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
