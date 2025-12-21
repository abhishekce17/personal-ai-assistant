# will complete the code in the 2nd PHASE
from fastapi import APIRouter, Depends, Query, Request, HTTPException, Header
from app.api.routes.user import authentication
import hmac
import hashlib
import os
import json

router = APIRouter()

async def verify_github_signature(
    request: Request,
    x_hub_signature_256: str = Header(None)
):
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not secret:
        print("WARNING: GITHUB_WEBHOOK_SECRET not set. Skipping signature verification.")
        return

    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing signature header")

    body = await request.body()
    
    # Calculate HMAC
    signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    return True

@router.get("/github", summary="Handle GitHub App Installation")
def github_app_installation(
    installation_id: str = Query(..., description="The GitHub App installation ID"),
    setup_action: str = Query(None, description="The action that triggered the setup"),
):
    """
    Handle the redirect from GitHub after App installation.
    Returns the installation_id as requested.
    """
    return {"installation_id": installation_id}


@router.post("/github-webhook", summary="Handle GitHub App Webhooks")
async def github_app_webhook(
    request: Request,
    verified: bool = Depends(verify_github_signature)
):
    """
    Handle incoming webhooks from GitHub App.
    """
    return {"status": "accepted", "payload_received": True}
