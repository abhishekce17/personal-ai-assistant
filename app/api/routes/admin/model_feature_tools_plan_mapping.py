from fastapi import APIRouter, HTTPException, Depends, Request
from db.models import Plan, Model, PlanModel, PlanModelCreate, Tool, PlanTool, PlanToolCreate, PlanModelUpdate
from sqlalchemy import select, join
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import require_admin_role_ids
from dotenv import load_dotenv
import os

from utils.db import activate_row, deactivate_row, unset_default_for_all

load_dotenv()

MASTER_ADMIN_ID = os.getenv("MASTER_ADMIN_ID")

router = APIRouter()

#----------------- Plan and Model Mapping --------------------#
@router.post("/plan-model", summary="Map a model to a plan")
async def create_plan_model_mapping(
    payload: PlanModelCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    # Check if plan and model exist
    result = await db.execute(select(Plan).where(Plan.id == payload.plan_id))
    plan = result.scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    result = await db.execute(select(Model).where(Model.id == payload.model_id))
    model = result.scalars().first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Check if mapping already exists
    result = await db.execute(
        select(PlanModel)
        .where(PlanModel.plan_id == payload.plan_id)
        .where(PlanModel.model_id == payload.model_id)
    )
    existing = result.scalars().first()

    if existing:
        raise HTTPException(status_code=409, detail="Mapping already exists")

    # If setting as default, unset other models of the same type for this plan
    if payload.is_default:
        await unset_default_for_all(
            db, 
            PlanModel, 
            condition=(
                (PlanModel.plan_id == payload.plan_id) & 
                (PlanModel.model_id.in_(
                    select(Model.id).where(Model.model_type == model.model_type)
                ))
            )
        )

    # Create mapping
    mapping = PlanModel(
        plan_id=payload.plan_id, 
        model_id=payload.model_id,
        is_default=payload.is_default or False
    )
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)

    return {"message": "Model successfully mapped to plan", "mapping_id": mapping.id, "success": True}


@router.get("/plan-model", summary="List all Plan-Model mappings")
async def list_all_plan_model_mappings(
    request: Request, admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID))
):
    db: AsyncSession = request.state.db
    stmt = select(
        PlanModel.id.label("mapping_id"),
        Plan.id.label("plan_id"),
        Plan.name.label("plan_name"),
        Model.id.label("model_id"),
        Model.model_name,
        PlanModel.created_at,
        PlanModel.updated_at,
        PlanModel.is_active,
        PlanModel.is_default,
    ).select_from(
        join(PlanModel, Plan, PlanModel.plan_id == Plan.id).join(
            Model, PlanModel.model_id == Model.id
        )
    )

    result = await db.execute(stmt)
    results = result.mappings().all()

    return {"success": True, "count": len(results), "mappings": results}


@router.delete("/plan-model/{mapping_id}", summary="Delete a Plan-Model mapping by ID")
async def delete_plan_model_mapping(
    mapping_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    result = await db.execute(select(PlanModel).where(PlanModel.id == mapping_id))
    mapping = result.scalars().first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    await db.delete(mapping)
    await db.commit()

    return {"message": "Mapping deleted successfully", "mapping_id": mapping_id, "success": True}

@router.patch("/plan-model/{mapping_id}", summary="Activate or Deactivate a Plan-Model mapping by ID")
async def activate_deactivate_plan_model_mapping(
    mapping_id: str,
    is_active: bool,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    if( is_active ):
        return await activate_row(db, PlanModel, mapping_id)
    elif (not is_active):
        return await deactivate_row(db, PlanModel, mapping_id)

@router.patch("/plan-model-update/{mapping_id}", summary="Update a Plan-Model mapping (is_default/is_active)")
async def update_plan_model_mapping(
    mapping_id: str,
    payload: PlanModelUpdate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    result = await db.execute(select(PlanModel).where(PlanModel.id == mapping_id))
    mapping = result.scalars().first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    if payload.is_active is not None:
        mapping.is_active = payload.is_active

    if payload.is_default is True:
        # Fetch model type for context
        result = await db.execute(select(Model).where(Model.id == mapping.model_id))
        model = result.scalars().first()
        
        await unset_default_for_all(
            db, 
            PlanModel, 
            condition=(
                (PlanModel.plan_id == mapping.plan_id) & 
                (PlanModel.model_id.in_(
                    select(Model.id).where(Model.model_type == model.model_type)
                ))
            )
        )
        mapping.is_default = True
    elif payload.is_default is False:
        mapping.is_default = False

    await db.commit()
    await db.refresh(mapping)

    return {"success": True, "message": "Mapping updated", "data": {"id": mapping.id, "is_default": mapping.is_default}}

#----------------- Plan and Tools Mapping --------------------#

@router.post("/plan-tool", summary="Map a tool to a plan")
async def create_plan_tool_mapping(
    payload: PlanToolCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    # Check if plan and model exist
    result = await db.execute(select(Plan).where(Plan.id == payload.plan_id))
    plan = result.scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    result = await db.execute(select(Tool).where(Tool.id == payload.tool_id))
    tool = result.scalars().first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    # Check if mapping already exists
    result = await db.execute(
        select(PlanTool)
        .where(PlanTool.plan_id == payload.plan_id)
        .where(PlanTool.tool_id == payload.tool_id)
    )
    existing = result.scalars().first()

    if existing:
        raise HTTPException(status_code=409, detail="Mapping already exists")

    # Create mapping
    mapping = PlanTool(plan_id=payload.plan_id, tool_id=payload.tool_id)
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)

    return {"success": True, "mapping_id": mapping.id, "message": "Tool successfully mapped to plan"}


@router.get("/plan-tool", summary="List all Plan-Tool mappings")
async def list_all_plan_tool_mappings(
    request: Request, admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID))
):
    db: AsyncSession = request.state.db
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

    result = await db.execute(stmt)
    results = result.mappings().all()

    return {"success": True, "count": len(results), "mappings": results}


@router.delete("/plan-tool/{mapping_id}", summary="Delete a Plan-Tool mapping by ID")
async def delete_plan_tool_mapping(
    mapping_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    result = await db.execute(select(PlanTool).where(PlanTool.id == mapping_id))
    mapping = result.scalars().first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")

    await db.delete(mapping)
    await db.commit()

    return {"message": "Mapping deleted successfully", "mapping_id": mapping_id, "success": True}

@router.patch("/plan-tool/{mapping_id}", summary="Activate or Deactivate a Plan-Tool mapping by ID")
async def activate_deactivate_plan_tool_mapping(
    mapping_id: str,
    is_active: bool,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    if( is_active ):
        return await activate_row(db, PlanTool, mapping_id)
    elif (not is_active):
        return await deactivate_row(db, PlanTool, mapping_id)