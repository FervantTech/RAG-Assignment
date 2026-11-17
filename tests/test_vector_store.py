"""Check persistence and ranking with known vectors; no model download needed."""

import tempfile
import unittest

from src.vector_store import get_collection, search_chunks, store_chunks


class VectorStoreTests(unittest.TestCase):
    def setUp(self):
        """Prepare a fresh test client or temporary database before each test."""
        self.directory = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.directory.cleanup)
        self.collection = get_collection(self.directory.name)
        self.records = [
            {"page_number": 2, "text": "First passage"},
            {"page_number": 8, "text": "Second passage"},
        ]
        store_chunks(self.collection, self.records, [[1.0, 0.0], [0.0, 1.0]],
                     "test.pdf", "test-model")

    def test_reopen_preserves_text_and_page_and_ranking(self):
        """Check that saved passages survive reopening and are returned in similarity order."""
        reopened = get_collection(self.directory.name)
        results = search_chunks(reopened, [0.0, 1.0], top_k=10)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["text"], "Second passage")
        self.assertEqual(results[0]["page_number"], 8)
        self.assertEqual(results[0]["source"], "test.pdf")
        self.assertLess(results[0]["distance"], results[1]["distance"])

    def test_reindex_replaces_old_source_and_removes_stale_chunks(self):
        """Check that rebuilding with a shorter PDF removes leftover records from the old PDF."""
        store_chunks(self.collection, [{"page_number": 5, "text": "Replacement"}],
                     [[1.0, 0.0]], "new.pdf", "test-model")
        self.assertEqual(self.collection.count(), 1)
        result = search_chunks(self.collection, [1.0, 0.0])[0]
        self.assertEqual(result["text"], "Replacement")
        self.assertEqual(result["source"], "new.pdf")
        self.assertEqual(result["page_number"], 5)

    def test_invalid_inputs_do_not_replace_existing_records(self):
        """Check that invalid storage inputs preserve existing records and invalid search limits fail."""
        with self.assertRaises(ValueError):
            store_chunks(self.collection, self.records, [[1.0, 0.0]],
                         "test.pdf", "test-model")
        self.assertEqual(self.collection.count(), 2)
        with self.assertRaises(ValueError):
            search_chunks(self.collection, [1.0, 0.0], top_k=0)


if __name__ == "__main__":
    unittest.main()
