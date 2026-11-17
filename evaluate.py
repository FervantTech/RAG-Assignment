"""Record live /ask results for ten questions; requires a configured Gemini key."""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values
from fastapi.testclient import TestClient

from src.api import app
from src.read_pdf import REPO_ROOT
from src.vector_store import get_collection


def main():
    """Send at least ten saved test questions through the API code.
    Record real answers and sources in a report for review, stopping on an API error."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", type=Path,
                        default=REPO_ROOT / "evaluation/questions.json")
    parser.add_argument("--output", type=Path,
                        default=REPO_ROOT / "evaluation/results.json")
    parser.add_argument("--delay", type=float, default=7,
                        help="Seconds between live requests; adjust for your project's quota.")
    args = parser.parse_args()
    import os
    key = os.getenv("GEMINI_API_KEY") or dotenv_values(REPO_ROOT / ".env").get("GEMINI_API_KEY")
    if not key:
        parser.error("Set GEMINI_API_KEY in .env before running the live evaluation.")
    if args.delay < 0:
        parser.error("--delay must not be negative.")
    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    if len(questions) < 10:
        parser.error("Include at least ten meaningful questions.")

    collection = get_collection()
    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "indexed_source": (collection.metadata or {}).get("source"),
        "note": "Live output, not automatically graded. Manually verify every answer and page.",
        "results": [],
    }
    client = TestClient(app)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for i, item in enumerate(questions):
        if i:
            time.sleep(args.delay)
        response = client.post("/ask", json={"question": item["question"]})
        report["results"].append({
            "question": item["question"],
            "http_status": response.status_code,
            **response.json(),
            "review": "pending",
        })
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Question {i + 1}/{len(questions)}: HTTP {response.status_code}")
        if response.status_code != 200:
            print("Stopped after an API error. Fix configuration/quota before retrying.")
            raise SystemExit(1)
    print(f"Saved live answers and source pages to {args.output}.")


if __name__ == "__main__":
    main()
