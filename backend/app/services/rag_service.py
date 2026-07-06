"""Advanced RAG pipeline building blocks.

Provides semantic chunking, cross-encoder reranking, query expansion,
parent-context retrieval, and context compression — all designed to
run non-blocking via asyncio.to_thread where needed.
"""

import asyncio
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Semantic Chunking
# ─────────────────────────────────────────────────────────────────────────────

# Sentence-ending regex: period/question/exclamation followed by whitespace
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

# Headings or blank-line boundaries typical in OCR / extracted text
_PARAGRAPH_RE = re.compile(r"\n{2,}")


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences (best-effort)."""
    parts = _SENTENCE_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def semantic_chunk(
    text: str,
    *,
    max_tokens: int = 800,
    overlap_tokens: int = 100,
    chars_per_token: float = 4.0,
) -> list[str]:
    """Split text into semantically-meaningful chunks.

    Strategy:
      1. Split on paragraph boundaries (double newlines / headings).
      2. Within each paragraph, accumulate sentences until we hit
         *max_tokens* (estimated via chars_per_token).
      3. Overlap the tail of the previous chunk into the next one
         so the LLM doesn't lose context at boundaries.

    Returns a list of chunk strings.
    """
    max_chars = int(max_tokens * chars_per_token)
    overlap_chars = int(overlap_tokens * chars_per_token)

    paragraphs = _PARAGRAPH_RE.split(text)
    sentences: list[str] = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        inner = _split_sentences(para)
        if inner:
            sentences.extend(inner)
        else:
            sentences.append(para)

    if not sentences:
        return [text] if text.strip() else []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sent_len = len(sentence)
        if current_len + sent_len > max_chars and current:
            chunk_text = " ".join(current)
            chunks.append(chunk_text)

            # build overlap from the tail of the current chunk
            overlap: list[str] = []
            ol = 0
            for s in reversed(current):
                ol += len(s)
                overlap.insert(0, s)
                if ol >= overlap_chars:
                    break
            current = overlap
            current_len = sum(len(s) for s in current)

        current.append(sentence)
        current_len += sent_len

    if current:
        chunks.append(" ".join(current))

    return chunks


def semantic_chunk_pages(
    pages: list[tuple[int, str]],
    *,
    max_tokens: int = 800,
    overlap_tokens: int = 100,
) -> list[dict]:
    """Chunk page-aware text.

    Args:
        pages: list of (page_number, page_text) tuples  (1-indexed).

    Returns:
        list of dicts with keys: text, page_number, chunk_index
    """
    result: list[dict] = []
    global_idx = 0

    for page_num, page_text in pages:
        if not page_text.strip():
            continue
        chunks = semantic_chunk(
            page_text,
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
        )
        for chunk_text in chunks:
            result.append({
                "text": chunk_text,
                "page_number": page_num,
                "chunk_index": global_idx,
            })
            global_idx += 1

    return result


# ─────────────────────────────────────────────────────────────────────────────
# 2. Cross-Encoder Reranking
# ─────────────────────────────────────────────────────────────────────────────
_reranker = None


def _get_reranker():
    """Lazy-load the cross-encoder to avoid startup cost."""
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        logger.info("Cross-encoder reranker loaded.")
    return _reranker


def _rerank_sync(
    query: str,
    documents: list[str],
    metadatas: list[dict],
    top_k: int = 5,
) -> list[tuple[str, dict, float]]:
    """Score and rerank documents using the cross-encoder (CPU).

    Returns list of (document_text, metadata, score) sorted by relevance.
    """
    if not documents:
        return []

    reranker = _get_reranker()
    pairs = [(query, doc) for doc in documents]
    scores = reranker.predict(pairs)

    scored = list(zip(documents, metadatas, scores))
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:top_k]


async def rerank_chunks(
    query: str,
    documents: list[str],
    metadatas: list[dict],
    top_k: int = 5,
) -> list[tuple[str, dict, float]]:
    """Async wrapper — runs cross-encoder in a thread."""
    return await asyncio.to_thread(
        _rerank_sync, query, documents, metadatas, top_k
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Query Expansion
# ─────────────────────────────────────────────────────────────────────────────
async def expand_query(query: str) -> list[str]:
    """Generate 2-3 alternative phrasings for a user query using the LLM.

    Returns a list *including* the original query.
    """
    from app.services.ai_service import ai_generate

    prompt = (
        "You are a search query expansion assistant.\n"
        "Given the user query below, generate exactly 3 alternative search queries "
        "that would help find relevant documents. Each alternative should capture "
        "a different angle or synonym of the original intent.\n"
        "Output ONLY the 3 alternatives, one per line, no numbering, no explanation.\n\n"
        f"User Query: {query}"
    )

    try:
        raw, _ = await ai_generate(prompt, temperature=0.3)
        alternatives = [
            line.strip().lstrip("0123456789.-) ")
            for line in raw.strip().splitlines()
            if line.strip() and len(line.strip()) > 5
        ][:3]
        return [query] + alternatives
    except Exception as e:
        logger.warning(f"Query expansion failed: {e}")
        return [query]


# ─────────────────────────────────────────────────────────────────────────────
# 4. Parent / Neighbor Context Retrieval
# ─────────────────────────────────────────────────────────────────────────────
def retrieve_parent_context(
    top_chunks: list[tuple[str, dict, float]],
    all_documents: list[str],
    all_metadatas: list[dict],
) -> list[tuple[str, dict, float]]:
    """For each top-ranked chunk, pull its immediate neighbors (±1 by
    chunk_index within the same document) to give the LLM more context.

    Returns the expanded list (deduped, preserving order).
    """
    # Build an index: (document_id, chunk_index) -> (text, meta)
    index: dict[tuple[str, int], tuple[str, dict]] = {}
    for doc, meta in zip(all_documents, all_metadatas):
        key = (meta.get("document_id", ""), meta.get("chunk_index", -1))
        if key[1] >= 0:
            index[key] = (doc, meta)

    seen_keys: set[tuple[str, int]] = set()
    result: list[tuple[str, dict, float]] = []

    for text, meta, score in top_chunks:
        doc_id = meta.get("document_id", "")
        ci = meta.get("chunk_index", -1)

        # Add neighbors first (before), then the chunk itself, then after
        for offset in [-1, 0, 1]:
            neighbor_idx = ci + offset
            key = (doc_id, neighbor_idx)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            if offset == 0:
                result.append((text, meta, score))
            elif key in index:
                n_text, n_meta = index[key]
                # Neighbor gets a slightly lower score to preserve ordering
                result.append((n_text, n_meta, score * 0.8))

    return result


# ─────────────────────────────────────────────────────────────────────────────
# 5. Context Compression / Deduplication
# ─────────────────────────────────────────────────────────────────────────────
def compress_context(
    chunks: list[tuple[str, dict, float]],
    *,
    overlap_threshold: float = 0.6,
) -> list[tuple[str, dict, float]]:
    """Remove near-duplicate chunks and merge contiguous ones from the
    same document.

    Uses a simple token-overlap ratio to detect duplicates.
    """
    if not chunks:
        return []

    def _token_set(text: str) -> set[str]:
        return set(text.lower().split())

    def _overlap_ratio(a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / min(len(a), len(b))

    deduped: list[tuple[str, dict, float]] = []
    token_sets: list[set[str]] = []

    for text, meta, score in chunks:
        ts = _token_set(text)
        is_dup = False
        for existing_ts in token_sets:
            if _overlap_ratio(ts, existing_ts) >= overlap_threshold:
                is_dup = True
                break
        if not is_dup:
            deduped.append((text, meta, score))
            token_sets.append(ts)

    # Merge contiguous chunks from the same doc (adjacent chunk_index)
    if len(deduped) <= 1:
        return deduped

    merged: list[tuple[str, dict, float]] = [deduped[0]]
    for text, meta, score in deduped[1:]:
        prev_text, prev_meta, prev_score = merged[-1]
        same_doc = (
            meta.get("document_id") == prev_meta.get("document_id")
            and meta.get("chunk_index", -1) == prev_meta.get("chunk_index", -2) + 1
        )
        if same_doc:
            # Merge texts, keep earlier metadata, keep higher score
            merged[-1] = (
                prev_text + "\n" + text,
                prev_meta,
                max(prev_score, score),
            )
        else:
            merged.append((text, meta, score))

    return merged
