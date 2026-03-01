from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db.models import SystemArtifact
from app.core.security import get_current_user
from typing import List

router = APIRouter()

class StaticDataRequest(BaseModel):
    reference_keys: List[str]

@router.post("/fetch", summary="Get active static data by one or multiple reference keys")
async def get_static_data_by_reference_keys(
    payload: StaticDataRequest,
    request: Request,
    user=Depends(get_current_user), # Authentication required for users
):
    if not payload.reference_keys:
        return {"success": True, "data": {}, "message": "No reference keys provided"}

    db: AsyncSession = request.state.db

    # Query the SystemArtifact table for all matching keys
    result = await db.execute(
        select(SystemArtifact)
        .where(
            (SystemArtifact.reference_key.in_(payload.reference_keys)) &
            (SystemArtifact.is_active == True)
        )
        # Order by key, then by revision descending so we can pick the latest below
        .order_by(SystemArtifact.reference_key, desc(SystemArtifact.revision_id))
    )
    artifacts = result.scalars().all()
    
    # Process results: keep only the latest revision for each reference_key
    latest_artifacts = {}
    for artifact in artifacts:
        if artifact.reference_key not in latest_artifacts:
            latest_artifacts[artifact.reference_key] = {
                "reference_key": artifact.reference_key,
                "revision_id": artifact.revision_id,
                "media_type": artifact.media_type.value if hasattr(artifact.media_type, 'value') else artifact.media_type,
                "artifact_payload": artifact.artifact_payload,
                "updated_at": artifact.updated_at
            }

    # Return the payload and metadata as a dictionary mapped by reference_key
    return {
        "success": True,
        "data": latest_artifacts,
        "message": "Static data retrieved successfully"
    }
