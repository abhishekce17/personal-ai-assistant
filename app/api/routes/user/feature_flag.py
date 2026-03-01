from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db.models import FeatureFlag
from app.core.security import get_current_user

router = APIRouter()

@router.get("/active", summary="Get all active feature flags")
async def get_active_feature_flags(
    request: Request,
    user=Depends(get_current_user), # Authentication required for users
):
    db: AsyncSession = request.state.db

    # Query the FeatureFlag table for all active flags
    result = await db.execute(
        select(FeatureFlag)
        .where(FeatureFlag.is_active == True)
        # Order by key, then by revision descending so we can pick the latest below
        .order_by(FeatureFlag.reference_key, desc(FeatureFlag.revision_id))
    )
    flags = result.scalars().all()
    
    # Process results: keep only the latest revision for each reference_key
    latest_flags = {}
    for flag in flags:
        if flag.reference_key not in latest_flags:
            latest_flags[flag.reference_key] = {
                "reference_key": flag.reference_key,
                "revision_id": flag.revision_id,
                "updated_at": flag.updated_at
            }

    # Return the payload and metadata as a dictionary mapped by reference_key
    return {
        "success": True,
        "data": latest_flags,
        "message": "Active feature flags retrieved successfully"
    }
