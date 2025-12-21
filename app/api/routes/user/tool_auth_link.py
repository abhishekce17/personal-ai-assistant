from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Body, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.core.security import get_current_user, verify_github_installation_ownership
from db.models import User, PendingState, Tool, FederatedIdentity
from pydantic import BaseModel
import hashlib
import base64
import os
from datetime import datetime, timedelta, timezone

router = APIRouter()


class AuthLinkRequest(BaseModel):
    platform: str
    state_hash: str | None = None

@router.post("/tool_auth_link", summary="Generate Tool Auth Link")
def tool_auth_link(
    request: Request,
    response: Response,
    payload: AuthLinkRequest,
    user: User = Depends(get_current_user)
):
    """
    Generate a redirect link for Tool OAuth and store pending state.
    """
    db: Session = request.state.db

    # Check if the platform exists and is active in the Tool table
    tool = db.query(Tool).filter(func.lower(Tool.tool_provider) == payload.platform.lower(), Tool.is_active == True).first()
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Platform '{payload.platform}' is not supported or inactive."
        )

    env_key = f"{payload.platform.upper()}_TOOL_INSTALLATION_LINK"
    base_link = os.getenv(env_key)

    if not base_link:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Redirect link for {payload.platform} is not configured."
        )

    # Check for existing valid installation
    existing_identity = db.query(FederatedIdentity).filter(
        FederatedIdentity.user_id == user.id,
        func.lower(FederatedIdentity.provider) == payload.platform.lower(),
        FederatedIdentity.is_active == True,
        FederatedIdentity.installation_id != None,
        FederatedIdentity.refresh_token != None,
        or_(
            FederatedIdentity.expires_at == None,
            FederatedIdentity.expires_at > datetime.now(timezone.utc)
        )
    ).first()

    if existing_identity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User is already connected to {payload.platform}."
        )
    
    # Check for existing pending state for this user and platform
    existing_pending = db.query(PendingState).filter(
        PendingState.user_id == str(user.id),
        PendingState.platform == payload.platform
    ).first()

    if existing_pending:
        # Only update state hash if it doesn't match
        if existing_pending.state_hash != payload.state_hash:
            existing_pending.state_hash = payload.state_hash
            existing_pending.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            db.commit()
            db.refresh(existing_pending)
        pending_state = existing_pending
            
    else:
        # Create pending state
        pending_state = PendingState(
            user_id=str(user.id),
            state_hash=payload.state_hash,
            platform=payload.platform,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        db.add(pending_state)
        db.commit()
        db.refresh(pending_state)
    
    

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
