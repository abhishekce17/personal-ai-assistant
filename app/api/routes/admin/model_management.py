from dotenv import load_dotenv
from fastapi import HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import ModelCreate, Model, ModelUpdate, User
from utils.db import deactivate_row, unset_default_for_all, activate_row, list_with_count
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

    if model_data.is_default:
        await unset_default_for_all(db, Model)

    model = Model(
        model_name=model_data.model_name,
        model_description=model_data.model_description,
        model_provider=model_data.model_provider,
        model_image=model_data.model_image,
        tool_support=model_data.tool_support,
        is_default=model_data.is_default,
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

    if model_data.is_default is True:
        await unset_default_for_all(db, Model)

    if model_data.model_name is not None:
        model.model_name = model_data.model_name
    if model_data.model_description is not None:
        model.model_description = model_data.model_description
    if model_data.model_provider is not None:
        model.model_provider = model_data.model_provider
    if model_data.model_image is not None:
        model.model_image = model_data.model_image
    if model_data.tool_support is not None:
        model.tool_support = model_data.tool_support
    if model_data.is_default is not None:
        model.is_default = model_data.is_default

    await db.commit()
    await db.refresh(model)

    return {
        "success": True,
        "message": "Model updated",
        "model": {"id": model.id, "name": model.model_name},
    }


@router.get("/list", summary="List all models")
async def list_models(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    data = await list_with_count(db, Model, User, User.default_model_id, Model.id, "user_count")
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