'''Routes for user authentication. This includes registering a new user,
logging in, and verifying a JWT token.'''

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "db"))
from database import get_db
from models import User

from security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"]) # This means all routes in this router start with: /auth


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str | bytes
# Pydantic validates the request.

class LoginRequest(BaseModel):
    email: EmailStr
    password: str | bytes


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Creates a new user account. Returns a token immediately so the
    user is logged in right after registering."""
    existing = db.query(User).filter(User.email == body.email).first() # Check if email already exists in DB to avoid duplicates (should be unique). 
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = User(email=body.email, hashed_password=hash_password(body.password)) # 
    db.add(user) # Adds the new user object to the current SQLAlchemy session.
    db.commit() # Commits the transaction to the database.
    db.refresh(user) # Refreshes the Python object using the database state.

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)
# JWT : is based on header, playload and signature

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Logs an existing user in. Returns a token to use for all
    subsequent authenticated requests."""
    user = db.query(User).filter(User.email == body.email).first()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)