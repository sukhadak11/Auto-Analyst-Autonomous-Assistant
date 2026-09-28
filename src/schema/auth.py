# These are moved directly from your routes.py; no fields or behavior are being changed.
from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str | bytes

class LoginRequest(BaseModel):
    email: EmailStr
    password: str | bytes

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    is_admin: bool
    is_active: bool