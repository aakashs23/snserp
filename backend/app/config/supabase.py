from urllib.parse import urlparse, urlunparse

from supabase import create_client, Client
from app.config.settings import settings


def normalize_supabase_url(url: str) -> str:
    """Normalize Supabase project URL so client auth/storage endpoints resolve correctly."""
    if not url:
        return url

    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    for suffix in ("/rest/v1", "/auth/v1"):
        if path.endswith(suffix):
            path = path[: -len(suffix)]
            break

    return urlunparse(parsed._replace(path=path))


supabase_url = normalize_supabase_url(settings.supabase_url)

supabase: Client = create_client(
    supabase_url=supabase_url,
    supabase_key=settings.supabase_service_key,
)


def ensure_documents_bucket() -> None:
    """Ensure the 'documents' storage bucket exists, create if missing."""
    try:
        # Try to list buckets to check if documents bucket exists
        buckets = supabase.storage.list_buckets()
        bucket_names = [b.name for b in buckets]
        
        if "documents" not in bucket_names:
            # Create the bucket if it doesn't exist
            supabase.storage.create_bucket(
                "documents",
                options={"public": False}
            )
            print("Created 'documents' storage bucket")
    except Exception as e:
        print(f"Warning: Could not ensure documents bucket exists: {e}")
        # Don't fail startup if bucket creation fails
        pass

