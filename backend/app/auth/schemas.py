from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = "faculty"
    department: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    department: Optional[str]

    class Config:
        from_attributes = True
