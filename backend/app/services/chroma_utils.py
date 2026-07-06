import logging

logger = logging.getLogger(__name__)


def is_embedding_dimension_mismatch(exc: Exception) -> bool:
    """Return True when a Chroma error points to an embedding dimension mismatch."""
    message = str(exc).lower()
    return "dimension" in message or "embedding" in message


def ensure_chroma_collection(client, collection_name: str):
    """Create or recreate a Chroma collection if its embedding dimension is incompatible."""
    try:
        return client.get_or_create_collection(name=collection_name)
    except Exception as exc:
        if is_embedding_dimension_mismatch(exc):
            logger.warning(
                "Recreating Chroma collection '%s' after embedding mismatch: %s",
                collection_name,
                exc,
            )
            try:
                client.delete_collection(name=collection_name)
            except Exception:
                pass
            return client.get_or_create_collection(name=collection_name)
        raise
