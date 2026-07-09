from typing import TypedDict, Annotated, Sequence, Optional
from uuid import UUID
from app.db.enums import TicketCategory, TicketPriority, TicketStatus
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    ticket_id: UUID
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    result: Optional[str]
    status: TicketStatus
    messages: Annotated[Sequence[BaseMessage], add_messages]
    error: Optional[str]
