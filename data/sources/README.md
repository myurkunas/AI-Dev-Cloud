# Heinz Admissions RAG — Cleaned Dataset (Member 2)

The cleaned, source-grounded corpus for the retrieval-based admissions assistant.
All text is extracted from approved, publicly available Heinz/CMU pages listed in
`../heinz_admissions_approved_sources.csv` (the approved-source registry).

## Contents
- `sources_manifest.json` — **single source of truth**: for each document, its
  filename, source URL, title, scope, topic, content version, and change frequency.
- `raw_pages/` — 32 cleaned main-content text files (nav/menus/footers stripped).
- `clean_page.py` — reusable rule-based boilerplate remover (the reproducible
  cleaning step).
- `verify_text.py` — Phase 1 gate: checks each raw page is clean/complete/logical.
- `build_chunks.py` — normalizes + chunks raw pages into `chunks.csv` using the manifest.
- `verify_dataset.py` — Phase 2 gate: dataset checks + retrieval sanity test.
- `chunks.csv` — the retrieval dataset (**107 chunks from 32 sources**).

## Pipeline
`webpage → extract main text → clean (strip nav/footer) → verify_text →
chunk (~700 chars, sentence-aware overlap) → verify_dataset → [embed → vector store → retrieve]`

Each chunk carries `source_url`, `source_title`, `content_version`, and
`date_accessed`, so every answer can cite its source page and that page's freshness.

### chunks.csv columns
`chunk_id, source_id, source_title, source_url, scope, topic, content_version,
change_frequency, date_accessed, char_count, token_estimate_approx, text`

## Sources ingested (32)
Grouped by category, spanning every in-scope question type:
- **General admissions (12):** admissions home, admissions FAQ, general/curriculum
  FAQ, financial-aid FAQ, transcripts, recommendations, video interview, English
  proficiency, connect-with-us, contact, partner scholarships, programs index.
- **Tuition & aid (4):** SFS graduate tuition, SFS cost of attendance, AIM
  financial aid, CMU graduate funding.
- **CMU policy/calendar (2):** CMU prospective-graduate policy, CMU academic calendar.
- **Program overviews (7):** AIM, MISM, MSPPM, MSISPM, MSHCA, MAM, MEIM (format/duration).
- **Program how-to-apply (7):** AIM, MISM, MSPPM, MSISPM, MSHCA, MAM, MEIM (deadlines,
  prerequisites, GRE/GMAT policy).

This covers **all seven full-time master's programs**. Not yet ingested (same URL
patterns exist in the registry, can be added the same way) and out of the current
full-time-master's scope: the part-time programs (MPM, online MSIT, MMM) and the
PhD programs — these have materially different rules (work-experience requirements,
non-fall starts, Dec 1-only PhD deadline), so add them only if the service is scoped
to answer for those applicants.

## Cleaning method (hybrid)
- `clean_page.py` is the reproducible rule-based cleaner and is used for the large
  program pages that the fetch tool saves to disk.
- The remaining pages were **curated** (extracted by hand from the fetched content)
  for two reasons: (1) to exclude out-of-scope material — visa/immigration notes and
  niche accelerated-partnership sections (Ajou, ESAN, VinUniversity, etc.) — per the
  team's no-international-advice scope, and (2) to reduce redundancy, since the six
  program how-to-apply pages share large blocks of identical boilerplate.
- All 30 files pass `verify_text.py` (no boilerplate, no truncation, all matched to
  the manifest).

## Verification results
- **Text gate:** 32/32 raw pages clean; no boilerplate/nav/link tokens; none truncated.
- **Chunk gate:** 107 chunks; sizes min 239 / median 563 / max 952 chars; no empty
  or duplicate chunks; complete metadata; all https. Two near-duplicate pairs remain
  (MAM ~ MEIM how-to-apply) — expected, since both are GRE-optional programs sharing
  near-identical QSSP/deadline wording; the `scope` metadata distinguishes them.
- **Retrieval sanity:** correct source returned for the straightforward factual
  questions (tuition, GRE, TOEFL, fee, recommendations, scholarships, contacts,
  program length/deadlines for a named program).

## Findings for the team (retrieval design)
These are design requirements surfaced by testing, not data defects:
1. **Program disambiguation.** Program overview/how-to-apply pages are near-identical
   on deadline wording, so a keyword search can return the wrong *program* (e.g., an
   "AI program deadlines" query matched the MAM overview). The workflow's
   "classify intent/program → retrieve" step must filter by the `scope` (program)
   metadata that every chunk carries.
2. **Comparative questions** ("difference between MISM and MSHCA") need multi-document
   retrieval; a single top-1 chunk scores low.
3. **Escalation cannot rely on a score threshold.** Applicant-specific questions
   ("will I get in with a 3.2 GPA?", "review my resume") still retrieve plausible
   chunks at moderate scores. An intent classifier/guardrail (Member 1's escalation
   policy) must route these to a human.
4. **Freshness/versioning.** The MSPPM and MAM how-to-apply pages still showed the
   August 2026 cycle at time of access while other programs showed August 2027 —
   captured as published and flagged in `content_version`. High-change sources
   (tuition, deadlines) need a refresh strategy (Week 5).

## Scope note
The English-proficiency page (08) is retained because the team's scope lists
English-language requirements as in-scope; it is the one international-adjacent page,
and its text explicitly notes the assistant answers the requirement but does not give
visa/immigration advice.

## Regenerate
```
python3 clean_page.py       # (optional) re-clean disk-saved pages into raw_pages/
python3 verify_text.py      # Phase 1 gate: raw page quality
python3 build_chunks.py     # rebuild chunks.csv from raw_pages/ + manifest
python3 verify_dataset.py   # Phase 2 gate: dataset checks + retrieval sanity test
```
