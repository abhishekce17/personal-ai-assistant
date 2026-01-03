from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Text,
    UniqueConstraint,
    Enum,
    Index
)
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from typing import Optional
import uuid

from utils.types import ArtifactFormat, IdentityScope


# pydentic models for type safety
class Login(BaseModel):
    email: EmailStr
    password: str


class AdminRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role_id: str  # from admin_roles table


class Register(BaseModel):
    email: EmailStr
    password: str
    name: str
    terms_and_condition: bool


class PlanCreate(BaseModel):
    name: str
    price: int
    description: Optional[str]
    is_default: Optional[bool]

class ToolCreate(BaseModel):
    name: str
    description: Optional[str]
    provider: Optional[str]
    image: Optional[str]

class StaticdataCreate(BaseModel):
    reference_key: str
    artifact_payload: str
    media_type: str
    revision_id: Optional[int]
    description: Optional[str]


class StaticdataUpdate(BaseModel):
    reference_key: Optional[str]
    artifact_payload: Optional[str]
    media_type: Optional[str]
    revision_id: Optional[int]
    description: Optional[str]

class PlanUpdate(BaseModel):
    name: Optional[str]
    slug: Optional[str]
    price: Optional[int]
    description: Optional[str]
    is_default: Optional[bool]


class ModelCreate(BaseModel):
    model_name: str
    model_description: str
    model_provider: str
    tool_support: Optional[bool]
    model_image: Optional[str]
    is_default: Optional[bool]

class ModelUpdate(BaseModel):
    model_name: Optional[str] = None
    model_description: Optional[str] = None
    model_provider: Optional[str] = None
    model_image: Optional[str] = None
    tool_support: Optional[bool] = None
    is_default: Optional[bool] = None


class PlanModelCreate(BaseModel):
    plan_id: str
    model_id: str


class PlanToolCreate(BaseModel):
    plan_id: str
    tool_id: str


class FeatureCreate(BaseModel):
    plan_id: str
    feature_key: str
    feature_value: Optional[str]



class FeatureFlagCreate(BaseModel):
    reference_key: str
    description: Optional[str]
    revision_id: Optional[int]



class FeatureFlagRetrieve(BaseModel):
    reference_key: str
    revision_id: int


class UserChatSessionRetrieve(BaseModel):
    id: str
    thread_id: str
    topic: Optional[str]
    updated_at: datetime



# Database related models
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


# Admin Table
class Admin(BaseMixin, Base):
    __tablename__ = "admins"

    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role_id = Column(String, ForeignKey("admin_roles.id"), index=True)
    avatar = Column(String, nullable=True)
    role = relationship("AdminRole", backref="admins")


class AdminRole(BaseMixin, Base):
    __tablename__ = "admin_roles"

    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)


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
    chat_sessions = relationship("ChatSession", back_populates="user")
    federated_identities = relationship("FederatedIdentity", back_populates="user", cascade="all, delete-orphan")

class FederatedIdentity(BaseMixin, Base):
    __tablename__ = "federated_identities"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)         
    provider_account_id = Column(String(255), nullable=False) 
    remark = Column(Enum(IdentityScope,name="identity_scope_enum"), default=IdentityScope.PERSONAL)
    installation_id  = Column(Text, nullable=True, unique=True)
    access_token = Column(Text, nullable=True, unique=True)
    refresh_token = Column(Text, nullable=True, unique=True)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="federated_identities")

# Models Table
class Model(BaseMixin, Base):
    __tablename__ = "models"

    model_name = Column(String, nullable=False)
    model_description = Column(Text)
    model_provider = Column(String)
    tool_support = Column(Boolean, default=True)
    user_count = Column(Integer, default=0)
    model_image = Column(String, nullable=True, default="")
    context_window = Column(Integer, nullable=True) # Max tokens capability
    is_default = Column(Boolean, default=False)


# Plans Table
class Plan(BaseMixin, Base):
    __tablename__ = "plans"

    name = Column(String, nullable=False, unique=True)
    slug = Column(String, unique=True, nullable=False)
    subscription_count = Column(Integer, default=0)
    price = Column(Integer)  # in cents
    description = Column(Text)
    is_default = Column(Boolean, default=False)

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
    tool_image = Column(String, nullable=True, default="")

    plans = relationship("PlanTool", back_populates="tool")


