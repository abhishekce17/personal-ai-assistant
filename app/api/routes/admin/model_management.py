from dotenv import load_dotenv
from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session, defer
from db.models import ModelCreate, Model
from utils.db import unset_default_for_all
from app.core.security import require_admin_role_ids
from fastapi import APIRouter
import os

load_dotenv()

router = APIRouter()

MASTER_ADMIN_ID = os.getenv("MASTER_ADMIN_ID")


@router.post("/create", summary="Create a new AI model")
def create_model(
    model_data: ModelCreate,
    request: Request = None,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db

    existing = db.query(Model).filter(Model.model_name == model_data.model_name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Model already exists")

    if model_data.is_default:
        unset_default_for_all(db, Model)

    model = Model(
        model_name=model_data.model_name,
        model_description=model_data.model_description,
        model_provider=model_data.model_provider,
        model_image=model_data.model_image,
        tool_support=model_data.tool_support,
        is_default=model_data.is_default,
    )

    db.add(model)
    db.commit()
    db.refresh(model)

    return {
        "message": "Model created",
        "model": {"id": model.id, "name": model.model_name},
    }


@router.get("/list", summary="List all models")
def list_models(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db
    models = db.query(Model).options(defer(Model.model_description)).all()
    return models


@router.delete("/delete/{model_id}", summary="Delete a model")
def delete_model(
    model_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    db.delete(model)
    db.commit()
    return {"message": f"Model '{model.model_name}' deleted"}
