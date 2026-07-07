from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.create_db import create_db_and_tables
from contextlib import asynccontextmanager

from app.db.seeder import seed_db
from app.lib.pinecone import create_pinecone_index
from app.routes.auth import auth_backend, fastapi_users, current_active_user
from app.routes.tickets import router as tickets_router
from app.routes.dashboard import router as dashboard_router
from app.schemas import UserRead, UserCreate, UserUpdate
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_pinecone_index()
    await create_db_and_tables()
    await seed_db()
    yield


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CLIENT_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth", tags=["auth"]
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
app.include_router(tickets_router, dependencies=[Depends(current_active_user)])
app.include_router(dashboard_router)
