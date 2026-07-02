from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas import TicketCreate
from app.db.models import Ticket, TicketEvent, AgentTask, TicketEvent, Escalation
from app.db.enums import (
    EventType,
    TicketStatus,
    TicketCategory,
    TicketPriority,
    AgentTaskStatus,
    EscalationStatus,
    AgentType,
)
from app.db.create_db import get_async_session
from app.db.create_db import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from uuid import UUID
from fastapi import Depends
from app.agents.graph import agent_app
from datetime import datetime
import json
from app.lib.redis import redis_client

router = APIRouter(prefix="/tickets", tags=["tickets"])


async def run_agent_workflow(
    ticket_id: UUID,
    title: str,
    description: str,
    priority: TicketPriority,
):
    started_at = datetime.utcnow()

    agent_result = await agent_app.ainvoke(
        {
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
            "category": None,
            "priority": priority,
            "result": None,
            "status": TicketStatus.PENDING,
            "messages": [],
            "error": None,
        }
    )

    completed_at = datetime.utcnow()

    category_to_agent = {
        TicketCategory.BILLING: AgentType.BILLING_AGENT,
        TicketCategory.TECHNICAL: AgentType.TECH_AGENT,
        TicketCategory.GENERAL: AgentType.ESCALATION_AGENT,
    }
    agent_type = category_to_agent.get(
        agent_result["category"],
        AgentType.ESCALATION_AGENT,
    )

    final_status = agent_result["status"]
    is_resolved = final_status == TicketStatus.RESOLVED

    async with async_session_maker() as session:
        agent_task = AgentTask(
            ticket_id=ticket_id,
            agent_type=agent_type,
            status=AgentTaskStatus.COMPLETED if is_resolved else AgentTaskStatus.FAILED,
            result=agent_result["result"],
            started_at=started_at,
            completed_at=completed_at,
        )
        session.add(agent_task)

        await session.execute(
            update(Ticket)
            .where(Ticket.id == ticket_id)
            .values(
                status=final_status,
                resolved_at=completed_at if is_resolved else None,
            )
        )

        event_type = EventType.AGENT_RESOLVED if is_resolved else EventType.ESCALATED
        ticket_event = TicketEvent(
            ticket_id=ticket_id,
            event_type=event_type,
            message=f"Ticket {event_type.value} by {agent_type.value}",
        )
        session.add(ticket_event)

        if not is_resolved:
            escalation = Escalation(
                ticket_id=ticket_id,
                reason=agent_result["result"],
                escalated_by_agent=agent_type.value,
                status=EscalationStatus.OPEN,
            )
            session.add(escalation)

        await session.commit()

        await redis_client.publish(
            "ticket_updates",
            json.dumps(
                {
                    "ticket_id": str(ticket_id),
                    "status": final_status.value,
                    "category": agent_result["category"].value,
                    "result": agent_result["result"],
                    "agent_type": agent_type.value,
                }
            ),
        )


@router.post("/", status_code=202)
async def create_ticket(
    ticket_data: TicketCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    ticket = Ticket(**ticket_data.model_dump())
    session.add(ticket)

    await session.flush()

    ticket_event = TicketEvent(
        ticket_id=ticket.id,
        event_type=EventType.CREATED,
        message=f"Ticket created with {ticket.priority.value} priority",
    )

    session.add(ticket_event)

    await session.commit()
    await session.refresh(ticket)

    background_tasks.add_task(
        run_agent_workflow, ticket.id, ticket.title, ticket.description, ticket.priority
    )

    return ticket


@router.get("/")
async def get_tickets(
    status: TicketStatus | None = None,
    category: TicketCategory | None = None,
    session: AsyncSession = Depends(get_async_session),
):
    query = select(Ticket).order_by(desc(Ticket.created_at))

    if status:
        query = query.where(Ticket.status == status)
    if category:
        query = query.where(Ticket.category == category)

    result = await session.execute(query)
    tickets = result.scalars().all()

    return tickets


@router.get("/{id}")
async def fetch_ticket(
    id: UUID,
    session: AsyncSession = Depends(get_async_session),
):
    ticket = await session.get(Ticket, id)

    if ticket is None:
        raise HTTPException(404, "Ticket not found")
    return ticket


@router.patch("/{id}")
async def update_ticket_status(
    id: UUID,
    status: TicketStatus,
    session: AsyncSession = Depends(get_async_session),
):
    await session.execute(update(Ticket).where(Ticket.id == id).values(status=status))
    ticket = await session.get(Ticket, id)

    return ticket
