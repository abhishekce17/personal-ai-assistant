from fastapi import APIRouter, HTTPException, status, Depends, Request
from db.models import Login, Register, User
from utils.security import hash_password, create_jwt_token
from sqlalchemy.orm import Session
from utils.security import verify_password

router = APIRouter()


@router.post("/login")
def login(login: Login, request: Request):
    email = login.email
    password = login.password
    db: Session = request.state.db  # ✅ Use DB from middleware
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required",
        )
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Eamil or password is wrong",
        )
    # Verify password
    verify_password(login.password, user.password)

    # Generate JWT token
    token = create_jwt_token(user.email, user.id)

    return {
        "message": "Login successful",
        "token": token,
    }


@router.post("/register")
def register(register: Register, request: Request):
    db: Session = request.state.db  # ✅ Use DB from middleware

    if not register.terms_and_condition:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Terms and conditions must be accepted",
        )

    existing_user = db.query(User).filter(User.email == register.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )
    print(f"Registering user: {register}")

    new_user = User(
        name=register.name,
        email=register.email,
        password=hash_password(register.password),
        terms_and_condition=register.terms_and_condition,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_jwt_token(new_user.email, new_user.id)

    return {
        "message": "User registered successfully",
        "token": token,
    }
