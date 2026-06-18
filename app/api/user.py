"""用户管理 API"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.user import UserProfileUpdate, UserProfile
from app.core.dependencies import get_current_user
from app.service.auth_service import get_user_profile, update_user_profile

router = APIRouter(prefix="/api/user", tags=["用户管理"])


@router.get("/profile", response_model=UserProfile)
async def get_profile(user: dict = Depends(get_current_user)):
    profile = await get_user_profile(user["user_id"])
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    return profile


@router.put("/profile", response_model=UserProfile)
async def update_profile(req: UserProfileUpdate, user: dict = Depends(get_current_user)):
    await update_user_profile(user["user_id"], req.avatar, req.profile_data)
    profile = await get_user_profile(user["user_id"])
    return profile
