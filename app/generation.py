"""Answer generation backends.

Two backends produce an answer string from the retrieved passages:

- "stub":   deterministic, no network. Returns the most relevant official
            passage verbatim. Lets the whole workflow run with zero secrets.
- "claude": calls the Anthropic API to write a grounded answer from the
            passages. Used only when ANTHROPIC_API_KEY is configured.

Both are given the same passages; the pipeline decides which to call.
"""

from . import config
from .retrieval import RetrievedPassage

# Instructions for the Claude backend. Encodes the brief's scope boundaries.
SYSTEM_PROMPT = """You are the Heinz College Admissions Assistant for prospective students.

Answer ONLY using the official CMU/Heinz source passages provided in the user \
message. Follow these rules:
- Ground every claim in the provided passages. Do not use outside knowledge.
- If the passages do not contain the answer, say you don't have reliable \
information and suggest contacting the Office of Admissions.
- Be concise and factual.
- Do NOT predict admission chances, calculate admission probability, give \
legal or immigration advice, or guarantee financial aid.
- Do not invent facts, deadlines, or figures that are not in the passages."""


def build_context(passages: list[RetrievedPassage]) -> str:
    """Format retrieved passages as labelled context for the model."""
    blocks = []
    for p in passages:
        d = p.document
        blocks.append(f"[{d.title} — {d.source_url}]\n{d.text}")
    return "\n\n".join(blocks)


def stub_generate(question: str, passages: list[RetrievedPassage]) -> str:
    """Deterministic extractive answer — no model call, no secrets required."""
    top = passages[0].document
    return (
        "(Prototype stub answer — retrieved from official Heinz College content; "
        "the language model is not connected in this run.)\n\n"
        f"{top.text.strip()}"
    )


def claude_generate(question: str, passages: list[RetrievedPassage]) -> str | None:
    """Grounded answer from Claude. Returns None if the model refuses."""
    import anthropic  # imported lazily so the stub path needs no dependency

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    context = build_context(passages)
    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Official source passages:\n{context}\n\n"
                    f"Prospective student question: {question}"
                ),
            }
        ],
    )
    if response.stop_reason == "refusal":
        return None
    return "".join(b.text for b in response.content if b.type == "text").strip()


def select_backend() -> str:
    """Resolve the configured backend, honouring 'auto'."""
    backend = config.GENERATION_BACKEND
    if backend == "auto":
        return "claude" if config.ANTHROPIC_API_KEY else "stub"
    return backend
