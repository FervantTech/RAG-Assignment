"""Check grounded citations and missing-evidence behaviour without an API key."""

import unittest
from unittest.mock import MagicMock, patch

from src.rag import EMBEDDING_MODEL, Citation, ModelAnswer, answer_question, retrieve, validate_answer


class GroundingTests(unittest.TestCase):
    def test_retrieve_includes_cover_without_duplicate_passages(self):
        """Keep document title context alongside vector search, without repeating it."""
        collection = MagicMock()
        collection.count.return_value = 2
        collection.metadata = {"embedding_model": EMBEDDING_MODEL}
        collection.get.return_value = {
            "ids": ["cover"],
            "documents": ["Sample course handbook"],
            "metadatas": [{"page_number": 1, "source": "handbook.pdf"}],
        }
        cover = {"page_number": 1, "text": "Sample course handbook", "source": "handbook.pdf"}
        for initial in ([], [cover]):
            with patch("src.rag.get_collection", return_value=collection):
                with patch("src.rag.embed_texts", return_value=[[1, 0]]):
                    with patch("src.rag.search_chunks", return_value=list(initial)):
                        passages = retrieve("What is the course called?")
            self.assertEqual(passages, [cover])

    passages = [{"page_number": 12, "text": "Students must attend all scheduled sessions."}]

    def test_valid_quote_produces_page_reference(self):
        """Check that a quote found in the evidence produces its supporting page reference."""
        result = ModelAnswer(answer="All scheduled sessions require attendance.", citations=[
            Citation(page_number=12, quote="attend all scheduled sessions")])
        self.assertEqual(validate_answer(result, self.passages)["source"], "Page 12")

    def test_invented_page_or_quote_or_missing_citation_is_rejected(self):
        """Check that unsupported quotes, pages, or missing citations lead to an unavailable answer."""
        for citations in ([], [Citation(page_number=99, quote="attend all scheduled sessions")],
                          [Citation(page_number=12, quote="Attendance is optional")]):
            result = ModelAnswer(answer="Unsupported answer", citations=citations)
            self.assertEqual(validate_answer(result, self.passages),
                             {"answer": "answer unavailable", "source": None})

    def test_model_abstention_has_no_page_reference(self):
        """Check that a model's unavailable answer does not claim a supporting page."""
        result = ModelAnswer(answer="answer unavailable", citations=[])
        self.assertIsNone(validate_answer(result, self.passages)["source"])

    def test_empty_retrieval_skips_model_request(self):
        """Check that no model request is made when retrieval finds no passages."""
        with patch("src.rag.retrieve", return_value=[]), patch("src.rag.generate_answer") as model:
            self.assertEqual(answer_question("Unknown?"),
                             {"answer": "answer unavailable", "source": None})
        model.assert_not_called()

    def test_question_and_retrieved_context_reach_generator(self):
        """Check that the answer generator receives the question and its retrieved passages."""
        response = ModelAnswer(answer="Attendance is required.", citations=[
            Citation(page_number=12, quote="attend all scheduled sessions")])
        with patch("src.rag.retrieve", return_value=self.passages):
            with patch("src.rag.generate_answer", return_value=response) as model:
                result = answer_question("What is required?")
        model.assert_called_once_with("What is required?", self.passages)
        self.assertEqual(result["source"], "Page 12")


if __name__ == "__main__":
    unittest.main()
