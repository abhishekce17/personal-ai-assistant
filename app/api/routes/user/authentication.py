from fastapi import APIRouter, HTTPException, status, Depends, Request
from db.models import Login, Register, User, Plan, PlanModel, Model
from app.core.security import hash_password, create_jwt_token
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import verify_password

router = APIRouter()


@router.post("/login")
async def login(login: Login, request: Request):
    email = login.email
    password = login.password
    db: AsyncSession = request.state.db  # ✅ Use DB from middleware
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required",
        )
    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Eamil or password is wrong",
        )
    # Verify password
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is suppended, please contact customer support",
        )
    verify_password(login.password, user.password)

    # Generate JWT token
    token = create_jwt_token(user.email, user.id)

    return {
        "message": "Login successful",
        "token": token,
    }


@router.post("/register")
async def register(register: Register, request: Request):
    db: AsyncSession = request.state.db

    if not register.terms_and_condition:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Terms and conditions must be accepted",
        )

    result = await db.execute(select(User).where(User.email == register.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    result = await db.execute(select(Plan).where((Plan.is_default == True) & (Plan.is_active == True)))
    default_plan = result.scalars().first()
    
    if not default_plan:
        raise HTTPException(status_code=400, detail="No active plan found")

    result = await db.execute(
        select(PlanModel)
        .where(PlanModel.plan_id == default_plan.id)
        .join(Model)
        .where((Model.is_default == True) & (Model.is_active == True))
    )
    mapping = result.scalars().first()
    
    if not mapping:
        raise HTTPException(
            status_code=400, detail=f"No default model for {default_plan.name} plan"
        )

    new_user = User(
        name=register.name,
        email=register.email,
        password=hash_password(register.password),
        terms_and_condition=register.terms_and_condition,
        current_plan_id=default_plan.id,
        default_model_id=mapping.model_id,
        avatar="",
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_jwt_token(new_user.email, new_user.id)

    return {
        "message": "User registered successfully",
        "token": token,
    }
