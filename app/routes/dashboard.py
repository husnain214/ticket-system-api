from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.lib.redis import redis_client
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from app.db.create_db import get_async_session
from sqlalchemy import select
from app.db.models import Ticket, Escalation
from app.db.enums import TicketStatus

router = APIRouter(tags=["dashboard"])


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await websocket.accept()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("ticket_updates")

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            await websocket.send_text(message["data"])

    except WebSocketDisconnect:
        await pubsub.unsubscribe("ticket_updates")
        await pubsub.aclose()


@router.get("/analytics")
async def fetch_analytics(
    session: AsyncSession = Depends(get_async_session),
):
    total_tickets = await session.scalar(select(func.count("*")).select_from(Ticket))
    pending_tickets = await session.scalar(
        select(func.count("*"))
        .select_from(Ticket)
        .where(Ticket.status == TicketStatus.PENDING)
    )
    resolved_tickets = await session.scalar(
        select(func.count("*"))
        .select_from(Ticket)
        .where(Ticket.status == TicketStatus.RESOLVED)
    )
    escalations = await session.scalar(select(func.count("*")).select_from(Escalation))
    resolution_rate = int(resolved_tickets / total_tickets * 100)

    analytics = {
        "total_tickets": total_tickets,
        "pending_tickets": pending_tickets,
        "resolved_tickets": resolved_tickets,
        "resolution_rate": resolution_rate,
        "escalations": escalations,
    }

    return analytics
