from dotenv import load_dotenv
from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
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
def create_plan(
    plan_data: PlanCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db

    existing = db.query(Plan).filter(Plan.name == plan_data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Plan already exists")
    if plan_data.is_default:
        unset_default_for_all(db, Plan)
    plan = Plan(
        name=plan_data.name,
        slug=plan_data.name.lower().replace(" ", "_"),
        price=plan_data.price,
        description=plan_data.description,
        is_default=plan_data.is_default,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return {"message": "Plan created", "plan": {"id": plan.id, "name": plan.name}}


@router.get("/list", summary="List all plans")
def list_plans(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db
    plans = db.query(Plan).all()
    return plans


@router.delete("/delete/{plan_id}", summary="Delete a plan")
def delete_plan(
    plan_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    db.delete(plan)
    db.commit()
    return {"message": "Plan deleted"}


@router.put("/update/{plan_id}", summary="Update an existing plan")
def update_plan(
    plan_id: str,
    plan_data: PlanCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
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
        db.commit()
        db.refresh(plan)
    except IntegrityError:
        db.rollback() # Important: Reset the session state
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
def activate_deactivate_plan(
    plan_id: str,
    is_active: bool,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db

    if( is_active ):
        return activate_row(db, Plan, plan_id)
    elif (not is_active):
        return deactivate_row(db, Plan, plan_id)