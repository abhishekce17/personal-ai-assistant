from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Integer, String, Boolean
from datetime import datetime, timezone
import uuid


# pydentic models for type safety
class Login(BaseModel):
    email: EmailStr
    password: str


class Register(BaseModel):
    email: EmailStr
    password: str
    name: str
    terms_and_condition: bool


Base = declarative_base()


class BaseMixin:
    id = Column(
        String,
        primary_key=True,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    is_active = Column(Boolean, default=True)


# Users Table
class User(BaseMixin, Base):
    __tablename__ = "users"

    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    default_model_id = Column(String, ForeignKey("models.id"), index=True)
    current_plan_id = Column(String, ForeignKey("plans.id"), index=True)
    terms_and_condition = Column(Boolean, default=True)
    avatar = Column(String)

    plan = relationship("Plan", back_populates="users")
    default_model = relationship("Model")
    plan_history = relationship("UserPlanHistory", back_populates="user")
    chat_sessions = relationship("ChatSessionEmbedding", back_populates="user")



# Models Table
class Model(BaseMixin, Base):
    __tablename__ = "models"

    model_name = Column(String, nullable=False)
    model_description = Column(Text)
    model_provider = Column(String)
    tool_support = Column(Boolean, default=True)
    user_count = Column(Integer, default=0)


# Plans Table
class Plan(BaseMixin, Base):
    __tablename__ = "plans"

    name = Column(String, nullable=False, unique=True)
    slug = Column(String, unique=True, nullable=False)
    subscription_count = Column(Integer, default=0)
    price = Column(Integer)  # in cents
    description = Column(Text)

    users = relationship("User", back_populates="plan")
    tools = relationship("PlanTool", back_populates="plan")
    models = relationship("PlanModel", back_populates="plan")
    features = relationship("Feature", back_populates="plan")


# Tools Table
class Tool(BaseMixin, Base):
    __tablename__ = "tools"

    tool_name = Column(String, nullable=False, unique=True)
    tool_description = Column(Text)
    tool_provider = Column(String)
    user_count = Column(Integer, default=0)

    plans = relationship("PlanTool", back_populates="tool")


# Plan–Tool mapping (Many-to-Many)
class PlanTool(BaseMixin, Base):
    __tablename__ = "plan_tools"

    plan_id = Column(String, ForeignKey("plans.id"), index=True)
    tool_id = Column(String, ForeignKey("tools.id"), index=True)

    plan = relationship("Plan", back_populates="tools")
    tool = relationship("Tool", back_populates="plans")

    __table_args__ = (UniqueConstraint('plan_id', 'tool_id', name='_plan_tool_uc'),)


# Plan–Model mapping (Many-to-Many)
class PlanModel(BaseMixin, Base):
    __tablename__ = "plan_models"

    plan_id = Column(String, ForeignKey("plans.id"), index=True)
    model_id = Column(String, ForeignKey("models.id"), index=True)

    plan = relationship("Plan", back_populates="models")
    model = relationship("Model")

    __table_args__ = (UniqueConstraint('plan_id', 'model_id', name='_plan_model_uc'),)


# Features per plan (Key-value)
class Feature(BaseMixin, Base):
    __tablename__ = "features"

    plan_id = Column(String, ForeignKey("plans.id"), index=True)
    feature_key = Column(String, nullable=False)
    feature_value = Column(String)

    plan = relationship("Plan", back_populates="features")

    __table_args__ = (UniqueConstraint('plan_id', 'feature_key', name='_plan_feature_uc'),)


# Optional: Plan history tracking
class UserPlanHistory(BaseMixin, Base):
    __tablename__ = "user_plan_history"

    user_id = Column(String, ForeignKey("users.id"), index=True)
    plan_id = Column(String, ForeignKey("plans.id"), index=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="plan_history")
    plan = relationship("Plan")

class BillingInformation(BaseMixin, Base):
    __tablename__ = "billing_information"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(String, ForeignKey("plans.id"), nullable=False, index=True)

    billing_cycle = Column(String, nullable=False)          # 'monthly', 'yearly'
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, default="USD")

    payment_method = Column(String, nullable=False)         # 'card', 'UPI', etc.
    payment_status = Column(String, default="pending")      # 'paid', 'failed', etc.
    transaction_id = Column(String, unique=True)            # from payment gateway
    invoice_url = Column(String)

    billing_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    next_billing_date = Column(DateTime, nullable=True)
    is_recurring = Column(Boolean, default=True)

    # Relationships
    user = relationship("User")
    plan = relationship("Plan")

class ChatSessionEmbedding(BaseMixin, Base):
    __tablename__ = "chat_session_embeddings"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    thread_id = Column(String, unique=True, index=True, nullable=False)

    content = Column(Text, nullable=False)     # full chat as JSON or text
    summary = Column(Text, nullable=True)      # optional summarized version

    embedding_id = Column(String, unique=True, index=True, nullable=False)  # links to vector row in Pinecone
    source = Column(String, default="chat")     # for categorization or doc ingestion

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="chat_sessions")