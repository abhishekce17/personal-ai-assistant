from dotenv import load_dotenv
from fastapi import HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
async def create_static_artifact(
    static_data: StaticdataCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    revision_id = static_data.revision_id or 1

    result = await db.execute(
        select(SystemArtifact)
        .where(
            (SystemArtifact.reference_key == static_data.reference_key) &
            (SystemArtifact.revision_id == revision_id)
        )
    )
    existing = result.scalars().first()
    
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
        await db.commit()
        await db.refresh(new_static_data)
        return {"success": True, "message": "Static data created", "static_data": {"id": new_static_data.id, "reference_key": new_static_data.reference_key}}


@router.get("/list", summary="List all static artifacts")
async def list_static_artifacts(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    result = await db.execute(select(SystemArtifact).order_by(SystemArtifact.reference_key.asc()))
    artifacts = result.scalars().all()
    return {"success": True, "data": artifacts}


@router.delete("/delete/{artifact_id}", summary="Delete a static artifact")
async def delete_static_artifact(
    artifact_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    result = await db.execute(select(SystemArtifact).where(SystemArtifact.id == artifact_id))
    artifact = result.scalars().first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Static artifact not found")

    await db.delete(artifact)
    await db.commit()
    return {"success": True, "data": None, "message": "Static artifact deleted"}

from sqlalchemy.exc import IntegrityError

@router.put("/update/{artifact_id}", summary="Update an existing static artifact")
async def update_static_artifact(
    artifact_id: str,
    static_data: StaticdataUpdate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    result = await db.execute(select(SystemArtifact).where(SystemArtifact.id == artifact_id))
    artifact = result.scalars().first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Static artifact not found")

  
    update_payload = static_data.model_dump(exclude_unset=True)
    if not update_payload:
        raise HTTPException(status_code=400, detail="No fields provided for update")


    for field, value in update_payload.items():
        setattr(artifact, field, value)

    try:
        await db.commit()
        await db.refresh(artifact)
    except IntegrityError:
        await db.rollback() 
        raise HTTPException(
            status_code=409, 
            detail="Conflict: An artifact with this reference_key and revision_id already exists."
        )

    return {
        "success": True,
        "static_data": {
            "id": artifact.id,
            "reference_key": artifact.reference_key,
            "revision_id": artifact.revision_id,
        },
        "message": "Static artifact updated",
    }
@router.patch("/activate-deactivate/{artifact_id}", summary="Activate or deactivate a static artifact")
async def activate_deactivate_static_artifact(
    artifact_id: str,
    is_active: bool,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    if is_active:
        return await activate_row(db, SystemArtifact, artifact_id)
    return await deactivate_row(db, SystemArtifact, artifact_id)
