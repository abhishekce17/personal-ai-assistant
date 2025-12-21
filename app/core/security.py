from fastapi import HTTPException, Header, Request, status, Depends
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from db.models import User, Admin
import httpx
import bcrypt
import time
import jwt
import base64
import hashlib
import os

load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")


def hash_password(plain_password: str) -> bytes:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode(), salt).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not bcrypt.checkpw(plain_password.encode(), hashed_password.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )


def create_jwt_token(email: str, id: str) -> str:
    payload = {
        "id": id,
        "email": email,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(
    request: Request,
    authorization: str = Header(None),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid or missing authorization token"
        )

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = verify_jwt_token(token)
        id = payload.get("id")
        if not id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        db: Session = request.state.db
        user = db.query(User).filter(User.id == id, User.is_active == True).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    

def extract_token(request: Request) -> str | None:
    # Header
    header = request.headers.get("Authorization")
    if header and header.startswith("Bearer "):
        return header.removeprefix("Bearer ").strip()
    
    # Cookie
    cookie = request.cookies.get("access_token")
    if cookie:
        return cookie.strip()

    return None


def get_current_admin(request: Request) -> Admin:
    token = extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    payload = verify_jwt_token(token)
    admin_id = payload.get("id")
    if not admin_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    db: Session = request.state.db
    admin = db.query(Admin).filter(Admin.id == admin_id).first()

    if not admin or not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin not found")

    return admin


def require_admin_role_ids(*allowed_ids: str):
    def _checker(admin: Admin = Depends(get_current_admin)):
        if admin.role_id not in allowed_ids:
            raise HTTPException(status_code=403, detail="Unauthorized admin")
        return admin
    return _checker


async def verify_github_installation_ownership(auth_code: str, installation_id: int) -> None:
    """
    Exchanges the OAuth code for a user token and verifies if that user
    actually owns the specified installation_id.
    Raises HTTPException if verification fails.
    """
    async with httpx.AsyncClient() as client:
        # 1. Exchange Code for Access Token
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": os.getenv("GITHUB_APP_CLIENT_ID"),
                "client_secret": os.getenv("GITHUB_APP_CLIENT_SECRET"),
                "code": auth_code,
            }
        )
        
        token_data = token_resp.json()
        
        if "error" in token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"GitHub Auth Error: {token_data.get('error_description', 'Invalid Code')}"
            )
            
        user_access_token = token_data.get("access_token")
        if not user_access_token:
             raise HTTPException(status_code=400, detail="Failed to retrieve access token from GitHub.")

        # 2. Verify Ownership via API
        # CORRECT METHOD: Fetch all installations this user manages
        verification_resp = await client.get(
            "https://api.github.com/user/installations",
            headers={
                "Authorization": f"Bearer {user_access_token}",
                "Accept": "application/vnd.github+json"
            },
            params={"per_page": 100} # Fetch up to 100 to ensure we see them all
        )

        if verification_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user installations from GitHub."
            )

        # 3. Strict Check (Filter the list)
        user_installations = verification_resp.json().get("installations", [])
        
        # Check if the requested installation_id exists in the user's authorized list
        # We cast both to int to ensure type safety
        is_owner = any(inst["id"] == int(installation_id) for inst in user_installations)

        if not is_owner:
            # 403 Forbidden means the user does NOT own this installation.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Security Alert: You do not have permission to link this installation."
            )     


def generate_github_jwt():
    """
    Generates a JWT for the GitHub App to authenticate as 'The App'.
    """
    private_key_content = os.getenv("GITHUB_APP_PRIVATE_KEY")
    
    if not private_key_content:
        raise ValueError("Environment variable 'GITHUB_APP_PRIVATE_KEY' is missing.")

    formatted_key = private_key_content.replace('\\n', '\n')

    if "-----BEGIN RSA PRIVATE KEY-----" not in formatted_key:
        raise ValueError(
            "Invalid Private Key format. The key must include the "
            "'-----BEGIN RSA PRIVATE KEY-----' header and footer."
        )

    payload = {
        "iat": int(time.time()),       
        "exp": int(time.time()) + 600, 
        "iss": os.getenv("GITHUB_APP_ID")
    }
    
    return jwt.encode(payload, formatted_key, algorithm="RS256")

async def get_github_installation_token(installation_id: str):
    """
    Generates an installation access token for the App.
    MUST be async to avoid blocking the server.
    """
    
    jwt_token = generate_github_jwt()
 
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers=headers
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to get token: {response.text}")

        return response.json()["token"]


def _get_encryption_key() -> bytes:
    """
    Retrieve or derive the encryption key.
    If ENCRYPTION_KEY is not set, derive one from JWT_SECRET_KEY.
    """
    if not JWT_SECRET_KEY:
        raise ValueError("No ENCRYPTION_KEY or JWT_SECRET_KEY found.")
        
    # Fernet requires a 32-byte url-safe base64-encoded key
    return base64.urlsafe_b64encode(hashlib.sha256(JWT_SECRET_KEY.encode()).digest())

def encrypt_value(value: str) -> str:
    """
    Encrypts a string value using Fernet (symmetric encryption).
    """
    if not value:
        return value
    f = Fernet(_get_encryption_key())
    return f.encrypt(value.encode()).decode()

def decrypt_value(token: str) -> str:
    """
    Decrypts a Fernet token back to the original string.
    """
    if not token:
        return token
    try:
        f = Fernet(_get_encryption_key())
        return f.decrypt(token.encode()).decode()
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid User")