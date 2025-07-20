# # 1. `POST /chat/new # Create new thread_id`
# # 2. `GET     /chat/{thread_id}       # Get messages in thread`
# # 3. `DELETE  /chat/{thread_id}       # Delete entire thread`
# # 4. `GET /chat/threads # List all user’s threads `


from fastapi import APIRouter, HTTPException, status, Depends
from db.models import Login, Register, User
from sqlalchemy.orm import Session

router = APIRouter()
