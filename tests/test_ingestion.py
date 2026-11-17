"""Check chunk boundaries and PDF page metadata using a fake PDF reader."""

import unittest
from unittest.mock import MagicMock, patch

from src.read_pdf import chunk_text, extract_pages


class IngestionTests(unittest.TestCase):
    def test_overlap_and_empty_input(self):
        """Check overlapping text pieces and the result of splitting an empty string."""
        self.assertEqual(chunk_text("ABCDEFGHIJ", 4, 1), ["ABCD", "DEFG", "GHIJ", "J"])
        self.assertEqual(chunk_text("", 4), [])

    def test_invalid_chunk_settings(self):
        """Check that invalid chunk sizes and overlap settings are rejected."""
        for size, overlap in ((0, 0), (-1, 0), (4, -1), (4, 4)):
            with self.assertRaises(ValueError):
                chunk_text("Text", size, overlap)

    def test_blank_pages_do_not_change_original_page_numbers(self):
        """Check that skipping blank pages still preserves the original PDF page numbers."""
        reader = MagicMock()
        reader.pages = [MagicMock(), MagicMock(), MagicMock()]
        for page, text in zip(reader.pages, ["  ", " Page two ", "Page three"]):
            page.extract_text.return_value = text
        with patch("src.read_pdf.PdfReader", return_value=reader):
            records = extract_pages("unused.pdf", max_pages=2)
        self.assertEqual(records, [{"page_number": 2, "text": "Page two"}])


if __name__ == "__main__":
    unittest.main()
