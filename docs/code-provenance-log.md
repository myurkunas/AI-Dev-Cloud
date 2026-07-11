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
| `deploy/ec2-user-data.sh`, `deploy/aws-ec2-guide.md` | Agent-generated | Claude Code (Opus 4.8) | "EC2 bootstrap + Learner Lab console deployment guide" | Member 4 | Reviewed; not yet executed in AWS |
| `.devcontainer/devcontainer.json` | Agent-generated | Claude Code (Opus 4.8) | "Devcontainer so a teammate can clone and run" | Member 4 | Reviewed, accepted |
| `README.md`, `docs/prototype-handoff.md`, this log | Agent-generated | Claude Code (Opus 4.8) | "Run instructions, team handoff, provenance log" | Member 4 | Reviewed, accepted |

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

The seed corpus text was condensed by the agent from official Heinz/CMU pages
fetched on **2026-07-11**. Facts (deadlines, score-age limits, dollar figures)
should be **spot-checked against the live source URLs** before relying on them —
this is part of Member 2's data-ownership review.

## Keeping this log current

Add a row whenever new code or content is generated: record origin
(agent/human), tool, the task/prompt, the reviewer, and what changed on review.
Other members should add their own review sign-off (e.g., Member 1 on the
governance strings, Member 3 on the architecture) as they verify their areas.
