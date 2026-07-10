import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.database.session import async_session_factory
from app.models.documents import Document
from app.services.storage_service import storage_remove

async def delete_expired_trash_loop():
    """Background task that runs periodically to permanently delete documents older than 30 days in the trash."""
    while True:
        try:
            async with async_session_factory() as session:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
                
                query = select(Document).where(
                    Document.is_deleted == True,
                    Document.deleted_at < cutoff_date
                )
                
                result = await session.execute(query)
                expired_docs = result.scalars().all()
                
                for doc in expired_docs:
                    # 1. Delete from Supabase Storage
                    try:
                        await storage_remove("documents", [doc.storage_path])
                    except Exception as e:
                        print(f"Cleanup Task: Failed to delete {doc.id} from storage: {e}")
                        
                    # 2. Delete from DB
                    await session.delete(doc)
                
                if expired_docs:
                    await session.commit()
                    print(f"Cleanup Task: Permanently deleted {len(expired_docs)} expired documents.")
                    
        except Exception as e:
            print(f"Cleanup Task: Error during trash cleanup: {e}")
            
        # Sleep for 12 hours before running again
        await asyncio.sleep(43200)
