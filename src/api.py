"""JSON API for the PDF assistant. Run with: python -m uvicorn src.api:app"""

import logging
from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, StringConstraints

from src.rag import ModelError, SetupError, answer_question

app = FastAPI(title="PDF RAG Assistant", version="0.1.0")
logger = logging.getLogger(__name__)


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: Annotated[str, StringConstraints(
        strict=True, strip_whitespace=True, min_length=1, max_length=2000
    )]


class AskResponse(BaseModel):
    answer: str
    source: str | None


@app.get("/health")
def health():
    """Tell a caller that the API process is running.
    This does not check the PDF index or contact Gemini."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Receive a JSON question and return a JSON answer with source pages.
    Turn setup and service problems into clear HTTP error responses."""
    try:
        return answer_question(request.question)
    except SetupError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ModelError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        # Keep unexpected failure details (and potential local data) out of responses.
        logger.error("Request failed with %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="The request could not be processed.") from exc
