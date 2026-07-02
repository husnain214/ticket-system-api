from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.lib.redis import redis_client

router = APIRouter()


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
