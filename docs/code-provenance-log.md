# Code Provenance Log

Per the TM1 requirement and CMU's generative-AI policy, this log records what
was human-written vs. AI-generated, which tool produced it, the task/prompt
given, who reviewed it, and what changed on review.

## Summary (be honest about this)

The prototype was built in an **AI-assisted / agentic** workflow. A human team
member acted as **Operator** (direction, decisions, acceptance) and **Critic**
(review, testing); the coding agent produced the implementation.

- **Tool:** Claude Code, running Anthropic **Claude Opus 4.8**.
- **Human role (Member 4, `myurkunas`):** set the goals and scope, made the key
  decisions (EC2 over serverless; stub-by-default; keyword retrieval for TM1;
  which pages to ground the corpus in), reviewed all generated code for
  reasonableness and correct behavior, and verified functionality by running the
  test suite and manual API/CLI demos.
- **Agent role:** wrote essentially all of the application code, the seed corpus,
  the tests, the deployment artifacts, and the documentation, from the human's
  task descriptions.

In short: **almost all code in this repo is agent-generated and human-reviewed.**
No portion was written by hand from scratch.

## Review method

- **Read-through:** Member 4 reviewed each generated file for reasonableness and
  understood the logic (see `docs/prototype-handoff.md`, which explains it).
- **Automated tests:** `pytest` — 8 tests covering retrieval ranking, the
  refuse/escalate paths, request validation, and the health check — all passing.
- **Manual verification:** ran the FastAPI server and CLI and confirmed the four
  behaviors (supported answer + citation, refuse, escalate, health) by hand.

## Artifact-by-artifact log

| Artifact | Origin | Tool | Task given to the agent | Reviewed by | Review outcome |
|---|---|---|---|---|---|
| `app/main.py` | Agent-generated | Claude Code (Opus 4.8) | "FastAPI app exposing POST /ask, a minimal HTML page, and /health" | Member 4 | Reviewed, ran server, accepted |
| `app/schemas.py` | Agent-generated | Claude Code (Opus 4.8) | "Pydantic request/response models with answer, sources, support status, escalation" | Member 4 | Reviewed, accepted |
| `app/retrieval.py` | Agent-generated | Claude Code (Opus 4.8) | "Simple, explainable keyword retriever over the corpus (no embeddings for TM1)" | Member 4 | Reviewed; IDF weighting added after review of over-citation (see notes) |
| `app/generation.py` | Agent-generated | Claude Code (Opus 4.8) | "Swappable stub + Claude backends; grounded system prompt with scope rules" | Member 4 | Reviewed, accepted |
| `app/pipeline.py` | Agent-generated | Claude Code (Opus 4.8) | "escalate → retrieve → support gate → generate; refuse when unsupported" | Member 4 | Reviewed, accepted |
| `app/config.py` | Agent-generated | Claude Code (Opus 4.8) | "Env-var config; no secrets in code" | Member 4 | Reviewed, accepted |
| `app/cli.py` | Agent-generated | Claude Code (Opus 4.8) | "CLI for quick manual testing" | Member 4 | Reviewed, accepted |
| `data/corpus.json` | Agent-generated from official sources | Claude Code (Opus 4.8) + web fetch | "Ground a seed corpus in real official Heinz admissions pages" | Member 4 | Reviewed; **facts need a source spot-check** (see caveat) |
| `tests/` | Agent-generated | Claude Code (Opus 4.8) | "pytest for retrieval ranking, refuse/escalate, validation, health" | Member 4 | Reviewed, ran (8 passing) |
| `deploy/ec2-user-data.sh`, `deploy/aws-ec2-guide.md` | Agent-generated | Claude Code (Opus 4.8) | "EC2 bootstrap + Learner Lab console deployment guide" | Member 4 | Reviewed; executed and tested on EC2 in the Learner Lab (instance torn down when the lab session ended; redeployable via the guide) |
| `.devcontainer/devcontainer.json` | Agent-generated | Claude Code (Opus 4.8) | "Devcontainer so a teammate can clone and run" | Member 4 | Reviewed, accepted |
| `README.md`, `docs/prototype-handoff.md`, this log | Agent-generated | Claude Code (Opus 4.8) | "Run instructions, team handoff, provenance log" | Member 4 | Reviewed, accepted |

