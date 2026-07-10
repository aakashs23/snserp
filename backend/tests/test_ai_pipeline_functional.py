"""Functional coverage for the document AI pipeline.

Every external dependency (LLM, embeddings, ChromaDB, Postgres) is faked, so
these run offline. They assert the pipeline's *behaviour* — chunking, category
normalisation, OCR text cleaning, and above all its degradation paths — not the
accuracy of any model.
"""

import json
import uuid

import pytest

from app.services import ai_pipeline
from app.services.ai_pipeline import clean_ocr_text, normalize_ai_category
from app.services.rag_service import semantic_chunk, semantic_chunk_pages


# ── Category normalisation: clamp whatever the LLM says to the allowed set ────
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Invoice", "Invoice"),
        ("invoice", "Invoice"),
        ("  Purchase Order  ", "Purchase Order"),
        ("po", "Purchase Order"),
        ("customer", "Customer Document"),
        ("misc", "Miscellaneous"),
        ("Bank Statement", "Bank Statement"),
        ("something the model invented", "Miscellaneous"),
        ("", "Miscellaneous"),
        (None, "Miscellaneous"),
    ],
)
def test_ai_category_is_clamped_to_the_allowed_set(raw, expected):
    assert normalize_ai_category(raw) == expected


def test_every_normalised_category_is_actually_allowed():
    for raw in ["invoice", "po", "garbage", None, "receipt"]:
        assert normalize_ai_category(raw) in ai_pipeline.ALLOWED_AI_CATEGORIES


# ── OCR text cleaning ────────────────────────────────────────────────────────
def test_clean_ocr_text_collapses_runs_of_spaces():
    assert clean_ocr_text("total     amount") == "total amount"


def test_clean_ocr_text_caps_blank_lines_at_two():
    assert clean_ocr_text("a\n\n\n\n\nb") == "a\n\nb"


def test_clean_ocr_text_strips_isolated_artifact_lines():
    cleaned = clean_ocr_text("Invoice\n|\nTotal")
    assert "|" not in cleaned


def test_clean_ocr_text_handles_empty_input():
    assert clean_ocr_text("") == ""
    assert clean_ocr_text(None) == ""


def test_clean_ocr_text_preserves_real_content():
    text = "Invoice INV-001\nAmount: 1,250.00"
    assert "INV-001" in clean_ocr_text(text)
    assert "1,250.00" in clean_ocr_text(text)


# ── Semantic chunking ────────────────────────────────────────────────────────
def test_short_text_stays_a_single_chunk():
    assert len(semantic_chunk("One sentence. Two sentences.")) == 1


def test_long_text_is_split_into_multiple_chunks():
    text = ". ".join(f"This is sentence number {i}" for i in range(400)) + "."
    chunks = semantic_chunk(text, max_tokens=100, overlap_tokens=10)
    assert len(chunks) > 1
    assert all(c.strip() for c in chunks)


def test_chunks_overlap_so_context_is_not_lost_at_boundaries():
    text = ". ".join(f"Sentence {i}" for i in range(200)) + "."
    chunks = semantic_chunk(text, max_tokens=50, overlap_tokens=20)
    assert len(chunks) >= 2
    tail_of_first = set(chunks[0].split())
    head_of_second = set(chunks[1].split())
    assert tail_of_first & head_of_second, "adjacent chunks share no tokens"


def test_empty_text_produces_no_chunks():
    assert semantic_chunk("") == []
    assert semantic_chunk("   ") == []


def test_chunk_indices_are_globally_sequential_across_pages():
    pages = [(1, "Page one text. More text."), (2, "Page two text."), (3, "Page three.")]
    records = semantic_chunk_pages(pages)
    assert [r["chunk_index"] for r in records] == list(range(len(records)))


def test_chunks_carry_their_source_page_number():
    pages = [(1, "Alpha text here."), (2, "Beta text here.")]
    records = semantic_chunk_pages(pages)
    assert {r["page_number"] for r in records} == {1, 2}


def test_blank_pages_are_skipped():
    records = semantic_chunk_pages([(1, "Real content."), (2, "   "), (3, "More content.")])
    assert {r["page_number"] for r in records} == {1, 3}


# ── End-to-end pipeline with every dependency faked ──────────────────────────
class _FakeResult:
    def scalar_one_or_none(self):
        return None


class _FakeSession:
    def __init__(self):
        self.added = []
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_a):
        return False

    async def get(self, *_a, **_kw):
        return None  # Document row absent; pipeline should tolerate it

    async def execute(self, *_a, **_kw):
        return _FakeResult()

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True


class _FakeCollection:
    def __init__(self, fail=False):
        self.fail = fail
        self.added_batches = []

    def add(self, **kwargs):
        if self.fail:
            raise RuntimeError("Collection expecting embedding with dimension of 384, got 768")
        self.added_batches.append(kwargs)


_GOOD_METADATA = {
    "title": "March Invoice",
    "description": "Invoice for March supply.",
    "keywords": ["invoice", "march"],
    "ai_category": "Invoice",
    "invoice_number": "INV-001",
    "customer_details": "Acme Ltd",
    "amount": 1250.0,
    "gst_number": "33ABCDE1234F1Z5",
}


