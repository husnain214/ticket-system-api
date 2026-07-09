from fastapi import APIRouter, WebSocket, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.lib.redis import redis_client
from app.db.create_db import get_async_session
from app.db.models import Ticket, Escalation, User
from app.db.enums import TicketStatus
from app.routes.auth import current_active_user

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

    except Exception as e:
        print("WebSocket error:", repr(e))

    finally:
        await pubsub.unsubscribe("ticket_updates")
        await pubsub.aclose()


@router.get("/analytics")
async def fetch_analytics(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(current_active_user),
):
    total_tickets = (
        await session.scalar(select(func.count()).select_from(Ticket))
    ) or 0

    if total_tickets == 0:
        return {
            "total_tickets": 0,
            "pending_tickets": 0,
            "resolved_tickets": 0,
            "escalations": 0,
            "resolution_rate": 0,
        }

    pending_tickets = (
        await session.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.status == TicketStatus.PENDING)
        )
    ) or 0

    resolved_tickets = (
        await session.scalar(
            select(func.count())
            .select_from(Ticket)
            .where(Ticket.status == TicketStatus.RESOLVED)
        )
    ) or 0

    escalations = (
        await session.scalar(select(func.count()).select_from(Escalation))
    ) or 0

    resolution_rate = int((resolved_tickets / total_tickets) * 100)

    return {
        "total_tickets": total_tickets,
        "pending_tickets": pending_tickets,
        "resolved_tickets": resolved_tickets,
        "escalations": escalations,
        "resolution_rate": resolution_rate,
    }
