"""The ask pipeline: escalate -> retrieve -> gate -> generate.

This is the heart of the prototype's intended behaviour:
1. Escalate applicant-specific / high-risk questions to a human.
2. Retrieve relevant official passages.
3. If nothing is relevant enough, refuse rather than invent an answer.
4. Otherwise generate a grounded answer and return supporting sources.
"""

import re

from . import config, generation
from .retrieval import RetrievedPassage, Retriever
from .schemas import AskResponse, Source, SupportStatus

CONTACT = "hnzadmit@andrew.cmu.edu or 412-268-2164"
ESCALATION_MESSAGE = (
    f"Please contact the Heinz College Office of Admissions directly at {CONTACT}."
)

# Applicant-specific or high-risk questions we must not answer ourselves.
_ESCALATION_PATTERNS = [
    r"\bmy chances\b",
    r"\bwill i (get|be) (in|admitted|accepted)\b",
    r"\b(chance|odds|probabilit)\w*\b.*\b(admit|accept|get in)\w*\b",
    r"\bget(ting)? (in|admitted|accepted)\b",
    r"\bimmigration\b",
    r"\bvisa\b",
    r"\blegal\b",
    r"\bguarantee\b",
    r"\breview my\b",
]


def needs_escalation(question: str) -> bool:
    q = question.lower()
    return any(re.search(pattern, q) for pattern in _ESCALATION_PATTERNS)


def _sources(passages: list[RetrievedPassage]) -> list[Source]:
    """Deduplicate sources by URL, preserving rank order."""
    seen: set[str] = set()
    sources: list[Source] = []
    for p in passages:
        url = p.document.source_url
        if url not in seen:
            seen.add(url)
            sources.append(Source(title=p.document.title, url=url))
    return sources


def answer(question: str, retriever: Retriever, backend: str | None = None) -> AskResponse:
    question = question.strip()

    if needs_escalation(question):
        return AskResponse(
            answer=(
                "This looks like an applicant-specific or high-risk question. "
                "A Heinz admissions representative is the right person to help."
            ),
            sources=[],
            support_status=SupportStatus.escalated,
            escalation=ESCALATION_MESSAGE,
            model="policy",
        )

    passages = retriever.search(question)
    # Keep only passages that clear the absolute floor AND are close to the best
    # match, so we don't cite weakly-related documents just because they made
    # the top-k or happen to share common words.
    top_score = passages[0].score if passages else 0.0
    cutoff = max(config.SUPPORT_THRESHOLD, top_score * config.SUPPORT_RATIO)
    relevant = [p for p in passages if p.score >= cutoff]
    supported = bool(relevant)

    if not supported:
        return AskResponse(
            answer=(
                "I don't have reliable information from official Heinz College "
                "sources to answer that."
            ),
            sources=[],
            support_status=SupportStatus.unsupported,
            escalation=ESCALATION_MESSAGE,
            model="policy",
        )

    backend = backend or generation.select_backend()
    if backend == "claude":
        text = generation.claude_generate(question, relevant)
        if text is None:  # model declined — fall back to a safe refusal
            return AskResponse(
                answer=(
                    "I'm not able to answer that. Please reach out to the "
                    "Office of Admissions."
                ),
                sources=[],
                support_status=SupportStatus.unsupported,
                escalation=ESCALATION_MESSAGE,
                model="claude",
            )
    else:
        text = generation.stub_generate(question, relevant)

    return AskResponse(
        answer=text,
        sources=_sources(relevant),
        support_status=SupportStatus.supported,
        escalation=None,
        model=backend,
    )
