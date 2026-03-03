from fastapi import APIRouter, Request, status
from db.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.security import get_current_user, verify_password, hash_password

router = APIRouter()


@router.get("/me")
async def get_user(user: User = Depends(get_current_user)):
    return {"user": user, "success": True}


@router.post("/update")
async def update_user(
    request: Request,
    user: User = Depends(get_current_user),
    name: str = None,
    email: str = None,
    avatar_id: str = None,
):
    db: AsyncSession = request.state.db
    if name:
        user.name = name
    if email:
        user.email = email
    if avatar_id:
        user.avatar = avatar_id

    await db.commit()
    await db.refresh(user)
    return {"success": True, "user": user, "message": "User updated successfully"}


@router.put("/password")
async def update_password(
    old_password: str,
    new_password: str,
    request: Request,
    user: User = Depends(get_current_user),
):
    db: AsyncSession = request.state.db
    verify_password(old_password, user.password)
    user.password = hash_password(new_password)
    await db.commit()
    return {"success": True, "data": None, "message": "Password changed successfully"}


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    password: str, request: Request, user: User = Depends(get_current_user)
):
    db: AsyncSession = request.state.db
    verify_password(password, user.password)
    await db.delete(user)
    await db.commit()
