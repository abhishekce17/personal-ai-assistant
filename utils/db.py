from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import update, select

def unset_default_for_all(session: Session, model):
    """
    Set is_default = False for all rows where it is currently True.
    Caller must commit the session.
    """
    if not hasattr(model, 'is_default'):
        raise AttributeError(f"The model {model.__name__} does not have an 'is_default' column.")

    result = session.execute(
        update(model)
        .where(model.is_default == True)
        .values(is_default=False)
    )

    print(f"Updated {result.rowcount} rows in {model.__name__}")


def _toggle_activation_row(db : Session, Model, id: str, activate: bool):
    """
    Set is_active = True for the row with the given id.
    """
    if not id:
        raise HTTPException(status_code=400, detail="ID is required")
    
    if not Model:
        raise HTTPException(status_code=400, detail="Model is required")
    
    if not hasattr(Model, 'is_active'):
        raise AttributeError(f"The model {Model.__name__} does not have an 'is_active' column.")

    row = db.execute(
        select(Model).filter(Model.id == id)
    ).scalars().first()

    if not row:
        raise HTTPException(status_code=404, detail="Row not found")

    row.is_active = activate
    db.commit()
    return {"success": True, "message": f"{Model.__name__} {'activated' if activate else 'deactivated'} successfully"}

def activate_row(db : Session, Model, id: str):
    return _toggle_activation_row(db, Model, id, True)

def deactivate_row(db : Session, Model, id: str):
    return _toggle_activation_row(db, Model, id, False)