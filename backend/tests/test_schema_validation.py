"""Input validation at the trust boundary.

Pure Pydantic — no app, no DB. Each test asserts both directions: oversized or
malformed input is rejected, and realistic valid input still constructs, so the
new constraints can't silently break normal use.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest
from app.schemas.documents import DocumentUpdate
from app.schemas.invoices import InvoiceCreate, InvoiceUpdate
from app.schemas.users import UserCreate


def _invoice(**overrides):
    data = dict(
        invoice_number="INV-2026-0001",
        customer_id=uuid.uuid4(),
        invoice_date=date(2026, 3, 1),
    )
    data.update(overrides)
    return InvoiceCreate(**data)


# ── Invoices ─────────────────────────────────────────────────────────────────
def test_valid_invoice_still_constructs():
    inv = _invoice(payment_mode="NEFT", notes="Paid in full", gross_amount=Decimal("1000"))
    assert inv.invoice_number == "INV-2026-0001"
    assert inv.status == "draft"


def test_invoice_number_cannot_exceed_its_column_width():
    with pytest.raises(ValidationError, match="at most 50 characters"):
        _invoice(invoice_number="X" * 51)


def test_invoice_number_cannot_be_empty():
    with pytest.raises(ValidationError):
        _invoice(invoice_number="")


def test_payment_mode_cannot_exceed_its_column_width():
    with pytest.raises(ValidationError, match="at most 30 characters"):
        _invoice(payment_mode="X" * 31)


@pytest.mark.parametrize("field", ["notes", "description"])
def test_free_text_fields_are_capped(field):
    with pytest.raises(ValidationError, match="at most 5000 characters"):
        _invoice(**{field: "X" * 5001})


def test_invoice_update_is_constrained_too():
    """The update path is a trust boundary just like create."""
    with pytest.raises(ValidationError):
        InvoiceUpdate(payment_mode="X" * 31)
    assert InvoiceUpdate(payment_mode="UPI").payment_mode == "UPI"


# ── Users ────────────────────────────────────────────────────────────────────
def _user(**overrides):
    data = dict(
        full_name="Aakash S",
        email="user@example.com",
        password="correct horse battery",
        role_id=uuid.uuid4(),
    )
    data.update(overrides)
    return UserCreate(**data)


def test_valid_user_still_constructs():
    assert _user().email == "user@example.com"


@pytest.mark.parametrize("bad_email", ["not-an-email", "@example.com", "a@b", "a b@c.com", ""])
def test_malformed_emails_are_rejected(bad_email):
    with pytest.raises(ValidationError):
        _user(email=bad_email)


def test_short_passwords_are_rejected():
    with pytest.raises(ValidationError, match="at least 8 characters"):
        _user(password="short")


def test_absurdly_long_passwords_are_rejected():
    """Unbounded passwords are a hashing DoS vector."""
    with pytest.raises(ValidationError, match="at most 128 characters"):
        _user(password="X" * 129)


# ── Documents ────────────────────────────────────────────────────────────────
def test_valid_document_update_still_constructs():
    d = DocumentUpdate(display_name="March invoice", category="Invoice")
    assert d.display_name == "March invoice"


def test_document_update_all_fields_optional():
    """PATCH-style partial update must remain possible."""
    assert DocumentUpdate().display_name is None


@pytest.mark.parametrize(
    "field,limit", [("original_name", 255), ("display_name", 255), ("category", 50)]
)
def test_document_fields_are_capped_at_column_width(field, limit):
    with pytest.raises(ValidationError, match=f"at most {limit} characters"):
        DocumentUpdate(**{field: "X" * (limit + 1)})


# ── Chat ─────────────────────────────────────────────────────────────────────
def test_valid_chat_message_still_constructs():
    assert ChatRequest(message="What was March revenue?").session_id is None


def test_chat_message_is_capped_before_reaching_the_llm():
    """Was unbounded: any size string flowed straight into the prompt."""
    with pytest.raises(ValidationError, match="at most 4000 characters"):
        ChatRequest(message="X" * 4001)


def test_empty_chat_message_is_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(message="")


def test_chat_message_at_the_limit_is_accepted():
    """Boundary: exactly 4000 must pass, not 3999."""
    assert len(ChatRequest(message="X" * 4000).message) == 4000
