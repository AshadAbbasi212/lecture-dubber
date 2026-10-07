from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.api.deps import get_current_user, check_auth_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRegisterRequest(BaseModel):
    email: EmailStr
    password: str


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class UserResponse(BaseModel):
    id: str
    email: str


@router.post("/register", response_model=TokenResponse, dependencies=[Depends(check_auth_rate_limit)])
def register(req: AuthRegisterRequest, db: Session = Depends(get_db)):
    if len(req.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )

    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    user = User(
        email=req.email.lower(),
        password_hash=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email
    )


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(check_auth_rate_limit)])
def login(req: AuthLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email
    )


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email)
