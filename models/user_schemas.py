# models/user_schemas.py
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password with minimum 6 characters")
    role: UserRole = Field(default=UserRole.USER, description="User role")

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores allowed)')
        return v.lower()

class UserLogin(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class UserResponse(UserBase):
    id: str
    role: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    login_count: int = 0

    class Config:
        from_attributes = True

class UserProfileResponse(UserResponse):
    preferences: Optional[Dict[str, Any]] = None

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password with minimum 6 characters")

    @validator('new_password')
    def passwords_different(cls, v, values):
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        return v

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    