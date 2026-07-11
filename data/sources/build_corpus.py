#!/usr/bin/env python3
"""build_corpus.py — convert chunks.csv into ../corpus.json for the app.

Bridges Member 2's chunk dataset (chunks.csv) to the document schema the
prototype's retriever reads (app/retrieval.py -> Document): id, title,
source_url, text, retrieved. Program/topic metadata is carried through as
extra fields; the current loader ignores them, and TM2 program-aware
retrieval can use them (scope = program, change_frequency = freshness).

Run from this directory:
    python build_corpus.py
"""
import csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNKS = os.path.join(HERE, "chunks.csv")
OUT = os.path.join(HERE, os.pardir, "corpus.json")  # -> data/corpus.json


def main():
    with open(CHUNKS, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    docs = []
    for r in rows:
        docs.append({
            "id": r["chunk_id"],
            "title": r["source_title"],
            "source_url": r["source_url"],
            "text": r["text"],
            "retrieved": r["date_accessed"],
            # passthrough metadata (ignored by the current loader; used by TM2
            # program-aware retrieval / freshness checks)
            "source_id": r["source_id"],
            "scope": r["scope"],
            "topic": r["topic"],
            "content_version": r["content_version"],
            "change_frequency": r["change_frequency"],
        })
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    n_sources = len({d["source_id"] for d in docs})
    print(f"Wrote {len(docs)} documents from {n_sources} sources -> {os.path.abspath(OUT)}")


if __name__ == "__main__":
    main()
