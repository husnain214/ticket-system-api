import uuid
from datetime import datetime
from app.db.enums import (
    UserRole,
    TicketStatus,
    TicketPriority,
    EscalationStatus,
    EventType,
    AgentTaskStatus,
    AgentType,
    TicketCategory,
)

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from fastapi_users.db import SQLAlchemyBaseUserTableUUID


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    role = Column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.OPERATOR
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    api_tokens = relationship("ApiToken", back_populates="created_by_user")
    assigned_escalations = relationship("Escalation", back_populates="assigned_to_user")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(TicketCategory, name="ticket_category"), nullable=False)
    status = Column(
        Enum(TicketStatus, name="ticket_status"),
        default=TicketStatus.PENDING,
        nullable=False,
    )
    priority = Column(
        Enum(TicketPriority, name="ticket_priority"),
        default=TicketPriority.MEDIUM,
        nullable=False,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    resolved_at = Column(DateTime, nullable=True)

    agent_tasks = relationship("AgentTask", back_populates="ticket")
    events = relationship("TicketEvent", back_populates="ticket")
    escalation = relationship("Escalation", back_populates="ticket", uselist=False)


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    event_type = Column(
        Enum(EventType, name="event_type"), default=EventType.CREATED, nullable=False
    )
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="events")


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(
        UUID(as_uuid=True), ForeignKey("tickets.id"), unique=True, nullable=False
    )
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    escalated_by_agent = Column(String)
    reason = Column(Text)
    status = Column(
        Enum(EscalationStatus, name="escalation_status"),
        default=EscalationStatus.OPEN,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    ticket = relationship("Ticket", back_populates="escalation")
    assigned_to_user = relationship("User", back_populates="assigned_escalations")


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    agent_type = Column(Enum(AgentType, name="agent_type"), nullable=False)
    status = Column(
        Enum(AgentTaskStatus, name="agent_task_status"),
        default=AgentTaskStatus.PENDING,
        nullable=False,
    )
    result = Column(Text)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    ticket = relationship("Ticket", back_populates="agent_tasks")


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, nullable=False, unique=True)
    label = Column(String)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    created_by_user = relationship("User", back_populates="api_tokens")
