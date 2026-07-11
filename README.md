# Heinz Admissions Assistant — Prototype (TM1)

An AI-enabled admissions information assistant for prospective students applying
to Carnegie Mellon University's Heinz College. It answers questions about
application requirements, deadlines, testing, English-language requirements, and
financial aid, grounded **only** in a small set of official Heinz College pages.

This is the **TM1 minimal working prototype**. It runs end-to-end with no
secrets (using a stubbed answer), and can generate grounded answers with Claude
when an API key is provided.

> **Team handoff:** [`docs/prototype-handoff.md`](docs/prototype-handoff.md)
> explains the prototype for the rest of the team — including whether it uses an
> LLM, the data/API contracts, and what each member needs to do next.

## What it does

`POST /ask` takes a question and returns:

```json
{
  "answer": "...",
  "sources": [{ "title": "...", "url": "https://www.heinz.cmu.edu/..." }],
  "support_status": "supported | unsupported | escalated",
  "escalation": "Please contact the Office of Admissions ...",
  "model": "stub | claude | policy"
}
```

Intended behaviour (per the project brief):

1. Accept a prospective student's question.
2. Search a small set of approved official Heinz content.
3. Send the retrieved context to a model (or the stub).
4. Return a grounded answer **with supporting source URLs**.
5. **Refuse** when no reliable source supports an answer (rather than inventing one).
6. **Escalate** applicant-specific / high-risk questions to a human representative.

## Architecture (data flow)

```
question ──▶ escalation check ──▶ retrieval ──▶ support gate ──▶ generation ──▶ answer + sources
             (applicant-specific?  (keyword      (relevant       (stub or        (grounded, cited,
              route to human)       scorer over   enough?         Claude)          or refusal)
                                    corpus.json)   else refuse)
```

- `data/corpus.json` — a few representative official Heinz pages, each tagged
  with its `source_url` (excerpted 2026-07-11).
- `app/retrieval.py` — simple, explainable keyword retriever (no embeddings yet).
- `app/generation.py` — swappable backends: `stub` (default, no secrets) and
  `claude` (Anthropic API).
- `app/pipeline.py` — the escalate → retrieve → gate → generate flow.
- `app/main.py` — FastAPI app: `POST /ask`, a minimal HTML page at `/`, `/health`.
- `app/cli.py` — command-line interface for quick testing.

## Clone and run

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the API
uvicorn app.main:app --reload
# open http://127.0.0.1:8000  (HTML form) or http://127.0.0.1:8000/docs
```

Ask via curl:

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Is the GRE required for Heinz College programs?"}'
```

Or via the CLI:

```bash
python -m app.cli "When is the application deadline?"
```

### Enabling the Claude backend (optional)

By default the prototype returns a stubbed (extractive) answer and needs no
secrets. To generate answers with Claude, copy `.env.example` to `.env` and set
`ANTHROPIC_API_KEY`. Configuration is read from environment variables — see
`.env.example` for all options. **No secrets are committed to the repository.**

## Tests

```bash
pytest
```

Covers retrieval ranking, the refuse and escalate paths, request validation,
and the `/health` check. Tests force the stub backend, so they need no API key.

## Scope boundaries

The assistant does **not** predict admission chances, compute admission
probabilities, give legal/immigration advice, guarantee financial aid, or make
claims unsupported by official sources. Such questions are refused or escalated.

## Status / AWS

TM1 is developed and run **locally** via the devcontainer. Nothing has been
deployed to or tested in AWS yet. The architecture is designed so the FastAPI
service can later be deployed into the AWS Academy Learner Lab; a ready-to-run
EC2 deployment (bootstrap script + console guide) is in
[`deploy/aws-ec2-guide.md`](deploy/aws-ec2-guide.md) for when a live demo is needed.
