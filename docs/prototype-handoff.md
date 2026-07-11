# Prototype Handoff — Heinz Admissions Assistant (TM1)

Owner: **Member 4 (prototype / code).**
Audience: the rest of the team, so you can build your parts against what the
code actually does — and know exactly what the code needs *from* you.

## Who should read what

| You are… | Read | Why |
|---|---|---|
| **Member 1** (scope & governance) | §7 Behavior rules in code | The refusal text, escalation triggers, and scope boundaries are hard-coded — align your written policy with them (and flag the one wording mismatch below). |
| **Member 2** (data & retrieval) | §8 Data contract | The exact JSON format the code reads, and how to swap your dataset in without touching code. |
| **Member 3** (architecture & docs) | §9 Architecture inputs | Components, tech choices, data flow, tradeoffs, and deployment — raw material for your diagram + narrative. |
| Everyone | §1–§6 | What it is, whether it uses an LLM, how to run/test it. |

---

## 1. What this is and its current status

An API-first assistant that answers prospective-student questions about Heinz
College admissions, grounded only in approved official Heinz/CMU content, with
source citations, refusals when unsupported, and escalation of applicant-specific
questions to a human.

**Status:** runnable end-to-end locally. Runs with **no secrets** by default.
Not yet deployed to AWS (a ready-to-run EC2 deployment is prepared but not
executed — see §9).

## 2. Does it use an LLM?

**It can, but by default it doesn't.** The answer-writing step has two swappable
backends, chosen automatically:

| Backend | When it's used | What it does |
|---|---|---|
| `stub` (default) | No `ANTHROPIC_API_KEY` set | **No LLM, no network.** Returns the top retrieved official passage *verbatim*, with a note that the model isn't connected. Extractive, not generative. |
| `claude` | `ANTHROPIC_API_KEY` is set | Sends the retrieved passages to Anthropic's Claude (`claude-opus-4-8`) to write a grounded answer. |

