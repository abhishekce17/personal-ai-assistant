# Endoints for user management in the admin panel
#1. GET /admin/users -> snap shot of user info -> name, email, plan, status, created, last login, ----- done
#2 GET /admin/users/:id -> detailed user info -> all fields   ----- done
#3 PUT /admin/users/:id -> update user info -> name, email, plan, status --- i don't think we need this endpoint right now
#4 DELETE /admin/users/:id -> delete user -> soft delete by setting is_active to false  ----- done
#5 POST /admin/users/:id/activate -> activate user  ----- done
#6 POST /admin/users/:id/deactivate -> deactivate user  ----- done
#7 POST /admin/users/:id/logout-all -> to implement it i'll need an extra column to store the flag for invoking logout on all devices ---- i'll implement it later once i have completed application development
#8 POST /admin/users/:id/reset-password -> send reset password email link to user ---- i don't think we need this endpoint right now
#9 POST /admin/users/:id/send-email ---- i don't think we need this endpoint right now
#10 POST /admin/users/:id/notify ---- i will implement it later once i have completed application development
#11 POST /admin/users/:id/plan/:plan_id -> change user plan ----- done

from dotenv import load_dotenv
from fastapi import HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import User, Plan
from utils.db import activate_row, deactivate_row
from app.core.security import require_admin_role_ids
from fastapi import APIRouter
import os

load_dotenv()

MASTER_ADMIN_ID = os.getenv("MASTER_ADMIN_ID")

router = APIRouter()


@router.get("/users", summary="List all users")
async def list_users(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)), # Ensure only admins can access, dont remove this as this check for admin roles and admin token
):
    db: AsyncSession = request.state.db

    result = await db.execute(select(User.avatar, User.name, User.email, User.id, User.created_at, User.current_plan_id, User.is_active, Plan.name.label("plan_name"), Plan.slug).join(Plan, User.current_plan_id == Plan.id))
    users = result.mappings().all()
    return users;


@router.post("/users/{id}", summary="Get user details by ID")
async def get_user_details(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    user_id = request.path_params["id"];
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    result = await db.execute(
                select(
                    *[c.label(f"user_{c.name}") for c in User.__table__.c],
                    *[c.label(f"plan_{c.name}") for c in Plan.__table__.c],
                )
                .join(Plan, User.current_plan_id == Plan.id, isouter=True)
                .filter(User.id == user_id)
            )
    user = result.mappings().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/users/{id}/activate", summary="Activate or Deactivate a user by ID")
async def activate_user(
    is_active: bool,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    user_id = request.path_params["id"]
    if( is_active ):
        return await activate_row(db, User, user_id)
    elif (not is_active):
        return await deactivate_row(db, User, user_id)

@router.post("/users/{id}/plan/{plan_id}", summary="Change user plan by ID")
async def change_user_plan(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    user_id = request.path_params["id"]
    plan_id = request.path_params["plan_id"]

    if not user_id or not plan_id:
        raise HTTPException(status_code=400, detail="User ID and Plan ID are required")
    
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Plan).filter(Plan.id == plan_id))
    plan = result.scalars().first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    user.current_plan_id = plan_id
    await db.commit()

    return {"success": True, "message": "User plan changed successfully"}
