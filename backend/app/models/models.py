import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, Float,
    Text, DateTime, ForeignKey, JSON, Enum
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum


class Base(DeclarativeBase):
    pass


class ContractStatus(str, enum.Enum):
    none = "none"
    proposed = "proposed"
    accepted = "accepted"
    amended = "amended"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class SilenceState(str, enum.Enum):
    confident = "confident"
    confused = "confused"
    distressed = "distressed"


class TrustEventType(str, enum.Enum):
    debit = "debit"
    credit = "credit"


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False, index=True)
    style_profile = Column(JSON, nullable=True)
    contract = Column(JSON, nullable=True)
    contract_status = Column(String, default="none")
    is_resolved = Column(Boolean, default=False)
    resolution_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    action_traces = relationship("ActionTrace", back_populates="session", cascade="all, delete-orphan")
    trust_events = relationship("TrustEvent", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    silence_state = Column(String, nullable=True)  # F02
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")


class ActionTrace(Base):
    __tablename__ = "action_traces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False, index=True)
    tool_name = Column(String, nullable=False)
    tool_input = Column(JSON, nullable=True)
    tool_result = Column(JSON, nullable=True)
    plain_summary = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="action_traces")


class TrustEvent(Base):
    __tablename__ = "trust_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)  # "debit" | "credit"
    amount = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)
    credit_code = Column(String, nullable=True)
    credit_value_inr = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="trust_events")


class CollectivePattern(Base):
    __tablename__ = "collective_patterns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_embedding_id = Column(String, nullable=True)  # Pinecone vector ID
    query_summary = Column(Text, nullable=False)
    resolution_summary = Column(Text, nullable=False)
    next_likely_issue = Column(Text, nullable=True)
    occurrence_count = Column(Integer, default=1)
    success_rate = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.user, server_default="user")
    trust_balance = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
