from sqlalchemy.orm import Session
from sqlalchemy import update

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
