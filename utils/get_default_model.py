from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import PlanModel, Model


async def get_default_model_for_plan(db: AsyncSession, plan_id: str):
    """
    Dynamically resolve the default model for a given plan.

    Strategy:
      1. Look for a model in the plan that is marked is_default=True and is_active=True.
      2. If none found, fall back to the first active model in the plan.
      3. Returns the Model object, or None if no active model exists for the plan.
    """
    if not plan_id:
        return None

    # 1. Try to find the explicitly marked default model for this plan
    result = await db.execute(
        select(Model)
        .join(PlanModel, PlanModel.model_id == Model.id)
        .where(
            (PlanModel.plan_id == plan_id)
            & (PlanModel.is_active == True)
            & (PlanModel.is_default == True)
            & (Model.is_active == True)
        )
    )
    default_model = result.scalars().first()

    if default_model:
        return default_model

    # 2. Fallback: first active model linked to this plan
    result = await db.execute(
        select(Model)
        .join(PlanModel, PlanModel.model_id == Model.id)
        .where(
            (PlanModel.plan_id == plan_id)
            & (PlanModel.is_active == True)
            & (Model.is_active == True)
        )
        .order_by(Model.created_at)
        .limit(1)
    )
    return result.scalars().first()
