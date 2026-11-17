"""Check the HTTP contract without making external model calls."""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api import app
from src.rag import ModelError, SetupError


class ApiTests(unittest.TestCase):
    def setUp(self):
        """Prepare a fresh test client or temporary database before each test."""
        self.client = TestClient(app)

    def test_answer_and_page_are_returned_as_json(self):
        """Check that a valid question returns an answer and page in the expected JSON format."""
        expected = {"answer": "Attendance is required.", "source": "Page 12"}
        with patch("src.api.answer_question", return_value=expected) as service:
            response = self.client.post("/ask", json={"question": " Attendance? "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        service.assert_called_once_with("Attendance?")

    def test_unavailable_answer_has_no_source(self):
        """Check that an unavailable answer has no claimed source page."""
        expected = {"answer": "answer unavailable", "source": None}
        with patch("src.api.answer_question", return_value=expected):
            self.assertEqual(self.client.post("/ask", json={"question": "Unknown?"}).json(), expected)

    def test_invalid_requests_are_rejected_before_model_calls(self):
        """Check that invalid input is rejected before any answer-generation call."""
        with patch("src.api.answer_question") as service:
            for payload in ({}, {"question": " "}, {"question": None},
                            {"question": 42}, {"question": "x" * 2001},
                            {"question": "hello", "extra": True}):
                with self.subTest(payload_type=str(type(payload.get("question")))):
                    self.assertEqual(self.client.post("/ask", json=payload).status_code, 422)
            self.assertEqual(self.client.post("/ask", content="{invalid",
                             headers={"Content-Type": "application/json"}).status_code, 422)
            service.assert_not_called()

    def test_service_errors_are_distinct_from_missing_answers(self):
        """Check that service failures produce errors instead of pretending evidence is missing."""
        for error, expected_status in ((SetupError("Configure Gemini."), 503),
                                       (ModelError("Quota reached."), 502),
                                       (RuntimeError("private detail"), 500)):
            with self.subTest(expected_status=expected_status):
                with patch("src.api.answer_question", side_effect=error):
                    response = self.client.post("/ask", json={"question": "Question?"})
                self.assertEqual(response.status_code, expected_status)
                self.assertNotIn("private detail", response.text)


if __name__ == "__main__":
    unittest.main()
