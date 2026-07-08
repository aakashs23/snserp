import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import async_session_factory
from app.api.invoices import export_invoices
from app.models.users import User
import uuid

async def main():
    async with async_session_factory() as db:
        user = User(id=uuid.uuid4(), email="test@example.com", full_name="Test", role_id=uuid.uuid4(), is_active=True)
        for fmt in ["csv", "xlsx", "pdf"]:
            try:
                print(f"Testing {fmt}...")
                response = await export_invoices(
                    format=fmt,
                    status_filter=None, customer_id=None, from_date=None, to_date=None,
                    search=None, sort_by="date", sort_order="desc",
                    db=db, current_user=user
                )
                print(f"SUCCESS {fmt}")
            except Exception as e:
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
