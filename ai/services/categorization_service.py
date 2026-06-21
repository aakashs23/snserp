"""AI document categorization service using Qwen 3."""

DOCUMENT_CATEGORIES = [
    "Invoice",
    "Purchase Order",
    "Agreements",
    "Customer Document",
    "Excel Sheets",
    "Bank Related Documents",
    "Government Letter",
    "Class A Share Documents",
    "TDS",
    "GST",
    "Company Receipts",
    "Miscellaneous",
]


class CategorizationService:
    """Automatically categorize uploaded documents using AI."""

    def __init__(self):
        pass

    async def categorize(self, document_text: str, filename: str) -> str:
        """Categorize a document based on its content and filename."""
        # TODO: Use Qwen 3 to classify document into one of DOCUMENT_CATEGORIES
        raise NotImplementedError

    async def extract_metadata(self, document_text: str) -> dict:
        """Extract structured metadata from document text."""
        # TODO: Extract invoice number, customer, date, amount, GST number etc.
        raise NotImplementedError
