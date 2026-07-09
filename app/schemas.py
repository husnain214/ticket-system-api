from fastapi_users import schemas
import uuid

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.db.enums import (
    TicketPriority,
    TicketCategory,
    UserRole,
)


class UserRead(schemas.BaseUser[uuid.UUID]):
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class TicketCreate(BaseModel):
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority
