"""OCR service using PaddleOCR for text extraction from images and scanned PDFs."""


class OCRService:
    """Extract text from scanned documents and images using PaddleOCR."""

    def __init__(self):
        self._ocr = None

    async def initialize(self):
        """Lazy-initialize PaddleOCR (heavy import)."""
        # TODO: Initialize PaddleOCR with configured language
        pass

    async def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from an image file."""
        # TODO: Implement OCR text extraction
        raise NotImplementedError

    async def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a scanned PDF using OCR."""
        # TODO: Implement PDF OCR extraction
        raise NotImplementedError
