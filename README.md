# RAG exploration

A Python workspace for exploring retrieval-augmented generation (RAG) over local PDFs.
The current test document is `data/Handbook.pdf`.

## Environment setup (PowerShell)

The local `.venv` was created with Python 3.14. To recreate it with an installed
Python interpreter, run from the repository root:

```powershell
python -m venv .venv
```

Activate the environment and check its interpreter:

```powershell
.\.venv\Scripts\Activate.ps1
python --version
python -m pip --version
```

If PowerShell blocks activation, you can use the environment directly:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip --version
```

Run `deactivate` to leave an activated environment.

## Project layout

- `data/`: local input documents, including the test PDF.
- `pyproject.toml`: project metadata and dependencies.
- `.venv/`: local Python environment (ignored by Git).

Install the project dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe src\read_pdf.py
```

The script inspects all PDF pages by default, skips blank text, makes overlapping
chunks, and generates one embedding per chunk using Sentence Transformers and
`sentence-transformers/all-MiniLM-L6-v2`. The first run downloads the model into
`.cache/models` and requires internet access. Embedding inference runs locally
on the CPU without an API key. The script reports the chunk count and embedding
dimensions, then saves vectors, text, and PDF page numbers in local ChromaDB
storage under `chroma_db/`. Chunks contain up to 800 characters with 100 characters
of overlap. Reindexing refreshes the single-document collection and removes stale
chunks, so it contains only the latest indexed document and page selection.

For a quick partial index, add `--max-pages 3`. For a different PDF, use
`--pdf "data/your-handbook.pdf"`. Run the indexer again after changing the PDF.

Search the saved index without reprocessing the PDF:

```powershell
.\.venv\Scripts\python.exe src\search.py "What is the course name?"
```

Search uses the same embedding model for the question and returns up to three
passages with PDF page numbers. Lower cosine distance means closer vectors;
it is not a confidence percentage or proof that an answer exists. This currently
retrieves passages only. The separate `/ask` API uses the five closest passages plus the cover/title page and
asks Gemini to generate a grounded answer.

Run the storage and retrieval tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Gemini setup

Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey)
using a project labelled Free tier. Do not enable billing if you want to avoid
paid API usage. Free access depends on the model and project quota; see
[Google's billing documentation](https://ai.google.dev/gemini-api/docs/billing).

On a fresh checkout, copy `.env.example` to `.env`. Enter your own key privately:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

The app reads this file automatically. It uses Gemini only for answer generation;
PDF extraction, embeddings, and vector search run locally. Retrieved text and the
question are sent to Google when `/ask` is called. Google's free-tier terms allow
content to be used to improve its products. No OpenAI key or Ollama is needed.

## Run the API

Build the PDF index first, then start the server from the repo root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` to try `POST /ask`. In another PowerShell terminal:

```powershell
$body = @{ question = "What is the course name?" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/ask -Method Post -ContentType 'application/json' -Body $body
```

The JSON response has `answer` and `source` fields, for example
`{"answer": "...", "source": "Page 12"}`. That page is an illustration, not a
verified answer for the current PDF. If the evidence is insufficient, the response
is `{"answer": "answer unavailable", "source": null}`.

The model must provide supporting quotes and pages internally. Python checks
those against the retrieved passages before returning an answer. This guards
against invented citations, but does not prove every claim in the answer is
entailed by its quotes. Review real questions and adjust retrieval or prompts
when needed. Page numbers refer to PDF positions, not printed book numbering.

Malformed, blank, non-string, overly long, or unexpected request fields return
HTTP 422 with JSON details. Missing setup returns 503, model failures return 502,
and unexpected errors return a generic 500. These failures are not reported as
missing document information. `GET /health` checks the process only.

For n8n, configure an HTTP Request node with POST, a JSON body containing
`question`, and the `/ask` URL reachable from n8n. If n8n runs inside Docker or on
another machine, its `localhost` is not this computer. Actual workflow integration
is outside this practical; no n8n workflow is included. The development server has
no authentication and binds only to loopback by default.

## Evaluation and submission

`tests/` covers ingestion, storage, grounding, the Gemini wrapper, and the API.
These unit tests use mocked model responses or fixed vectors; they do not make
external model calls or establish real answer quality.

`evaluation/questions.json` contains twelve handbook questions: ten covering
multiple topics and two questions the handbook should not answer. Expected facts
and PDF pages are included for checking the results. With a configured Gemini
key and index, record actual answers and pages:

```powershell
.\.venv\Scripts\python.exe evaluate.py
```

This sends live requests using your configured Gemini project. It writes
`evaluation/results.json` after each response and stops on API errors. Requests
are spaced seven seconds apart; adjust `--delay` for your actual quota. Check
every answer and source page. The included report has assistant review notes;
inspect them yourself before submission. New runs reset their review fields to pending.

Before submission:

- Index the actual student handbook with `--pdf`, without `--max-pages`.
- Review `evaluation/results.json` and `evaluation/review.md` against the handbook.
  Regenerate the results whenever the document, questions, or retrieval code changes.
- Check answer accuracy and source pages manually; rerun unit tests.
- Include source code, requirements, this README, tests, and reviewed evaluation
  evidence. Ensure the assessor can obtain the input handbook (it is ignored by Git
  by default). Keep credentials, the virtual environment, model cache, and generated
  database out of the submission. Confirm the required Git/ZIP format in the brief.

## Code map

- `src/read_pdf.py`: PDF extraction, chunking, embeddings, and index-building CLI.
- `src/vector_store.py`: persistent ChromaDB storage and similarity retrieval.
- `src/search.py`: command-line retrieval demonstration.
- `src/rag.py`: Gemini answer generation and evidence validation.
- `src/api.py`: FastAPI JSON endpoints and request validation.
- `evaluate.py`: live question/answer/source report generator.

## Local files

Documents in `data/`, generated artifacts, vector stores, and `.env` files are
ignored by Git. The PDF remains available locally and will not be committed.
Keep API keys in a local `.env` file if a chosen provider requires them.

Do not rebuild the index while the API is serving questions. The single-document
refresh updates records in batches; it is not an atomic production deployment.

## Verification snapshot

The handbook index contains 39 chunks. Twenty local automated tests pass. Twelve
handbook questions were run through the real API code: ten factual topics and two
unsupported requests. The first run matched 11/12 expected outcomes. A later API
retest answered the curriculum question correctly; all original attempts are
retained in `evaluation/results.json`. See `evaluation/review.md` for the evidence
and limitations. This is not a guarantee of an Excellent rubric rating.

Retrieval also includes the cover/title page alongside the five closest chunks,
which helps answer document-identity questions such as the course name.
Restart an already-running API after source-code changes so it loads this version.
