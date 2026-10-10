from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def register_user(db: Session, user_in: UserCreate) -> Tuple[Optional[User], Optional[str]]:
    existing = get_user_by_email(db, user_in.email)
    if existing:
        return None, "A user with this email already exists"

    user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, None


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

    
def delete_user_and_data(db: Session, user: User) -> None:
    """Cascade deletion of all user sessions, check-ins, and reflections (FR-005, FR-043)."""
    db.delete(user)
    db.commit()