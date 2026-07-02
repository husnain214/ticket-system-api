from fastapi import FastAPI
from app.db.create_db import create_db_and_tables
from contextlib import asynccontextmanager

from app.routes.auth import auth_backend, fastapi_users
from app.routes.tickets import router as tickets_router
from app.routes.dashboard import router as dashboard_router
from app.schemas import UserRead, UserCreate, UserUpdate


@asynccontextmanager
async def lifespan():
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(tickets_router)
app.include_router(dashboard_router)
