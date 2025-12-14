from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.security import require_admin_role_ids
from db.models import FeatureFlag, FeatureFlagCreate
from utils.db import activate_row, deactivate_row
import os

load_dotenv()

MASTER_ADMIN_ID = os.getenv("MASTER_ADMIN_ID")

router = APIRouter()

@router.post("/create", summary="Create a new feature flag")
def create_feature_flag(
    feature_flag_data: FeatureFlagCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db

    revision_id = feature_flag_data.revision_id or 1

    existing = (
        db.query(FeatureFlag)
        .filter(
            FeatureFlag.reference_key == feature_flag_data.reference_key,
            FeatureFlag.revision_id == revision_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Feature flag already exists, consider updating it instead or changing the revision ID",
        )

    else:
        new_feature_flag = FeatureFlag(
            reference_key=feature_flag_data.reference_key,
            revision_id=revision_id,
            description=feature_flag_data.description,
        )

        db.add(new_feature_flag)
        db.commit()
        db.refresh(new_feature_flag)
        return {
            "message": "Feature flag created",
            "feature_flag": {
                "id": new_feature_flag.id,
                "reference_key": new_feature_flag.reference_key,
            },
        }


@router.patch("/toggle/{feature_id}", summary="Toggle feature flag status")
def toggle_feature_flag(
    feature_id: str,
    is_active: bool,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db

    if is_active:
        return activate_row(db, FeatureFlag, feature_id)
    return deactivate_row(db, FeatureFlag, feature_id)


@router.delete("/delete/{feature_id}", summary="Delete a feature flag")
def delete_feature_flag(
    feature_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db
    feature_flag = db.query(FeatureFlag).filter(FeatureFlag.id == feature_id).first()
    if not feature_flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    db.delete(feature_flag)
    db.commit()
    return {"message": "Feature flag deleted"}


@router.get("/list", summary="List all feature flags")
def list_feature_flags(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db
    feature_flags = db.query(FeatureFlag).order_by(FeatureFlag.reference_key.asc()).all()
    return feature_flags
