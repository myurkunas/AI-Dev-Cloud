#!/usr/bin/env python3
"""
build_chunks.py — Heinz admissions RAG prototype dataset builder.

Reads cleaned page text from raw_pages/ and per-source metadata from
sources_manifest.json, splits each page into retrieval-sized chunks with
sentence-aware overlap, and writes chunks.csv with source metadata carried
through to every chunk (so answers can cite their source + freshness).

Boilerplate removal happens upstream (clean_page.py); this does normalization
+ chunking only.
"""
import csv, os, re, glob, json

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw_pages")
OUT = os.path.join(HERE, "chunks.csv")
MANIFEST = os.path.join(HERE, "sources_manifest.json")

TARGET = 700      # target chunk size in characters
MAXCHARS = 950    # hard cap before forced sentence split
OVERLAP = 140     # chars of trailing context prepended to next chunk

_m = json.load(open(MANIFEST, encoding="utf-8"))
DATE_ACCESSED = _m["date_accessed"]
META = {s["file"]: dict(source_id=s["source_id"], title=s["title"], url=s["url"],
                        scope=s["scope"], topic=s["topic"],
                        content_version=s["content_version"],
                        change_frequency=s["change_frequency"]) for s in _m["sources"]}

def normalize(text):
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def split_sentences(p):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", p)
    return [s.strip() for s in parts if s.strip()]

def chunk_text(text):
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, buf = [], ""
    def flush():
        nonlocal buf
        if buf.strip():
            chunks.append(buf.strip())
        buf = ""
    for p in paras:
        if len(p) > MAXCHARS:
            flush()
            cur = ""
            for s in split_sentences(p):
                if cur and len(cur) + len(s) + 1 > TARGET:
                    chunks.append(cur.strip()); cur = ""
                cur += (" " if cur else "") + s
            if cur.strip():
                chunks.append(cur.strip())
            continue
        if buf and len(buf) + len(p) + 2 > TARGET:
            flush()
        buf += ("\n\n" if buf else "") + p
    flush()
    out = []
    for i, c in enumerate(chunks):
        if i == 0:
            out.append(c); continue
        tail = chunks[i-1][-OVERLAP:]
        m = re.search(r"[.!?]\s+(.*)$", tail)
        ov = m.group(1) if m else tail
        out.append((ov + " " + c).strip() if ov and len(ov) < OVERLAP + 40 else c)
    # merge any tiny chunk (< MINCHARS) into a neighbor: previous if it exists,
    # otherwise the next chunk (handles a short leading title line).
    MINCHARS = 120
    merged = []
    for c in out:
        if merged and len(c) < MINCHARS:
            merged[-1] = (merged[-1] + " " + c).strip()
        else:
            merged.append(c)
    if len(merged) > 1 and len(merged[0]) < MINCHARS:
        merged[1] = (merged[0] + " " + merged[1]).strip()
        merged.pop(0)
    return merged

def main():
    rows, cid = [], 0
    for path in sorted(glob.glob(os.path.join(RAW, "*.txt"))):
        fn = os.path.basename(path)
        meta = META.get(fn)
        if not meta:
            print("WARN: no manifest entry for", fn); continue
        text = normalize(open(path, encoding="utf-8").read())
        for ch in chunk_text(text):
            cid += 1
            rows.append({
                "chunk_id": f"c{cid:03d}",
                "source_id": meta["source_id"], "source_title": meta["title"],
                "source_url": meta["url"], "scope": meta["scope"], "topic": meta["topic"],
                "content_version": meta["content_version"],
                "change_frequency": meta["change_frequency"],
                "date_accessed": DATE_ACCESSED,
                "char_count": len(ch), "token_estimate_approx": round(len(ch) / 4),
                "text": ch,
            })
    cols = ["chunk_id","source_id","source_title","source_url","scope","topic",
            "content_version","change_frequency","date_accessed",
            "char_count","token_estimate_approx","text"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} chunks from {len(set(r['source_id'] for r in rows))} sources -> {OUT}")

if __name__ == "__main__":
    main()
