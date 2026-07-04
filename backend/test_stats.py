import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import SessionLocal
from app.api.analytics import get_dashboard_stats
from app.models.users import User

async def main():
    async with SessionLocal() as db:
        user = User(id="00000000-0000-0000-0000-000000000000", email="test@test.com", role="admin")
        try:
            res = await get_dashboard_stats(current_user=user, db=db)
            print(res)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
