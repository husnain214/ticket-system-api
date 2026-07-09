import uuid
from app.core.config import settings
from fastapi_users.password import PasswordHelper


from app.db.create_db import async_session_maker
from app.db.models import User
from app.db.enums import UserRole

password_helper = PasswordHelper()

ADMIN_EMAIL, ADMIN_PASSWORD = settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD


async def seed_db():
    async with async_session_maker() as session:
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Admin already exists: {ADMIN_EMAIL}")
            return

        hashed_password = password_helper.hash(ADMIN_PASSWORD)

        admin = User(
            id=uuid.uuid4(),
            email=ADMIN_EMAIL,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            is_superuser=False,
        )

        session.add(admin)
        await session.commit()
        print(f"Admin created: {ADMIN_EMAIL}")
        print(f"Password: {ADMIN_PASSWORD}")
