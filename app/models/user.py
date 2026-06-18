from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=100)
    email: EmailStr


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    avatar: Optional[str] = None
    profile_data: dict = {}

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    avatar: Optional[str] = None
    profile_data: Optional[dict] = None
