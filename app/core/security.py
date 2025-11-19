from fastapi import HTTPException, Header, Request, status, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from db.models import User, Admin
import bcrypt
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
        user = db.query(User).filter(User.id == id).first()
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