**Important:** *everything except the final wording is real even in stub mode* —
question intake, retrieval, source citations, refusal, and escalation all run for
real. Only "phrase a fluent answer from the passages" is stubbed. This is
explicitly allowed for TM1 ("return a stubbed response if the model … is not
connected yet") and lets anyone run the project with zero setup. Switching to a
real LLM is one environment variable — no code change.

## 3. Clone, run, test

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://127.0.0.1:8000  (form) or /docs
pytest                             # 8 tests, no API key needed
python -m app.cli "When is the application deadline?"   # CLI
```

Full instructions and the optional Claude setup are in the top-level `README.md`.

## 4. Repository map

```
app/
  main.py        FastAPI app: POST /ask, GET / (HTML form), GET /health
  schemas.py     Pydantic request/response models (the API contract)
  pipeline.py    The core flow: escalate -> retrieve -> gate -> generate
  retrieval.py   IDF-weighted keyword retriever over the corpus
  generation.py  Backends: stub (default) and claude; backend selection
  config.py      All settings, read from environment variables
  cli.py         Command-line interface
data/
  corpus.json    The approved-content dataset (Member 2 owns this — see §8)
tests/           pytest suite (retrieval, refuse/escalate, validation, health)
deploy/          EC2 bootstrap script + Learner Lab console guide (§9)
docs/            This document
```

## 5. API contract (`POST /ask`)

Request:
```json
{ "question": "Is the GRE required for Heinz College programs?" }
```
(`question` is required, min length 1; an empty question returns HTTP 422.)

Response:
```json
{
  "answer": "…",
  "sources": [{ "title": "…", "url": "https://www.heinz.cmu.edu/…" }],
  "support_status": "supported | unsupported | escalated",
  "escalation": "Please contact the Office of Admissions …" ,   // null when answered
  "model": "stub | claude | policy"                              // which generator ran
}
```

`support_status` meaning: `supported` = grounded answer with citations;
`unsupported` = refused (no reliable source); `escalated` = routed to a human.

## 6. How it works end to end (`pipeline.py`)

```
question
  │
  ├─▶ 1. Escalation check ── matches an applicant-specific/high-risk pattern? ─▶ ESCALATED (model="policy")
  │
  ├─▶ 2. Retrieve ── score every corpus doc by IDF-weighted keyword overlap
  │
  ├─▶ 3. Support gate ── keep docs scoring ≥ max(SUPPORT_THRESHOLD, top×SUPPORT_RATIO)
  │        └─ none pass? ─▶ UNSUPPORTED / refuse (model="policy")
  │
  └─▶ 4. Generate ── stub or claude writes the answer from the kept passages ─▶ SUPPORTED + sources
```

Step 3 is what keeps citations honest: a doc is only cited if it clears an
absolute floor *and* is close to the best match, so common words like "Heinz"
don't drag unrelated pages into the answer.

## 7. Behavior rules currently encoded in code — **Member 1, align these**

These are governance decisions that live in the code today. Member 1 owns the
written policy; please confirm the code matches your intended wording/rules, and
tell me what to change.

- **Refusal (unsupported) message**, in `pipeline.py`:
  > "I don't have reliable information from official Heinz College sources to
  > answer that."  + "Please contact the Heinz College Office of Admissions
  > directly at hnzadmit@andrew.cmu.edu or 412-268-2164."

  ⚠️ **Mismatch to resolve:** Member 1's spec gives the exact fallback line as
  *"I could not verify that answer from the approved Heinz College sources.
  Please contact Heinz Admissions."* The code currently uses different wording.
  **Decide on one canonical string and I'll update the code to match.**

- **Escalation triggers** (`_ESCALATION_PATTERNS` in `pipeline.py`): questions
  matching phrases like *my chances*, *will I get in/admitted/accepted*,
  *odds/probability of admission*, *immigration*, *visa*, *legal*, *guarantee*,
  *review my …* are routed to a human without being answered. Member 1: is this
  the right list? Add/remove phrases as your escalation policy dictates.

- **Scope boundaries** are also written into the Claude system prompt in
  `generation.py` (no admission prediction, no legal/immigration advice, no aid
  guarantees, no unsourced claims). These should mirror Member 1's in/out-of-scope
  definition — worth a cross-check.

## 8. Data contract (the corpus) — **Member 2, this is your target format**

`data/corpus.json` is a JSON **array of documents**. The code reads these fields:

```json
{
  "id": "standardized-testing",          // required, unique slug
  "title": "Standardized testing (GRE/GMAT) requirements",  // required; shown as the citation title
  "source_url": "https://www.heinz.cmu.edu/…",              // required; the cited URL
  "text": "The GRE or GMAT is required for …",              // required; the content that gets searched & returned
  "retrieved": "2026-07-11"              // optional; date accessed
}
```

**How to hand off your dataset:** deliver a `corpus.json` in this shape (or point
`CORPUS_PATH` at your file). Then it just works — no code change.

- **Extra columns are safe.** You can add `topic`, `scope` (program-specific vs
  general), `volatile` (changes-frequently flag), etc. from your source
  spreadsheet — the loader ignores fields it doesn't use, so your richer tracking
  sheet can export straight into this file.
- The current file has **6 seed docs** I wrote to unblock the prototype; treat it
  as a placeholder to **replace** with your ~10–20 vetted pages.
- **Retrieval today is keyword-based (IDF), not embeddings.** Your "webpage →
  text → chunks → embeddings → vector store" pipeline is the TM2/TM3 upgrade. The
  `Retriever` class in `retrieval.py` is the single swap point — a future
  embedding retriever can replace it behind the same `search()` interface without
  touching the rest of the app.

## 9. Architecture inputs — **Member 3, raw material for your diagram/narrative**

**Components (current):**
- **Interface:** minimal HTML form + `POST /ask` JSON API + CLI (API-first).
- **Backend:** FastAPI (Python), Pydantic for validated request/response.
- **Retrieval:** in-process IDF keyword retriever over `corpus.json`.
- **Knowledge source:** curated official Heinz/CMU content (`data/corpus.json`).
- **Generation:** pluggable — stub (default) or Claude via the Anthropic API.
- **Governance in-line:** escalation + refusal + scope rules in `pipeline.py`.

**Data flow:** `user → HTML/API → FastAPI → escalation check → retrieval →
support gate → generation (stub/Claude) → answer + source citations`, with an
**escalation path** to the Office of Admissions when unsupported or high-risk.

**Technology choices & why (one-liners):**
- *FastAPI* — API-first, async, auto OpenAPI docs at `/docs`; matches the course's API-first emphasis.
- *Pydantic* — enforces the request/response contract (structured output).
- *Keyword/IDF retrieval for TM1* — simple and explainable; embeddings deferred to avoid overbuilding.
- *Swappable model layer* — runs with zero secrets (stub) yet upgrades to Claude via one env var; keeps secrets in env, not code.
- *Env-var config* — secrets/configuration outside the repo (`.env`, gitignored).

**Key tradeoffs to write up:**
- Keyword vs. embedding retrieval (simplicity/explainability now vs. semantic recall later).
- Stub vs. LLM (reproducible/free/testable vs. fluent generative answers + cost/nondeterminism).
- Extractive vs. generative answers in stub mode.

**Deployment (prepared, not executed):** single **EC2** instance on **Amazon
Linux 2023**, app run by a **systemd** service via **uvicorn**, provisioned by a
**user-data** bootstrap that clones the repo and installs dependencies. See
`deploy/aws-ec2-guide.md` and `deploy/ec2-user-data.sh`. Notes for the diagram:
AWS hosting = EC2; storage = the corpus file on the instance (S3/vector DB is a
TM2/TM3 evolution); secrets = `ANTHROPIC_API_KEY` via env/systemd (never in repo);
logging = cloud-init + systemd/journal today. Learner Lab is ephemeral, so this
is a demo-on-demand deployment, not a persistent host.

## 10. Configuration (all via environment variables, `config.py`)

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(unset)* | Enables the Claude backend when set. |
| `ANTHROPIC_MODEL` | `claude-opus-4-8` | Model id for the Claude backend. |
| `GENERATION_BACKEND` | `auto` | `auto` (Claude if key present, else stub), `stub`, or `claude`. |
| `TOP_K` | `3` | Max passages retrieved per question. |
| `SUPPORT_THRESHOLD` | `1.0` | Absolute score floor for an answer to count as supported. |
| `SUPPORT_RATIO` | `0.5` | A passage is only cited if its score ≥ this fraction of the top score. |
| `CORPUS_PATH` | `data/corpus.json` | Path to the corpus file. |

See `.env.example`. Nothing secret is committed to the repo.

## 11. Known limitations & where TM2/TM3 extend it

- Keyword retrieval (no semantic/embedding search yet) — swap `Retriever`.
- No chunking; each corpus entry is one passage — fine for a small corpus.
- No logging/metrics, evaluation suite, or source-freshness checks yet (TM2).
- Corpus is a hand-curated seed of 6 pages (Member 2 replaces/expands).
- Stub mode answers are extractive quotes, not generated prose.

## 12. Open items / decisions needed

1. **Member 1:** confirm the canonical refusal/fallback wording (see the mismatch
   in §7) and the escalation trigger list — then I'll update the code.
2. **Member 2:** deliver the vetted `corpus.json` (§8 format) to replace the seed.
3. **Member 3:** the §9 inputs feed your diagram + narrative; ask me for any
   detail you need.
