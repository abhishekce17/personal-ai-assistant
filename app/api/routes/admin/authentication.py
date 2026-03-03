import os
from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Admin, AdminRegister, Login
from app.core.security import hash_password, verify_password, create_jwt_token

router = APIRouter()


@router.post("/login")
async def admin_login(login: Login, request: Request, response: Response):
    is_production = os.getenv("ENVIRONMENT") == "production"
    db: AsyncSession = request.state.db
    email = login.email
    password = login.password

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    result = await db.execute(select(Admin).where(Admin.email == email))
    admin = result.scalars().first()
    
    if not admin:
        raise HTTPException(status_code=401, detail="Email or password is incorrect")

    verify_password(password, admin.password)

    token = create_jwt_token(admin.email, admin.id)
    response.set_cookie(
        key="access_token",        # The name of the cookie
        value=token,               # The JWT
        httponly=True,             # ✅ JavaScript cannot read this (Security)
        max_age=60 * 60 * 24,      # 1 day in seconds
        expires=60 * 60 * 24,      # (Optional) consistency for older browsers
        samesite="none",           # ✅ Required for cross-origin cookie delivery (frontend ≠ backend domain)
        secure=True,               # ✅ Required when samesite="none" (backend must be HTTPS)
    )

    return {
        "message": "Admin login successful",
        "accessToken": token, 
    }

@router.post("/register")
async def admin_register(register: AdminRegister, request: Request):
    db: AsyncSession = request.state.db

    result = await db.execute(select(Admin).where(Admin.email == register.email))
    existing_admin = result.scalars().first()
    
    if existing_admin:
        raise HTTPException(status_code=409, detail="Admin already exists")

    new_admin = Admin(
        name=register.name,
        email=register.email,
        password=hash_password(register.password),
        role_id=register.role_id,
    )

    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)

    token = create_jwt_token(new_admin.email, new_admin.id)

    return {
        "message": "Admin registered successfully",
        "token": token,
    }


@router.post("/logout")
async def admin_logout(response: Response):
    response.delete_cookie(
        key="access_token",
        samesite="none",
        secure=True,
        httponly=True,
    )
    return {"message": "Admin logged out successfully"}

