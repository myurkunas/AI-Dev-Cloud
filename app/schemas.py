"""Pydantic request/response models for the /ask endpoint.

These define the public contract. The fields anticipate the fuller TM2/TM3
system (answer, sources, support status, escalation) while staying simple.
"""

from enum import Enum

from pydantic import BaseModel, Field


class SupportStatus(str, Enum):
    """Whether the answer is grounded in approved official sources."""

    supported = "supported"
    unsupported = "unsupported"
    escalated = "escalated"


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="A prospective student's admissions question.",
        examples=["Is the GRE required for Heinz College programs?"],
    )


class Source(BaseModel):
    title: str
    url: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source] = []
    support_status: SupportStatus
    # Guidance to a human admissions representative when we won't/can't answer.
    escalation: str | None = None
    # Which generator produced the answer: "stub", "claude", or "policy".
    model: str
