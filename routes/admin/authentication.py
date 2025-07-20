from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm import Session
from db.models import Admin, AdminRegister, Login
from utils.security import hash_password, verify_password, create_jwt_token

router = APIRouter()

@router.post("/login")
def admin_login(login: Login, request: Request):
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

    return {
        "message": "Admin login successful",
        "token": token,
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
