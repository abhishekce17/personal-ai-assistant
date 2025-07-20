from fastapi import APIRouter, Request, status
from db.models import User
from sqlalchemy.orm import Session
from fastapi import Depends
from utils.security import get_current_user, verify_password, hash_password

router = APIRouter()


@router.get("/me")
def get_user(user: User = Depends(get_current_user)):
    return {"user": user}


@router.post("/update")
def update_user(
    request: Request,
    user: User = Depends(get_current_user),
    name: str = None,
    email: str = None,
    avatar_id: str = None,
    default_model_id: str = None
):
    db: Session = request.state.db
    if name:
        user.name = name
    if email:
        user.email = email
    if avatar_id:
        user.avatar = avatar_id
    if default_model_id:
        user.default_model_id = default_model_id

    db.commit()
    db.refresh(user)
    return {"user": user}


@router.put("/password")
def update_password(
    old_password: str,
    new_password: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    db: Session = request.state.db
    verify_password(old_password, user.password)
    user.password = hash_password(new_password)
    db.commit()
    return {"message": "password changes successfully"}


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    password: str, request: Request, user: User = Depends(get_current_user)
):
    db: Session = request.state.db
    verify_password(password, user.password)
    db.delete(user)
    db.commit()
