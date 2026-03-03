from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import PlanModel, Model
from utils.types import ModelType
from typing import Optional


async def get_default_model_for_plan(
    db: AsyncSession, plan_id: str, model_type: Optional[ModelType] = None
):
    """
    Dynamically resolve the default model for a given plan and optional model type.

    Strategy:
      1. Look for a model in the plan that is marked is_default=True, is_active=True, 
         and matches model_type (if provided).
      2. If none found, fall back to the first active model in the plan matching the type.
      3. Returns the Model object, or None if no active model exists for the plan.
    """
    if not plan_id:
        return None

    # 1. Try to find the explicitly marked default model for this plan
    query = (
        select(Model)
        .join(PlanModel, PlanModel.model_id == Model.id)
        .where(
            (PlanModel.plan_id == plan_id)
            & (PlanModel.is_active == True)
            & (PlanModel.is_default == True)
            & (Model.is_active == True)
        )
    )

    if model_type:
        query = query.where(Model.model_type == model_type)

    result = await db.execute(query)
    default_model = result.scalars().first()

    if default_model:
        return default_model

    # 2. Fallback: first active model linked to this plan (filtered by type if provided)
    fallback_query = (
        select(Model)
        .join(PlanModel, PlanModel.model_id == Model.id)
        .where(
            (PlanModel.plan_id == plan_id)
            & (PlanModel.is_active == True)
            & (Model.is_active == True)
        )
    )

    if model_type:
        fallback_query = fallback_query.where(Model.model_type == model_type)

    fallback_query = fallback_query.order_by(Model.created_at).limit(1)

    result = await db.execute(fallback_query)
    return result.scalars().first()
