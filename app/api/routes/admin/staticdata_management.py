from dotenv import load_dotenv
from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db.models import SystemArtifact, StaticdataCreate, StaticdataUpdate
from app.core.security import require_admin_role_ids
from fastapi import APIRouter
import os

from utils.db import activate_row, deactivate_row

load_dotenv()

MASTER_ADMIN_ID = os.getenv("MASTER_ADMIN_ID")

router = APIRouter()


@router.post("/create", summary="Create a new static artifact")
def create_static_artifact(
    static_data: StaticdataCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db

    revision_id = static_data.revision_id or 1

    existing = (
        db.query(SystemArtifact)
        .filter(
            SystemArtifact.reference_key == static_data.reference_key,
            SystemArtifact.revision_id == revision_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Static data already exists, consider updating it instead or changing the revision ID")
    
    else:
        new_static_data = SystemArtifact(
            reference_key=static_data.reference_key,
            artifact_payload=static_data.artifact_payload,
            media_type=static_data.media_type,
            revision_id=revision_id,
            description=static_data.description
        )
   
        db.add(new_static_data)
        db.commit()
        db.refresh(new_static_data)
        return {"message": "Static data created", "static_data": {"id": new_static_data.id, "reference_key": new_static_data.reference_key}}


@router.get("/list", summary="List all static artifacts")
def list_static_artifacts(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db
    artifacts = db.query(SystemArtifact).order_by(SystemArtifact.reference_key.asc()).all()
    return artifacts


@router.delete("/delete/{artifact_id}", summary="Delete a static artifact")
def delete_static_artifact(
    artifact_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db
    artifact = db.query(SystemArtifact).filter(SystemArtifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Static artifact not found")

    db.delete(artifact)
    db.commit()
    return {"message": "Static artifact deleted"}

from sqlalchemy.exc import IntegrityError

@router.put("/update/{artifact_id}", summary="Update an existing static artifact")
def update_static_artifact(
    artifact_id: str,
    static_data: StaticdataUpdate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db


    artifact = db.query(SystemArtifact).filter(SystemArtifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Static artifact not found")

  
    update_payload = static_data.model_dump(exclude_unset=True)
    if not update_payload:
        raise HTTPException(status_code=400, detail="No fields provided for update")


    for field, value in update_payload.items():
        setattr(artifact, field, value)

    try:
        db.commit()
        db.refresh(artifact)
    except IntegrityError:
        db.rollback() 
        raise HTTPException(
            status_code=409, 
            detail="Conflict: An artifact with this reference_key and revision_id already exists."
        )

    return {
        "message": "Static artifact updated",
        "static_data": {
            "id": artifact.id,
            "reference_key": artifact.reference_key,
            "revision_id": artifact.revision_id,
        },
    }
@router.patch("/activate-deactivate/{artifact_id}", summary="Activate or deactivate a static artifact")
def activate_deactivate_static_artifact(
    artifact_id: str,
    is_active: bool,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: Session = request.state.db

    if is_active:
        return activate_row(db, SystemArtifact, artifact_id)
    return deactivate_row(db, SystemArtifact, artifact_id)
