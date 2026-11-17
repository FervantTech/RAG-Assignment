"""Test Gemini request construction and configuration without contacting Google."""

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from google import genai
from google.genai import types

from src.rag import ModelAnswer, ModelError, SetupError, generate_answer


class GeminiTests(unittest.TestCase):
    def test_schema_passes_real_sdk_conversion_without_network(self):
        """Check that Google's SDK accepts our answer format without contacting Google."""
        payload = {"candidates": [{"content": {"parts": [{"text":
            '{"answer":"answer unavailable","citations":[]}'}], "role": "model"},
            "finishReason": "STOP"}]}
        with genai.Client(api_key="fake-test-key") as client:
            with patch.object(client._api_client, "request",
                              return_value=types.HttpResponse(body=json.dumps(payload))) as request:
                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite", contents="Test",
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json", response_schema=ModelAnswer))
                request.assert_called_once()
        self.assertEqual(ModelAnswer.model_validate_json(response.text).citations, [])

    def test_missing_key_does_not_contact_google(self):
        """Check that a missing API key produces a setup error without contacting Google."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            with patch("src.rag.load_dotenv"), patch("src.rag.genai.Client") as client:
                with self.assertRaises(SetupError):
                    generate_answer("Question?", [])
                client.assert_not_called()

    def test_structured_response_and_context(self):
        """Check that the question and evidence are passed to the mocked Gemini client."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = (
            '{"answer":"Required.","citations":[{"page_number":12,"quote":"Attendance required"}]}'
        )
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key"}):
            with patch("src.rag.load_dotenv"), patch("src.rag.genai.Client") as factory:
                factory.return_value.__enter__.return_value = mock_client
                result = generate_answer("Attendance?", [
                    {"page_number": 12, "text": "Attendance required"}])
        self.assertEqual(result.citations[0].page_number, 12)
        kwargs = mock_client.models.generate_content.call_args.kwargs
        self.assertIn("Attendance required", kwargs["contents"])
        self.assertIn("Attendance?", kwargs["contents"])

    def test_malformed_response_is_a_service_error(self):
        """Check that an unreadable model response becomes a clear service error."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "not JSON"
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-test-key"}):
            with patch("src.rag.load_dotenv"), patch("src.rag.genai.Client") as factory:
                factory.return_value.__enter__.return_value = mock_client
                with self.assertRaises(ModelError):
                    generate_answer("Question?", [])


if __name__ == "__main__":
    unittest.main()
