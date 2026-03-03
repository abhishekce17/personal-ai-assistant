from dotenv import load_dotenv
from fastapi import HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.models import ModelCreate, Model, ModelUpdate, User, PlanModel
from utils.types import ModelType
from utils.db import deactivate_row, activate_row
from app.core.security import require_admin_role_ids
from fastapi import APIRouter
import os

load_dotenv()

router = APIRouter()

MASTER_ADMIN_ID = os.getenv("MASTER_ADMIN_ID")


@router.post("/create", summary="Create a new AI model")
async def create_model(
    model_data: ModelCreate,
    request: Request = None,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    result = await db.execute(select(Model).where(Model.model_name == model_data.model_name))
    existing = result.scalars().first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Model already exists")

    model = Model(
        model_name=model_data.model_name,
        model_description=model_data.model_description,
        model_provider=model_data.model_provider,
        model_type=model_data.model_type,
        model_image=model_data.model_image,
        tool_support=model_data.tool_support,
        context_window=model_data.context_window,
    )

    db.add(model)
    await db.commit()
    await db.refresh(model)

    return {
        "success": True,
        "message": "Model created",
        "model": {"id": model.id, "name": model.model_name},
    }

@router.put("/update/{model_id}", summary="Update an existing AI model")
async def update_model(
    model_id: str,
    model_data: ModelUpdate,
    request: Request = None,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalars().first()

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model_data.model_name is not None:
        model.model_name = model_data.model_name
    if model_data.model_description is not None:
        model.model_description = model_data.model_description
    if model_data.model_provider is not None:
        model.model_provider = model_data.model_provider
    if model_data.model_type is not None:
        model.model_type = model_data.model_type
    if model_data.model_image is not None:
        model.model_image = model_data.model_image
    if model_data.tool_support is not None:
        model.tool_support = model_data.tool_support
    if model_data.context_window is not None:
        model.context_window = model_data.context_window

    await db.commit()
    await db.refresh(model)

    return {
        "success": True,
        "message": "Model updated",
        "model": {"id": model.id, "name": model.model_name},
    }


@router.get("/types", summary="Get all available model types")
async def get_model_types(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    return {"success": True, "data": [t.value for t in ModelType]}


@router.get("/list", summary="List all models")
async def list_models(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    # Fetch all models
    result = await db.execute(select(Model))
    models = result.scalars().all()

    # Count users per model via plan membership:
    # Users → current_plan_id → PlanModel → model_id
    count_result = await db.execute(
        select(PlanModel.model_id, func.count(func.distinct(User.id)).label("cnt"))
        .join(User, User.current_plan_id == PlanModel.plan_id)
        .where(PlanModel.is_active == True)
        .group_by(PlanModel.model_id)
    )
    count_map = {str(row[0]).lower(): row[1] for row in count_result.all()}

    data = []
    for model in models:
        row_dict = {c.name: getattr(model, c.name) for c in Model.__table__.columns}
        row_dict["user_count"] = count_map.get(str(model.id).lower(), 0)
        data.append(row_dict)

    return {"success": True, "data": data}


@router.delete("/delete/{model_id}", summary="Delete a model")
async def delete_model(
    model_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalars().first()
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    await db.delete(model)
    await db.commit()
    return {"success": True, "data": None, "message": f"Model '{model.model_name}' deleted"}

@router.patch("/activate-deactivate/{model_id}", summary="Activate or Deactivate a model by ID")
async def activate_deactivate_model(
    model_id: str,
    is_active: bool,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    if( is_active ):
        return await activate_row(db, Model, model_id)
    elif (not is_active):
        return await deactivate_row(db, Model, model_id)