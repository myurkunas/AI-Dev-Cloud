# Scope, Users, and Governance: Heinz Admissions Assistant

---

## 1. Problem Statement

Prospective Heinz College applicants need answers to a narrow, repetitive set of admissions questions: deadlines, required materials, testing requirements, English-language proficiency, tuition, and program length. Those answers exist, but they are spread across dozens of Heinz and CMU pages, they differ by program, and they change between admissions cycles. Applicants either spend real time reconciling sources, act on a page that does not apply to their program, or email the Office of Admissions with questions the website already answers.

The failure mode that matters here is not slowness. It is confident wrongness. An applicant who acts on a stale deadline or another program's requirement is worse off than one who found nothing at all. A general-purpose chatbot makes this worse, because it produces fluent answers with no traceable source.

We are building an AI-enabled admissions information service that helps prospective Heinz College students find accurate, source-grounded answers about applications, requirements, deadlines, costs, and programs, using approved publicly available CMU and Heinz webpages.

The service is API-first. It retrieves from an approved source set, grounds every answer in what it retrieved, cites the pages that support the answer, refuses when no approved source supports one, and routes applicant-specific questions to a human. The chat interface is the presentation layer, not the system.

---

## 2. Target User

The primary user is the prospective Heinz College applicant: someone considering or preparing an application to a Heinz graduate program. They are outside CMU, unauthenticated, and cannot be assumed to know Heinz's program structure or vocabulary.

Four sub-cases shape the requirements:

- **Domestic applicant.** The baseline case. Deadlines, materials, testing, tuition.
- **International applicant.** Adds English-language requirements. This is also the user most likely to ask visa and immigration questions, which the system must refuse.
- **Applicant comparing Heinz programs.** Needs program-scoped answers rather than Heinz-wide ones. Most exposed to the risk of one program's rule being presented as universal.
- **Career-changer or non-traditional applicant.** Asks eligibility questions that shade into "would I be competitive?", which is the escalation boundary.

The Office of Admissions is a secondary stakeholder-as-user. They are not a questioner, but they are affected by every answer. The system helps them if it deflects volume on answerable questions and hands off cleanly on the rest. It hurts them if it says something wrong in their name.

Not users at TM1: current students, faculty, staff, and applicants to CMU colleges other than Heinz. The corpus does not cover them, so the system refuses rather than improvises.

---

## 3. Main Use Cases

| # | Use case | Example question | Expected behavior |
|---|---|---|---|
| UC1 | Deadline lookup | "When is the application deadline?" | Grounded answer with source link. If deadlines are program-specific, say so rather than picking one. |
| UC2 | Required materials | "What do I need to submit?" | Grounded, itemized, cited. |
| UC3 | Standardized testing | "Is the GRE required?" | Grounded and cited. Must not generalize one program's policy to all. |
| UC4 | English-language requirements | "Do I need TOEFL if my degree was taught in English?" | Grounded and cited. If the approved sources do not resolve the conditional, refuse. This is a common hallucination trap. |
| UC5 | Tuition and cost | "How much is tuition?" | Grounded and cited, preserving the source's own scoping (per-year, per-unit, per-program). |
| UC6 | Program format and length | "How long is the MSPPM program?" | Grounded and cited. |
| UC7 | Admissions contacts | "Who do I contact about my application?" | Official contact information. |
| UC8 | Refusal | "What is the average GRE score of admitted students?" | Fallback language (Section 7). No guess, no "typically." |
| UC9 | Escalation | "What are my chances?" or "Can you review my résumé?" | Routed to a human. No partial answer. |

UC8 and UC9 are real use cases, not error paths. A system that never refuses has not been tested.

---

## 4. In Scope and Out of Scope

### In scope: answered when an approved source supports it

- Application deadlines
- Required application materials
- Standardized testing requirements and waivers, as published
- English-language proficiency requirements
- Program prerequisites and stated eligibility criteria
- Tuition and published costs
- Financial aid information: what exists, how to apply, published deadlines
- Program format, length, and delivery mode
- Admissions office contact information
- Published, factual differences between Heinz programs

### Out of scope: not answered, even when asked directly

| Category | Why | Disposition |
|---|---|---|
| Predicting admission ("Will I get in?", "What are my chances?", "What are my odds?") | The system has no admissions-decision data. Any number or reassurance would be fabricated. | Escalate |
| Evaluating an applicant's materials (résumé, essay, transcript, "review my...") | Same reason. It also invites users to paste personal data into a public endpoint. | Escalate |
| Immigration, visa, and legal advice | Regulated advice with real consequences. Not ours to give at any confidence level. | Escalate |
| Financial aid guarantees ("Will I get funding?") | Distinct from published aid information, which is in scope. Describing the aid landscape is in scope; promising an individual an outcome is not. | Escalate |
| Anything not supported by an approved source | The catch-all, and the most important rule. Coverage gaps must surface as refusals, not as plausible prose. | Refuse |
| Non-Heinz CMU colleges; current-student questions | Outside the corpus. | Refuse |

