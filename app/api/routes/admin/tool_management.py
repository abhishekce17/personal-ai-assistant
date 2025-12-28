import importlib
from dotenv import load_dotenv
from fastapi import HTTPException, Depends, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Plan, Tool, ToolCreate
from app.core.security import require_admin_role_ids
from fastapi import APIRouter
import os

from utils.db import activate_row, deactivate_row

load_dotenv()

MASTER_ADMIN_ID = os.getenv("MASTER_ADMIN_ID")

router = APIRouter()


@router.post("/create", summary="Create a new tool")
async def create_tool(
    tool_data: ToolCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    tool_name_lowercase = tool_data.name.lower().strip()

    result = await db.execute(select(Tool).where(Tool.tool_name == tool_name_lowercase))
    existing = result.scalars().first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Tool already exists")
    

    tool_module = importlib.import_module(f"app.Tools.{tool_name_lowercase}_tools")
    if tool_module and hasattr(tool_module, "make_tools"):
        tool = Tool(
            tool_name=tool_name_lowercase,
            tool_description=tool_data.description,
            tool_provider=tool_data.provider,
            tool_image=tool_data.image,
        )
        db.add(tool)
        await db.commit()
        await db.refresh(tool)
        return {"message": "Tool created", "tool": {"id": tool.id, "name": tool.tool_name}}
    elif not tool_module:
        raise HTTPException(status_code=404, detail="Tool implementation not found")


@router.get("/list", summary="List all tools")
async def list_tools(
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    result = await db.execute(select(Tool))
    tools = result.scalars().all()
    return tools


@router.delete("/delete/{tool_id}", summary="Delete a tool")
async def delete_tool(
    tool_id: str,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalars().first()
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    await db.delete(tool)
    await db.commit()
    return {"message": "Tool deleted"}

@router.put("/update/{tool_id}", summary="Update an existing tool")
async def update_tool(
    tool_id: str,
    tool_data: ToolCreate,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalars().first()
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    if tool_data.name:
        tool.tool_name = tool_data.name

    if tool_data.description:
        tool.tool_description = tool_data.description

    if tool_data.provider:
        tool.tool_provider = tool_data.provider

    if tool_data.image:
        tool.tool_image = tool_data.image

    try:
        await db.commit()
        await db.refresh(tool)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Tool name already exists")

    return {
        "message": "Tool updated",
        "tool": {
            "id": tool.id,
            "name": tool.tool_name,
            "provider": tool.tool_provider,
            "description": tool.tool_description,
            "image": tool.tool_image,
        },
    }

@router.patch("/activate-deactivate/{tool_id}", summary="Activate or Deactivate a tool by ID")
async def activate_deactivate_tool(
    tool_id: str,
    is_active: bool,
    request: Request,
    admin=Depends(require_admin_role_ids(MASTER_ADMIN_ID)),
):
    db: AsyncSession = request.state.db

    if( is_active ):
        return await activate_row(db, Tool, tool_id)
    elif (not is_active):
        return await deactivate_row(db, Tool, tool_id)
