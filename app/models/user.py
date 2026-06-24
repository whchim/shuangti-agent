from typing import Optional
from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    email: Optional[str] = ""


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    profile_data: dict = {}
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    email: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=100)


class DeleteAccountRequest(BaseModel):
    password: str = Field(min_length=1)


class ChangeUsernameRequest(BaseModel):
    new_username: str = Field(min_length=1, max_length=50)
