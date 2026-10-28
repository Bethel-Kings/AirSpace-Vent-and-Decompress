from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.auth import delete_user_and_data

router = APIRouter(tags=["Users & Account"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile."""
    return current_user


@router.delete("/account", status_code=status.HTTP_200_OK)
def delete_account(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FR-052: Deletes the user account and all associated sessions,
    check-ins, and reflections in a single cascading operation.
    """
    delete_user_and_data(db, current_user)
    response.delete_cookie(key="access_token")
    return {"message": "Account and all associated data permanently deleted."}
