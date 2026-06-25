# from pydantic import BaseModel
from fastapi_users import schemas
import uuid

from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.enums import (
    TicketStatus,
    TicketPriority,
    TicketCategory,
    EventType,
    AgentTaskStatus,
    AgentType,
)


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


# class AgentTaskResponse(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     id: UUID
#     ticket_id: UUID
#     agent_type: AgentType
#     status: AgentTaskStatus
#     result: Optional[str] = None
#     started_at: Optional[datetime] = None
#     completed_at: Optional[datetime] = None


# class TicketEventResponse(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     id: UUID
#     ticket_id: UUID
#     event_type: EventType
#     message: Optional[str] = None
#     created_at: datetime


# class EscalationResponse(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     id: UUID
#     ticket_id: UUID
#     assigned_to: Optional[UUID] = None
#     escalated_by_agent: Optional[str] = None
#     reason: Optional[str] = None
#     status: str
#     created_at: datetime
#     resolved_at: Optional[datetime] = None


class TicketCreate(BaseModel):
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority


# class TicketResponse(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     id: UUID
#     title: str
#     description: str
#     category: TicketCategory
#     status: TicketStatus
#     priority: TicketPriority
#     created_at: datetime
#     updated_at: datetime
#     resolved_at: Optional[datetime] = None


# class TicketListResponse(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     id: UUID
#     title: str
#     category: TicketCategory
#     status: TicketStatus
#     priority: TicketPriority
#     created_at: datetime


# class TicketDetailResponse(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     id: UUID
#     title: str
#     description: str
#     category: TicketCategory
#     status: TicketStatus
#     priority: TicketPriority
#     created_at: datetime
#     updated_at: datetime
#     resolved_at: Optional[datetime] = None
#     events: list[TicketEventResponse] = []
#     agent_tasks: list[AgentTaskResponse] = []
#     escalation: Optional[EscalationResponse] = None
