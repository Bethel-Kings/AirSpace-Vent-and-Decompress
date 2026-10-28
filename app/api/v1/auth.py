from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import authenticate_user, invalidate_sessions, issue_token, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    """Registers a new user with an Argon2id-hashed password (FR-001, FR-002)."""
    user, error = register_user(db, user_in)
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    return user


@router.post("/login", response_model=Token)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def login(request: Request, login_in: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticates a user and returns an access token + sets HTTP-only cookie."""
    user = authenticate_user(db, login_in.email, login_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = issue_token(user)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        samesite="lax",
        max_age=86400,
        secure=settings.ENVIRONMENT == "production",
    )
    return Token(access_token=token, token_type="bearer")


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invalidates outstanding tokens and clears the session cookie (FR-004)."""
    invalidate_sessions(db, current_user)
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}
