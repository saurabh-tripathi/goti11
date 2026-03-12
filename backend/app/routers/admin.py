import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin_user, get_db
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/admin", tags=["admin"])


class UserPatch(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None
    prize_points: int | None = None


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), _: User = Depends(get_current_admin_user)):
    return db.query(User).all()


@router.patch("/users/{user_id}", response_model=UserResponse)
def patch_user(
    user_id: uuid.UUID,
    body: UserPatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.get("/cricapi/matches")
def cricapi_matches(
    _: User = Depends(get_current_admin_user),
):
    from app.services.cricket_api import get_current_matches
    return get_current_matches()
