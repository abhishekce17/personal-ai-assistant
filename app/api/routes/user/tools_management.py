from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Body, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_, select
from app.core.security import generate_github_jwt, get_current_user, verify_github_installation_ownership, encrypt_value, decrypt_value
from db.models import User, PendingState, Tool, FederatedIdentity
from pydantic import BaseModel
import hashlib
import time
import jwt
import httpx
import base64
import os
from datetime import datetime, timedelta, timezone
from utils.db import activate_row, deactivate_row

router = APIRouter()

class ToolLinkCallback(BaseModel):
    platform: str
    installation_id: int    
    code : str
    refresh_token: Optional[str] = None
    code_verifier: str 

@router.post("/tool_auth_callback", summary="Finalize Tool Link")
async def tool_auth_callback(
    request: Request,
    payload: ToolLinkCallback,
    user: User = Depends(get_current_user)
):
    """
    Verify the PKCE proof and link the installation to the user.
    """
    db: AsyncSession = request.state.db

    # 1. Retrieve the Pending State using the UUID
    result = await db.execute(select(PendingState).where(
        PendingState.user_id == str(user.id),  # Ensure it belongs to this user
        PendingState.platform == payload.platform.lower()
    ))
    pending_state = result.scalars().first()
    
    if not pending_state: # Check for None before accessing attributes
         raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired state. Please try connecting again."
        )

    expires_at_aware = pending_state.expires_at.replace(tzinfo=timezone.utc)
    if not pending_state.is_active or expires_at_aware < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired state. Please try connecting again."
        )

    # NOTE: Ensure this matches the Client's hashing method exactly (SHA256)
    verifier_bytes = payload.code_verifier.encode('utf-8')
    hashed_bytes = hashlib.sha256(verifier_bytes).digest()
    
    # If your client sent a Hex string, use hexdigest(). 
    # If Base64Url, use urlsafe_b64encode.
    # assuming standard Base64Url for PKCE:
    calculated_hash = base64.urlsafe_b64encode(hashed_bytes).decode('utf-8').rstrip('=')

    # Compare calculated hash with the one stored in DB
    if calculated_hash != pending_state.state_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security verification failed"
        )
    if payload.platform.lower() == "github":
        await verify_github_installation_ownership(payload.code, payload.installation_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform '{payload.platform}' is not supported for verification."
        )

    result = await db.execute(select(FederatedIdentity).where(
        FederatedIdentity.installation_id == str(payload.installation_id),
        FederatedIdentity.provider == payload.platform
    ))
    existing_link = result.scalars().first()
    
    if existing_link and existing_link.user_id != user.id:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This installation is already linked to another account."
        )
    
    if existing_link and existing_link.user_id == user.id:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This installation is already linked to your account."
        )

    # Create Link - ENCRYPT installation_id before saving
    encrypted_installation_id = encrypt_value(str(payload.installation_id))
    
    new_identity = FederatedIdentity(
        user_id=user.id,
        provider=payload.platform,
        provider_account_id=str(encrypted_installation_id), 
        installation_id=encrypted_installation_id,
        refresh_token=str( payload.refresh_token if payload.refresh_token else encrypted_installation_id)
    )
    db.add(new_identity)
    await db.delete(pending_state)

    # Increment user_count in Tools table
    result = await db.execute(select(Tool).where(func.lower(Tool.tool_provider) == payload.platform.lower()))
    tool_record = result.scalars().first()
    if tool_record:
        tool_record.user_count += 1
    
    await db.commit()

    return {"success": True, "data": None, "message": "Repository access linked successfully."}


@router.delete("/uninstall_app/{installation_id}")
async def uninstall_app(
    request: Request,
    installation_id: str, # Encrypted string
    user: User = Depends(get_current_user)
):
    db: AsyncSession = request.state.db

    # 1. Verify ownership locally - Exact Match
    result = await db.execute(select(FederatedIdentity).where(
        FederatedIdentity.installation_id == installation_id,
        FederatedIdentity.user_id == user.id
    ))
    identity_link = result.scalars().first()

    if not identity_link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to uninstall this app or it doesn't exist."
        )

    try:
        app_jwt = generate_github_jwt()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Could not generate App credentials")
    
    # Decrypt for GitHub API
    decrypted_id = decrypt_value(installation_id)

    # 3. Call GitHub API to delete the installation
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"https://api.github.com/app/installations/{decrypted_id}",
            headers={
                "Authorization": f"Bearer {app_jwt}", # <--- MUST BE JWT
                "Accept": "application/vnd.github+json"
            }
        )

        if response.status_code == 204:
            # 4. Cleanup: Remove the link from your database
            
            # Decrement user_count
            result = await db.execute(select(Tool).where(func.lower(Tool.tool_provider) == identity_link.provider.lower()))
            tool_record = result.scalars().first()
            if tool_record and tool_record.user_count > 0:
                 tool_record.user_count -= 1

            await db.delete(identity_link)
            await db.commit()
            return {"success": True, "data": None, "message": "App uninstalled successfully"}
        
        elif response.status_code == 404:
            # If not found on GitHub, remove from our DB as well to sync state
            
            # Decrement user_count
            result = await db.execute(select(Tool).where(func.lower(Tool.tool_provider) == identity_link.provider.lower()))
            tool_record = result.scalars().first()
            if tool_record and tool_record.user_count > 0:
                 tool_record.user_count -= 1

            await db.delete(identity_link)
            await db.commit()
            return {"success": True, "data": None, "message": "Installation already removed or not found"}
            
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"GitHub API Error: {response.text}"
            )


@router.patch("/activate-deactivate/{installation_id}", summary="Activate or Deactivate a tool by ID")
async def activate_deactivate_tool(
    installation_id: str, # Encrypted string
    is_active: bool,
    request: Request,
    user: User = Depends(get_current_user),
):
    db: AsyncSession = request.state.db

    # 1. Verify ownership locally - Exact Match
    result = await db.execute(select(FederatedIdentity).where(
        FederatedIdentity.installation_id == installation_id,
        FederatedIdentity.user_id == user.id
    ))
    identity_link = result.scalars().first()

    if not identity_link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this app or it doesn't exist."
        )

    if( is_active ):
        return await activate_row(db, FederatedIdentity, identity_link.id)
    elif (not is_active):
        return await deactivate_row(db, FederatedIdentity, identity_link.id)