from dotenv import load_dotenv
from fastapi import HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Plan, PlanCreate
from sqlalchemy.exc import IntegrityError
from utils.db import activate_row, deactivate_row, unset_default_for_all
from app.core.security import require_admin_role_ids
from fastapi import APIRouter
import os

load_dotenv()

MASTER_ADMIN_ID = os.getenv("MASTER_ADMIN_ID")

router = APIRouter()


@router.post("/create", summary="Create a new plan")
async def create_plan(
    plan_data: PlanCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    result = await db.execute(select(Plan).where(Plan.name == plan_data.name))
    existing = result.scalars().first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Plan already exists")
    if plan_data.is_default:
        await unset_default_for_all(db, Plan)
    plan = Plan(
        name=plan_data.name,
        slug=plan_data.name.lower().replace(" ", "_"),
        price=plan_data.price,
        description=plan_data.description,
        is_default=plan_data.is_default,
    )

    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    return {"message": "Plan created", "plan": {"id": plan.id, "name": plan.name}}


@router.get("/list", summary="List all plans")
async def list_plans(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    result = await db.execute(select(Plan))
    plans = result.scalars().all()
    return plans


@router.delete("/delete/{plan_id}", summary="Delete a plan")
async def delete_plan(
    plan_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalars().first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    await db.delete(plan)
    await db.commit()
    return {"message": "Plan deleted"}


@router.put("/update/{plan_id}", summary="Update an existing plan")
async def update_plan(
    plan_id: str,
    plan_data: PlanCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalars().first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if plan_data.name:
        plan.name = plan_data.name
        plan.slug = plan_data.name.lower().replace(" ", "-")

    if plan_data.price is not None:
        plan.price = plan_data.price

    if plan_data.description:
        plan.description = plan_data.description

    try:
        await db.commit()
        await db.refresh(plan)
    except IntegrityError:
        await db.rollback() # Important: Reset the session state
        # This catches the duplicate name error efficiently
        raise HTTPException(status_code=409, detail="Plan name already exists")

    return {
        "message": "Plan updated",
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "price": plan.price,
            "description": plan.description,
        },
    }

@router.patch("/activate-deactivate/{plan_id}", summary="Activate or Deactivate a plan by ID")
async def activate_deactivate_plan(
    plan_id: str,
    is_active: bool,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    if( is_active ):
        return await activate_row(db, Plan, plan_id)
    elif (not is_active):
        return await deactivate_row(db, Plan, plan_id)