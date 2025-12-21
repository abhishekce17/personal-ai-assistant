from fastapi import HTTPException, Header, Request, status, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from db.models import User, Admin
import httpx
import bcrypt
import time
import jwt
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
                "client_id": os.getenv("GITHUB_CLIENT_ID"),
                "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
                "code": auth_code,
            }
        )
        
        token_data = token_resp.json()
        
        if "error" in token_data:
            # This usually happens if the code is expired or invalid
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"GitHub Auth Error: {token_data.get('error_description', 'Invalid Code')}"
            )
            
        user_access_token = token_data.get("access_token")
        if not user_access_token:
             raise HTTPException(status_code=400, detail="Failed to retrieve access token from GitHub.")

        # 2. Verify Ownership via API
        # We ask GitHub: "Does the user owning this token have access to installation X?"
        verification_resp = await client.get(
            f"https://api.github.com/user/installations/{installation_id}",
            headers={
                "Authorization": f"Bearer {user_access_token}",
                "Accept": "application/vnd.github+json"
            }
        )

        # 3. Strict Check
        if verification_resp.status_code != 200:
            # 403 Forbidden or 404 Not Found means the user does NOT own this installation.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Security Alert: You do not have permission to link this installation."
            )
        

async def get_github_installation_token(installation_id: str):
    """
    Generates an installation access token for the App.
    MUST be async to avoid blocking the server.
    """
    # 1. Create a JWT for the App Authentication
    pem_file = os.getenv("GITHUB_APP_PRIVATE_KEY") 
    
    payload = {
        "iat": int(time.time()),       # Issued at now
        "exp": int(time.time()) + 600, # Expires in 10 mins
        "iss": os.getenv("GITHUB_APP_ID")
    }
    
    jwt_token = jwt.encode(payload, pem_file, algorithm="RS256")
 
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