# Plan–Tool mapping (Many-to-Many)
class PlanTool(BaseMixin, Base):
    __tablename__ = "plan_tools"

    plan_id = Column(String, ForeignKey("plans.id"), index=True)
    tool_id = Column(String, ForeignKey("tools.id"), index=True)

    plan = relationship("Plan", back_populates="tools")
    tool = relationship("Tool", back_populates="plans")

    __table_args__ = (UniqueConstraint("plan_id", "tool_id", name="_plan_tool_uc"),)


# Plan–Model mapping (Many-to-Many)
class PlanModel(BaseMixin, Base):
    __tablename__ = "plan_models"

    plan_id = Column(String, ForeignKey("plans.id"), index=True)
    model_id = Column(String, ForeignKey("models.id"), index=True)

    plan = relationship("Plan", back_populates="models")
    model = relationship("Model")

    __table_args__ = (UniqueConstraint("plan_id", "model_id", name="_plan_model_uc"),)


# Features per plan (Key-value)
class Feature(BaseMixin, Base):
    __tablename__ = "features"

    plan_id = Column(String, ForeignKey("plans.id"), index=True)
    feature_key = Column(String, nullable=False)
    feature_value = Column(String)

    plan = relationship("Plan", back_populates="features")

    __table_args__ = (
        UniqueConstraint("plan_id", "feature_key", name="_plan_feature_uc"),
    )


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

    billing_cycle = Column(String, nullable=False)  # 'monthly', 'yearly'
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, default="USD")

    payment_method = Column(String, nullable=False)  # 'card', 'UPI', etc.
    payment_status = Column(String, default="pending")  # 'paid', 'failed', etc.
    transaction_id = Column(String, unique=True)  # from payment gateway
    invoice_url = Column(String)

    billing_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    next_billing_date = Column(DateTime, nullable=True)
    is_recurring = Column(Boolean, default=True)

    # Relationships
    user = relationship("User")
    plan = relationship("Plan")


class ChatSession(BaseMixin, Base):
    __tablename__ = "chat_sessions"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    thread_id = Column(String, unique=True, index=True, nullable=False)
    
    topic = Column(String(255), nullable=True)
    
    interactions = relationship(
        "ChatInteraction", 
        back_populates="session", 
        cascade="all, delete-orphan",
        order_by="ChatInteraction.created_at"  # <--- RECOMMENDED ADDITION
    )
    user = relationship("User", back_populates="chat_sessions")

class ChatInteraction(BaseMixin, Base):
    __tablename__ = "chat_interactions"

    thread_id = Column(String, ForeignKey("chat_sessions.thread_id"), nullable=False, index=True)
    content = Column(Text, nullable=False) 

    session = relationship("ChatSession", back_populates="interactions")
    __table_args__ = (
        Index('idx_thread_interaction_time', 'thread_id', 'created_at'),
    )

# class ChatSessionEmbedding(BaseMixin, Base):
#     __tablename__ = "chat_session_embeddings"

#     user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
#     thread_id = Column(String, unique=True, index=True, nullable=False)

#     content = Column(Text, nullable=False)  # full chat as JSON or text
#     topic = Column(String(255), nullable=True)  # short conversation title

#     embedding_id = Column(
#         String, unique=True, index=True, nullable=True
#     )  # links to vector row in Pinecone
#     source = Column(String, default="chat")  # for categorization or doc ingestion

#     user = relationship("User", back_populates="chat_sessions")


class SystemArtifact(BaseMixin, Base):
    __tablename__ = "system_artifacts"

    reference_key = Column(String(100), index=True, nullable=False)
    revision_id = Column(Integer, default=1, nullable=False)
    artifact_payload = Column(Text, nullable=False)
    # Tells the frontend how to parse it: 'text/markdown', 'application/json', 'text/html'
    media_type = Column(
        Enum(ArtifactFormat, name="artifact_format_enum"), 
        default=ArtifactFormat.TEXT, 
        nullable=False
    )
    description = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint('reference_key', 'revision_id', name='uq_artifact_revision'),
    )


class FeatureFlag(BaseMixin, Base):
    __tablename__ = "feature_flag"

    reference_key = Column(String(100), index=True, nullable=False)
    revision_id = Column(Integer, default=1, nullable=False)
    description = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint('reference_key', 'revision_id', name='feature_artifact_revision'),
    )



class PendingState(BaseMixin, Base):
    __tablename__ = "pending_state"

    user_id = Column(String, index=True, nullable=False)
    platform = Column(String, nullable=False)
    state_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'platform', name='uix_user_platform'),)
