from fastapi import APIRouter, HTTPException
from app.schemas import TicketCreate
from app.db.models import Ticket, TicketEvent
from app.db.enums import EventType, TicketStatus, TicketCategory
from app.db.create_db import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from uuid import UUID
from fastapi import Depends

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/", status_code=202)
async def create_ticket(
    ticketData: TicketCreate,
    session: AsyncSession = Depends(get_async_session),
):
    ticket = Ticket(**ticketData.model_dump())
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
