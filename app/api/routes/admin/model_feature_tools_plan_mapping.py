from fastapi import APIRouter, HTTPException, Depends, Request
from db.models import Plan, Model, PlanModel, PlanModelCreate, Tool, PlanTool, PlanToolCreate
from sqlalchemy import select, join
from sqlalchemy.orm import Session
from app.core.security import require_admin_role_ids
from dotenv import load_dotenv
import os

load_dotenv()

MASTER_ADMIN_ID = os.getenv("MASTER_ADMIN_ID")

router = APIRouter()

#----------------- Plan and Model Mapping --------------------#
@router.post("/plan-model", summary="Map a model to a plan")
def create_plan_model_mapping(
    payload: PlanModelCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db

    # Check if plan and model exist
    plan = db.query(Plan).filter(Plan.id == payload.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    model = db.query(Model).filter(Model.id == payload.model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Check if mapping already exists
    existing = (
        db.query(PlanModel)
        .filter(
            PlanModel.plan_id == payload.plan_id, PlanModel.model_id == payload.model_id
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=409, detail="Mapping already exists")

    # Create mapping
    mapping = PlanModel(plan_id=payload.plan_id, model_id=payload.model_id)
    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    return {"message": "Model successfully mapped to plan", "mapping_id": mapping.id}


@router.get("/plan-model", summary="List all Plan-Model mappings")
def list_all_plan_model_mappings(
    request: Request, admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID))
):
    db: Session = request.state.db
    stmt = select(
        PlanModel.id.label("mapping_id"),
        Plan.id.label("plan_id"),
        Plan.name.label("plan_name"),
        Model.id.label("model_id"),
        Model.model_name,
        PlanModel.created_at,
        PlanModel.updated_at,
        PlanModel.is_active,
    ).select_from(
        join(PlanModel, Plan, PlanModel.plan_id == Plan.id).join(
            Model, PlanModel.model_id == Model.id
        )
    )

    results = db.execute(stmt).mappings().all()

    return {"count": len(results), "mappings": results}


@router.delete("/plan-model/{mapping_id}", summary="Delete a Plan-Model mapping by ID")
def delete_plan_model_mapping(
    mapping_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db

    mapping = db.query(PlanModel).filter(PlanModel.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    db.delete(mapping)
    db.commit()

    return {"message": "Mapping deleted successfully", "mapping_id": mapping_id}


#----------------- Plan and Tools Mapping --------------------#

@router.post("/plan-tool", summary="Map a tool to a plan")
def create_plan_tool_mapping(
    payload: PlanToolCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db

    # Check if plan and model exist
    plan = db.query(Plan).filter(Plan.id == payload.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    tool = db.query(Tool).filter(Tool.id == payload.tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    # Check if mapping already exists
    existing = (
        db.query(PlanTool)
        .filter(
            PlanTool.plan_id == payload.plan_id, PlanTool.tool_id == payload.tool_id
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=409, detail="Mapping already exists")

    # Create mapping
    mapping = PlanTool(plan_id=payload.plan_id, tool_id=payload.tool_id)
    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    return {"message": "Tool successfully mapped to plan", "mapping_id": mapping.id}


@router.get("/plan-tool", summary="List all Plan-Tool mappings")
def list_all_plan_tool_mappings(
    request: Request, admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID))
):
    db: Session = request.state.db
    stmt = select(
        PlanTool.id.label("mapping_id"),
        Plan.id.label("plan_id"),
        Plan.name.label("plan_name"),
        Tool.id.label("tool_id"),
        Tool.tool_name,
        PlanTool.created_at,
        PlanTool.updated_at,
        PlanTool.is_active,
    ).select_from(
        join(PlanTool, Plan, PlanTool.plan_id == Plan.id).join(
            Tool, PlanTool.tool_id == Tool.id
        )
    )

    results = db.execute(stmt).mappings().all()

    return {"count": len(results), "mappings": results}


@router.delete("/plan-tool/{mapping_id}", summary="Delete a Plan-Tool mapping by ID")
def delete_plan_tool_mapping(
    mapping_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db

    mapping = db.query(PlanTool).filter(PlanTool.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    db.delete(mapping)
    db.commit()

    return {"message": "Mapping deleted successfully", "mapping_id": mapping_id}