@pytest.fixture
def pipeline_env(monkeypatch):
    """Wire the pipeline to fakes. Returns (session, collection, calls)."""
    session = _FakeSession()
    collection = _FakeCollection()
    calls = {"generate": [], "embed": []}

    async def fake_generate(prompt, **_kw):
        calls["generate"].append(prompt)
        return json.dumps(_GOOD_METADATA), "fake-provider"

    async def fake_embed(text):
        calls["embed"].append(text)
        return [0.1, 0.2, 0.3]

    def fake_ocr():
        raise AssertionError("PaddleOCR must not run for plain-text input")

    monkeypatch.setattr(ai_pipeline, "async_session_factory", lambda: session)
    monkeypatch.setattr(ai_pipeline, "ai_generate", fake_generate)
    monkeypatch.setattr(ai_pipeline, "ai_embed", fake_embed)
    monkeypatch.setattr(ai_pipeline, "collection", collection)
    monkeypatch.setattr(ai_pipeline, "get_ocr", fake_ocr)
    return session, collection, calls


def test_text_document_is_extracted_embedded_and_indexed(pipeline_env):
    import asyncio

    session, collection, calls = pipeline_env
    body = b"Invoice for March. Total amount is 1250.00. Thank you."

    asyncio.run(
        ai_pipeline.process_document_background(
            uuid.uuid4(), body, "march.txt", "text/plain"
        )
    )

    assert len(calls["generate"]) == 1, "the LLM should be asked for metadata exactly once"
    assert calls["embed"], "chunks should have been embedded"
    assert collection.added_batches, "embeddings should have been written to Chroma"
    assert session.committed

    batch = collection.added_batches[0]
    assert len(batch["documents"]) == len(batch["embeddings"]) == len(batch["ids"])
    meta = batch["metadatas"][0]
    assert meta["file_name"] == "march.txt"
    assert meta["page_number"] == 1


def test_chroma_failure_does_not_lose_the_document(monkeypatch):
    """A stale vector store must not throw away OCR text and metadata."""
    import asyncio

    session = _FakeSession()
    failing_collection = _FakeCollection(fail=True)

    async def fake_generate(prompt, **_kw):
        return json.dumps(_GOOD_METADATA), "fake-provider"

    async def fake_embed(_text):
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr(ai_pipeline, "async_session_factory", lambda: session)
    monkeypatch.setattr(ai_pipeline, "ai_generate", fake_generate)
    monkeypatch.setattr(ai_pipeline, "ai_embed", fake_embed)
    monkeypatch.setattr(ai_pipeline, "collection", failing_collection)

    asyncio.run(
        ai_pipeline.process_document_background(
            uuid.uuid4(), b"Some invoice text here.", "x.txt", "text/plain"
        )
    )

    assert session.committed, "the document must still be committed"
    doc_ai = [o for o in session.added if type(o).__name__ == "DocumentAI"]
    assert doc_ai, "DocumentAI row should still be written"
    assert doc_ai[0].embedding_status == "completed"
    assert doc_ai[0].chromadb_id is None, "unindexed documents must not claim a chroma id"


def test_unparseable_llm_output_falls_back_to_safe_metadata(monkeypatch):
    """The LLM sometimes returns prose instead of JSON. Don't crash."""
    import asyncio

    session = _FakeSession()

    async def fake_generate(_prompt, **_kw):
        return "Sure! Here is the metadata you asked for.", "fake-provider"

    async def fake_embed(_text):
        return [0.1]

    monkeypatch.setattr(ai_pipeline, "async_session_factory", lambda: session)
    monkeypatch.setattr(ai_pipeline, "ai_generate", fake_generate)
    monkeypatch.setattr(ai_pipeline, "ai_embed", fake_embed)
    monkeypatch.setattr(ai_pipeline, "collection", _FakeCollection())

    asyncio.run(
        ai_pipeline.process_document_background(
            uuid.uuid4(), b"Body text.", "weird.txt", "text/plain"
        )
    )

    assert session.committed
    meta = [o for o in session.added if type(o).__name__ == "DocumentMetadata"]
    assert meta, "metadata row should still be written"
    assert meta[0].title == "weird.txt", "falls back to the filename"


def test_markdown_fenced_json_is_parsed(monkeypatch):
    """Models love wrapping JSON in ```json fences."""
    import asyncio

    session = _FakeSession()

    async def fake_generate(_prompt, **_kw):
        return "```json\n" + json.dumps(_GOOD_METADATA) + "\n```", "fake-provider"

    async def fake_embed(_text):
        return [0.1]

    monkeypatch.setattr(ai_pipeline, "async_session_factory", lambda: session)
    monkeypatch.setattr(ai_pipeline, "ai_generate", fake_generate)
    monkeypatch.setattr(ai_pipeline, "ai_embed", fake_embed)
    monkeypatch.setattr(ai_pipeline, "collection", _FakeCollection())

    asyncio.run(
        ai_pipeline.process_document_background(
            uuid.uuid4(), b"Body text.", "fenced.txt", "text/plain"
        )
    )

    meta = [o for o in session.added if type(o).__name__ == "DocumentMetadata"]
    assert meta[0].title == "March Invoice"
    assert meta[0].invoice_number == "INV-001"


def test_docx_text_extraction_reads_paragraphs():
    """extract_docx_text parses the OOXML directly, with no python-docx dep."""
    import io
    import zipfile

    xml = (
        '<?xml version="1.0"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p><w:r><w:t>First paragraph.</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Second </w:t></w:r><w:r><w:t>paragraph.</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml)

    text = ai_pipeline.extract_docx_text(buf.getvalue())
    assert text == "First paragraph.\nSecond paragraph."


def test_corrupt_docx_returns_empty_rather_than_raising():
    assert ai_pipeline.extract_docx_text(b"not a zip file") == ""
