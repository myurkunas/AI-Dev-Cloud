"""A small, explainable keyword retriever over the approved Heinz corpus.

For TM1 we deliberately avoid embeddings / vector search. The corpus is a
handful of representative pages, so a simple keyword-overlap scorer is enough
to prove the workflow and is easy for the team to explain. TM2/TM3 can swap
this Retriever for an embedding-based one behind the same interface.
"""

import json
import math
import re
from collections import Counter

from pydantic import BaseModel

from . import config

# Common words that carry little meaning for matching admissions questions.
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for",
    "from", "how", "i", "in", "is", "it", "me", "my", "of", "on", "or", "the",
    "to", "was", "what", "when", "where", "which", "who", "will", "with", "you",
    "your", "can", "need", "there", "any",
}


def _tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics, drop stopwords."""
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS]


class Document(BaseModel):
    id: str
    title: str
    source_url: str
    text: str
    retrieved: str | None = None


class RetrievedPassage(BaseModel):
    document: Document
    score: float


class Retriever:
    """Scores documents by IDF-weighted keyword overlap with the query.

    Each matched query term contributes its inverse document frequency (IDF),
    so terms that appear in almost every document (e.g. "heinz", "college")
    count for ~0, while distinctive terms (e.g. "gre", "toefl") dominate. A
    small frequency bonus breaks ties. This keeps unrelated pages from being
    cited just because they share common words.
    """

    def __init__(self, documents: list[Document]):
        self.documents = documents
        self._counts: dict[str, Counter] = {
            d.id: Counter(_tokenize(f"{d.title} {d.text}")) for d in documents
        }
        n = len(documents)
        doc_freq = Counter()
        for counts in self._counts.values():
            doc_freq.update(counts.keys())
        # IDF = log(N / df); a term in every document scores 0.
        self._idf: dict[str, float] = {
            term: math.log(n / df) for term, df in doc_freq.items()
        }

    def score(self, query_terms: set[str], doc: Document) -> float:
        counts = self._counts[doc.id]
        total = 0.0
        for t in query_terms:
            count = counts[t]
            if count > 0:
                total += self._idf.get(t, 0.0) * (1 + 0.1 * (count - 1))
        return total

    def search(self, query: str, top_k: int | None = None) -> list[RetrievedPassage]:
        top_k = top_k if top_k is not None else config.TOP_K
        query_terms = set(_tokenize(query))
        scored = [
            RetrievedPassage(document=d, score=self.score(query_terms, d))
            for d in self.documents
        ]
        scored = [p for p in scored if p.score > 0]
        scored.sort(key=lambda p: p.score, reverse=True)
        return scored[:top_k]


def load_documents(path: str | None = None) -> list[Document]:
    path = path or config.CORPUS_PATH
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return [Document(**item) for item in raw]


def get_retriever(path: str | None = None) -> Retriever:
    return Retriever(load_documents(path))
