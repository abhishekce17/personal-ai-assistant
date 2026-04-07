from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Body, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, select
from app.core.security import get_current_user, verify_github_installation_ownership
from db.models import User, PendingState, Tool, FederatedIdentity, PlanTool
from pydantic import BaseModel
import hashlib
import base64
import os
from datetime import datetime, timedelta, timezone

router = APIRouter()


class AuthLinkRequest(BaseModel):
    tool_id: str
    state_hash: str | None = None

@router.post("/tool_auth_link", summary="Generate Tool Auth Link")
async def tool_auth_link(
    request: Request,
    response: Response,
    payload: AuthLinkRequest,
    user: User = Depends(get_current_user)
):
    """
    Generate a redirect link for Tool OAuth and store pending state.
    """
    db: AsyncSession = request.state.db

    # Check if the tool exists and is active
    result = await db.execute(select(Tool).where(Tool.id == payload.tool_id, Tool.is_active == True))
    tool = result.scalars().first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Tool not found or inactive."
        )

    base_link = tool.installation_url
    if not base_link:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Redirect link for {tool.tool_name} is not configured in tool settings."
        )

    # Validate that this tool is allowed by the user's current plan
    if user.current_plan_id:
        result = await db.execute(
            select(PlanTool).where(
                PlanTool.tool_id == tool.id,
                PlanTool.plan_id == user.current_plan_id,
                PlanTool.is_active == True
            )
        )
        plan_tool_mapping = result.scalars().first()
        if not plan_tool_mapping:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your current plan does not support the '{tool.tool_name}' tool."
            )
    else:
        # If user has no plan (shouldn't happen with default plans), deny access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must have an active plan to connect tools."
        )

    # Check for existing valid installation
    result = await db.execute(select(FederatedIdentity).where(
        FederatedIdentity.user_id == user.id,
        func.lower(FederatedIdentity.provider) == tool.tool_provider.lower(),
        FederatedIdentity.is_active == True,
        FederatedIdentity.installation_id != None,
        FederatedIdentity.refresh_token != None,
        or_(
            FederatedIdentity.expires_at == None,
            FederatedIdentity.expires_at > datetime.now(timezone.utc)
        )
    ))
    existing_identity = result.scalars().first()

    if existing_identity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User is already connected to {tool.tool_provider}."
        )
    
    # Check for existing pending state for this user and platform
    result = await db.execute(select(PendingState).where(
        PendingState.user_id == str(user.id),
        PendingState.platform == tool.tool_provider
    ))
    existing_pending = result.scalars().first()

    if existing_pending:
        # Only update state hash if it doesn't match
        if existing_pending.state_hash != payload.state_hash:
            existing_pending.state_hash = payload.state_hash
            existing_pending.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            await db.commit()
            await db.refresh(existing_pending)
        pending_state = existing_pending
            
    else:
        # Create pending state
        pending_state = PendingState(
            user_id=str(user.id),
            state_hash=payload.state_hash,
            platform=tool.tool_provider,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        db.add(pending_state)
        await db.commit()
        await db.refresh(pending_state)
    
    

    # Append state to the link (assuming the base link accepts query params)
    # Check if '?' exists to decide between '?' and '&'
    separator = "&" if "?" in base_link else "?"
    redirect_link = f"{base_link}{separator}state={payload.state_hash}"
    
    response.set_cookie(
        key="pending_id",
        value=str(payload.state_hash),
        httponly=True,
        samesite="lax",
        max_age=600  # 10 minutes
    )

    return {
        "redirect_url": redirect_link,
        "pending_id": payload.state_hash
    }
