import uuid
from datetime import datetime
from uuid import UUID

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.db.enums import (
    AgentTaskStatus,
    AgentType,
    EscalationStatus,
    EventType,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    UserRole,
)


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.OPERATOR,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    api_tokens: Mapped[list["ApiToken"]] = relationship(
        back_populates="created_by_user"
    )

    assigned_escalations: Mapped[list["Escalation"]] = relationship(
        back_populates="assigned_to_user"
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[TicketCategory | None] = mapped_column(
        Enum(TicketCategory, name="ticket_category"),
        nullable=True,
    )

    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status"),
        default=TicketStatus.PENDING,
        nullable=False,
    )

    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority"),
        default=TicketPriority.MEDIUM,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    agent_tasks: Mapped[list["AgentTask"]] = relationship(back_populates="ticket")

    events: Mapped[list["TicketEvent"]] = relationship(back_populates="ticket")

    escalation: Mapped["Escalation | None"] = relationship(
        back_populates="ticket",
        uselist=False,
    )


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    ticket_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tickets.id"),
        nullable=False,
    )

    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type"),
        default=EventType.CREATED,
        nullable=False,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    ticket: Mapped["Ticket"] = relationship(back_populates="events")


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    ticket_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tickets.id"),
        unique=True,
        nullable=False,
    )

    assigned_to: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    escalated_by_agent: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[EscalationStatus] = mapped_column(
        Enum(EscalationStatus, name="escalation_status"),
        default=EscalationStatus.OPEN,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    ticket: Mapped["Ticket"] = relationship(back_populates="escalation")

    assigned_to_user: Mapped["User | None"] = relationship(
        back_populates="assigned_escalations"
    )


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    ticket_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tickets.id"),
        nullable=False,
    )

    agent_type: Mapped[AgentType] = mapped_column(
        Enum(AgentType, name="agent_type"),
        nullable=False,
    )

    status: Mapped[AgentTaskStatus] = mapped_column(
        Enum(AgentTaskStatus, name="agent_task_status"),
        default=AgentTaskStatus.PENDING,
        nullable=False,
    )

    result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    ticket: Mapped["Ticket"] = relationship(back_populates="agent_tasks")


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    created_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    label: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_by_user: Mapped["User"] = relationship(back_populates="api_tokens")
