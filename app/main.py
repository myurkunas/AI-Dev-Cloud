"""FastAPI entry point.

Exposes:
- GET  /          a bare-bones HTML form to try the assistant
- POST /ask       the JSON API described in the project brief
- GET  /health    a liveness check

Run locally:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from . import generation, pipeline
from .retrieval import get_retriever
from .schemas import AskRequest, AskResponse

app = FastAPI(
    title="Heinz Admissions Assistant",
    description="TM1 prototype: grounded Q&A over official Heinz admissions content.",
    version="0.1.0",
)

# Load the corpus once at startup and reuse the retriever across requests.
retriever = get_retriever()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "documents": len(retriever.documents), "backend": generation.select_backend()}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    return pipeline.answer(request.question, retriever)


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Heinz Admissions Assistant (TM1 prototype)</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; }
    textarea { width: 100%; }
    pre { background: #f4f1ea; padding: 1rem; white-space: pre-wrap; }
    .muted { color: #666; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h1>Heinz Admissions Assistant</h1>
  <p class="muted">TM1 prototype. Answers are grounded in a small set of official
  Heinz College pages. Applicant-specific questions are routed to a human.</p>
  <form id="f">
    <textarea id="q" rows="3" placeholder="Is the GRE required for Heinz College programs?"></textarea>
    <p><button type="submit">Ask</button></p>
  </form>
  <pre id="out"></pre>
  <script>
    document.getElementById('f').addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = document.getElementById('q').value;
      const out = document.getElementById('out');
      out.textContent = 'Asking...';
      const res = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      out.textContent = JSON.stringify(await res.json(), null, 2);
    });
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML
