from fastapi import APIRouter

from app.db.repository import users_repo
from app.schemas.users import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def list_users(active_only: bool = True):
    return users_repo.list_users(active_only=active_only)


@router.patch("/{user_id}/deactivate")
def deactivate_user(user_id: int):
    users_repo.set_user_active(user_id, is_active=False)
    return {"status": "deactivated"}
