import os
from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy.orm import Session
from db.models import Admin, AdminRegister, Login
from app.core.security import hash_password, verify_password, create_jwt_token

router = APIRouter()


@router.post("/login")
def admin_login(login: Login, request: Request, response: Response):
    is_production = os.getenv("ENVIRONMENT") == "production"
    db: Session = request.state.db
    email = login.email
    password = login.password

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    admin = db.query(Admin).filter(Admin.email == email).first()
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
        samesite="lax",            # ✅ Protects against CSRF
        secure=is_production,      # ⚠️ Set to True if using HTTPS (Production), False for localhost (Development)
    )

    return {
        "message": "Admin login successful",
        "accessToken": token, 
    }

@router.post("/register")
def admin_register(register: AdminRegister, request: Request):
    db: Session = request.state.db

    existing_admin = db.query(Admin).filter(Admin.email == register.email).first()
    if existing_admin:
        raise HTTPException(status_code=409, detail="Admin already exists")

    new_admin = Admin(
        name=register.name,
        email=register.email,
        password=hash_password(register.password),
        role_id=register.role_id,
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    token = create_jwt_token(new_admin.email, new_admin.id)

    return {
        "message": "Admin registered successfully",
        "token": token,
    }