## Member 2 — dataset & retrieval corpus (replaces the seed corpus)

Member 2 (`lindberg.simpsoniii`) owns the approved-source data. The **6-document
seed `corpus.json`** written by Member 4 has been **replaced** by Member 2's vetted
corpus (32 official Heinz/CMU pages → 107 chunks) via the pipeline in
`data/sources/`. Human role: Member 2 acted as Operator/Critic — chose the approved
sources, curated each page to exclude out-of-scope content (visa/immigration,
niche accelerated-partnership sections), spot-checked facts against the live URLs,
and ran the verification gates. Tool: Claude (Cowork), Claude Opus 4.8.

| Artifact | Origin | Tool | Task given to the agent | Reviewed by | Review outcome |
|---|---|---|---|---|---|
| `data/sources/raw_pages/*.txt` (32) | Agent-curated from official sources | Claude (Cowork, Opus 4.8) + web fetch | "Clean each approved Heinz/CMU page to on-scope main-content text" | Member 2 | Reviewed; passes `verify_text.py` (no boilerplate/truncation) |
| `data/sources/sources_manifest.json` | Agent-generated | Claude (Cowork) | "Single source of truth: url/title/scope/topic/version per document" | Member 2 | Reviewed, accepted |
| `data/sources/heinz_admissions_approved_sources.csv` | Agent-generated | Claude (Cowork) + web fetch | "Approved-source registry with change-frequency + content-version" | Member 2 | Reviewed; links verified against live sites |
| `data/sources/{clean_page,build_chunks,verify_text,verify_dataset}.py` | Agent-generated | Claude (Cowork) | "Reproducible clean → chunk → verify pipeline (stdlib only)" | Member 2 | Reviewed, ran; gates pass |
| `data/sources/chunks.csv` | Generated by `build_chunks.py` | Claude (Cowork) | "Chunk raw pages (~700 chars, overlap) with source metadata" | Member 2 | Reviewed; 107 chunks, sizes/dupe/boilerplate checks pass |
| `data/sources/build_corpus.py` | Agent-generated | Claude (Cowork) | "Convert chunks.csv → data/corpus.json in the app's Document schema" | Member 2 | Reviewed, accepted |
| `data/corpus.json` | Generated by `build_corpus.py` from Member 2's dataset | Claude (Cowork) | "Replace the 6-doc seed with the vetted 107-chunk corpus" | Member 2 | Reviewed; app + tests run against it |
| `tests/test_retrieval.py`, `tests/test_ask.py` | Agent-updated | Claude (Cowork) | "Make seed-specific assertions robust to the new corpus" | Member 2 | Reviewed; `pytest` 9 passing |

## Notable AI-assisted iterations (review changed the code)

- **Retrieval quality:** the first keyword scorer cited unrelated pages because
  common words ("Heinz", "College") appear in most documents. After reviewing the
  output, the scorer was changed to **IDF-weighted** matching plus a
  **relative citation cutoff**, so only genuinely relevant sources are cited.
- **Fallback wording (open item):** the refusal text in `pipeline.py` does **not**
  yet match Member 1's specified fallback line. Flagged for alignment; the code
  will be updated once Member 1 confirms the canonical string. (See
  `docs/prototype-handoff.md` §7.)

## Accuracy caveat

The corpus text was extracted by the agent from official Heinz/CMU pages fetched
on **2026-07-11** and reviewed by Member 2 against the live source URLs. Two
program how-to-apply pages (MSPPM, MEIM, MAM) still showed the **August 2026**
admissions cycle at time of access while other programs showed August 2027; these
are captured **as published** and flagged in each document's `content_version`.
High-change facts (tuition, deadlines) should be refreshed each cycle — this is
the source-freshness work planned for TM2.

## Keeping this log current

Add a row whenever new code or content is generated: record origin
(agent/human), tool, the task/prompt, the reviewer, and what changed on review.
Other members should add their own review sign-off (e.g., Member 1 on the
governance strings, Member 3 on the architecture) as they verify their areas.
