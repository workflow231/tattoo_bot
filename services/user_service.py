from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User
from db.repositories.user_repo import (
    change_admin_status,
    get_or_create_user,
)
from utils.config import get_admin_ids_from_env

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
        user, _ = user_tuple

        if telegram_id in get_admin_ids_from_env() and not user.is_admin:
            await change_admin_status(session=self.session, admin_id=telegram_id)

        return user_tuple