The controlling rule: if an approved source does not support it, the system does not say it. Every other out-of-scope rule is a special case of this one.


### For in-scope questions, the system is trustworthy if:

1. **Every substantive claim is traceable.** Each answer returns at least one approved source URL, and that page actually supports the claim.
2. **It refuses rather than guesses.** If no supporting passage is found, the system returns the fallback language rather than a hedged partial answer.
3. **It escalates rather than assesses.** Applicant-specific questions are routed to a human with no attempted answer.
4. **Program scope is preserved.** One program's rule is never presented as a Heinz-wide fact.

A wrong-but-cited answer is a corpus problem. A confident answer with no citation is a governance problem. We treat them differently.

---

## 5. Stakeholders

| Stakeholder | What they need from the system |
|---|---|
| Prospective applicant (primary user) | Correctness over fluency, and a visible path to a human when the system cannot help. |
| Heinz Office of Admissions | Nothing unsourced said in their name, clean escalation, and correct contact details. They bear the cost of every wrong answer the system gives. |
| Heinz College and CMU (institutional) | Answers that never contradict official pages, and a clear posture that this is an unofficial aid rather than an official channel. |
| Project team (Members 1 to 4) | A stable scope that does not drift mid-sprint. |
| Course instructor | Evidence of scope, architecture, and governance reasoning. |

Note: the system directs users to the Office of Admissions by name, email, and phone. For TM1 this is a local classroom prototype and is not publicly deployed, so no approval was sought. Before any public deployment, the Office of Admissions should be told that a system is routing users to them.

---

## 6. Risks and Safeguards

| # | Risk | Consequence | Safeguard |
|---|---|---|---|
| R1 | Hallucination: the model invents a deadline, fee, or requirement. | The applicant misses a deadline or submits the wrong materials. This is the highest-severity risk in the system. | A support gate sits between retrieval and generation. Retrieved passages must clear a score floor and be close to the best match before anything is cited. If none pass, the system refuses instead of generating. Generation is instructed to use only the retrieved passages. |
| R2 | Cross-program contamination: one program's rule is presented as universal. | Silent, plausible, and hard for the applicant to catch. This is the most likely wrong-answer mode. | Corpus chunks carry program and scope metadata, and answers must preserve source scoping. Mitigation is only partial at TM1, because keyword retrieval is not program-aware. Program-aware retrieval is a TM2 requirement. |
| R3 | Staleness: deadlines and tuition change, but the corpus does not. | A cited, well-formed, confidently wrong answer. | Every corpus entry records its source URL and retrieval date. There is no freshness check at TM1; the corpus is a point-in-time snapshot. Freshness monitoring is a TM2 requirement. |
| R4 | Over-collection of personal data: users paste résumés or transcripts into a public endpoint. | Sensitive data captured in logs. | Escalation triggers on "review my..." intercept the main vector, and the system never asks for personal information. No logging exists yet, so a redaction decision must be made before TM2 adds it. |
| R5 | Authority confusion: the user treats output as an official ruling. | The applicant trusts the assistant over the official page. | The service is positioned as an information aid, not an official channel. Every answer carries source links, so the authoritative page is one click away. Refusals and escalations both name a human contact. |
| R6 | Scope creep: "just let it also do X." | Governance boundaries erode until the system is a general chatbot again. | This document is canonical. Scope changes are amended here first and implemented second. |

---

## 7. Human-Escalation Policy

### Principle

Escalation is not a failure state. It is the correct answer to questions the system is structurally unable to answer: not because it lacks data today, but because answering would require judgment it does not have and must not simulate. No amount of corpus expansion moves these questions into scope.

### Triggers

A question is escalated when it asks the system to:

1. Predict an admissions outcome: chances, odds, probability, "will I get in / accepted / admitted."
2. Evaluate an individual's materials or profile: "review my...", résumé, essay, transcript, competitiveness.
3. Give immigration, visa, or legal advice.
4. Guarantee an outcome: admission, funding, financial aid, or a scholarship.

### Behavior on escalation

- The system does not partially answer. There is no "I cannot say for sure, but generally...", because a hedged assessment is still an assessment.
- No answer content is returned. The escalation message is returned instead.
- Escalation is checked before retrieval, so an applicant-specific question is never answered even if the corpus happens to contain relevant-looking text.
- The named human contact is the Heinz College Office of Admissions.

### Escalation compared with refusal

| | Refusal | Escalation |
|---|---|---|
| What it means | "The approved sources do not cover this." | "This is not answerable by a system, by design." |
| Fixable by | Expanding the corpus. | Nothing. It stays out of scope. |
| Example | "What is the average admitted GPA?" | "What are my chances of getting in?" |

### System language

Fallback and refusal:

> I don't have reliable information from official Heinz College sources to answer that. Please contact the Heinz College Office of Admissions directly at hnzadmit@andrew.cmu.edu or 412-268-2164.

Escalation:

> Please contact the Heinz College Office of Admissions directly at hnzadmit@andrew.cmu.edu or 412-268-2164.
