from fastapi import APIRouter, HTTPException, status, Depends
from db.models import Login, Register, User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
