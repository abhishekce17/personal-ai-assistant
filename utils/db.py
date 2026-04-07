from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy import update, select

async def unset_default_for_all(session: AsyncSession, model, condition=None):
    """
    Set is_default = False for all rows where it is currently True.
    Caller must commit the session.
    """
    if not hasattr(model, 'is_default'):
        raise AttributeError(f"The model {model.__name__} does not have an 'is_default' column.")

    query = update(model).where(model.is_default == True)
    
    if condition is not None:
        query = query.where(condition)

    result = await session.execute(
        query.values(is_default=False)
    )

    print(f"Updated {result.rowcount} rows in {model.__name__}")


async def _toggle_activation_row(db : AsyncSession, Model, id: str, activate: bool):
    """
    Set is_active = True for the row with the given id.
    """
    if not id:
        raise HTTPException(status_code=400, detail="ID is required")
    
    if not Model:
        raise HTTPException(status_code=400, detail="Model is required")
    
    if not hasattr(Model, 'is_active'):
        raise AttributeError(f"The model {Model.__name__} does not have an 'is_active' column.")

    result = await db.execute(select(Model).filter(Model.id == id))
    row = result.scalars().first()

    if not row:
        raise HTTPException(status_code=404, detail="Row not found")

    row.is_active = activate
    await db.commit()
    return {"success": True, "data": None, "message": f"{Model.__name__} {'activated' if activate else 'deactivated'} successfully"}

async def activate_row(db : AsyncSession, Model, id: str):
    return await _toggle_activation_row(db, Model, id, True)

async def deactivate_row(db : AsyncSession, Model, id: str):
    return await _toggle_activation_row(db, Model, id, False)


async def list_with_count(db: AsyncSession, primary_model, count_model, count_fk_column, primary_pk_column, count_label: str = "user_count"):
    """
    Generic list with dynamic count using two separate queries (faster than JOIN).
    1. Fetches all rows from primary_model
    2. Runs a GROUP BY COUNT on count_model
    3. Merges counts in Python

    Args:
        primary_model: The main table (e.g., Model, Plan, Tool)
        count_model: The table to count from (e.g., User, FederatedIdentity)
        count_fk_column: The column in count_model to group by (e.g., User.default_model_id)
        primary_pk_column: The PK column in primary_model to match against (e.g., Model.id)
        count_label: The label for the count field in the response
    """
    from sqlalchemy import func

    # Query 1: Fetch all rows
    result = await db.execute(select(primary_model))
    rows = result.scalars().all()

    # Query 2: Get counts via GROUP BY (uses indexes, no JOIN)
    count_query = select(count_fk_column, func.count().label("cnt"))
    
    # Check if count_model has is_active
    from sqlalchemy.inspection import inspect
    mapper = inspect(count_model)
    if "is_active" in mapper.attrs:
        count_query = count_query.where(count_model.is_active == True)
        
    count_result = await db.execute(
        count_query.group_by(count_fk_column)
    )
    count_map = {str(row[0]).lower() if row[0] else "none": row[1] for row in count_result.all()}

    # Merge
    data = []
    for row in rows:
        row_dict = {c.name: getattr(row, c.name) for c in primary_model.__table__.columns}
        pk_val = getattr(row, primary_pk_column.key)
        row_dict[count_label] = count_map.get(str(pk_val).lower(), 0) if pk_val else 0
        data.append(row_dict)
    return data