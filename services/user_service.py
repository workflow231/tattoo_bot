import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from db.repositories.user_repo import get_or_create_user, check_user_is_admin, change_admin_status

load_dotenv()


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_or_get_user(
        self,
        telegram_id: int,
        username: str | None,
    ) -> tuple[User, bool]:
        user_tuple = await get_or_create_user(
            session=self.session,
            telegram_id=telegram_id,
            username=username,
        )

        if await check_user_is_admin(
            session=self.session,
            telegram_id=telegram_id
        ):
            await change_admin_status(
                session=self.session,
                admin_id=int(os.getenv("ADMIN_ID"))
            )

        return user_tuple
