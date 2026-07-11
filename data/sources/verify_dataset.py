#!/usr/bin/env python3
"""
verify_dataset.py — quality checks + retrieval sanity test for chunks.csv.

Confirms the prototype dataset is clean and useful for embedding/retrieval:
  1. structural checks (sizes, empty/duplicate, metadata completeness)
  2. boilerplate-leakage scan (nav/footer tokens that should NOT be present)
  3. a lightweight TF-IDF retrieval test over sample questions, to show the
     right SOURCE surfaces for each question, and that an out-of-scope /
     applicant-specific question scores low (-> fallback/escalation).

This uses only the standard library (no embeddings) so it runs anywhere;
the real system swaps this scorer for vector similarity.
"""
import csv, os, re, math, statistics
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "chunks.csv")

rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
print(f"Loaded {len(rows)} chunks\n")

# ---------- 1. structural checks ----------
sizes = [int(r["char_count"]) for r in rows]
print("== Chunk size (chars) ==")
print(f"  min {min(sizes)}  median {int(statistics.median(sizes))}  "
      f"mean {int(statistics.mean(sizes))}  max {max(sizes)}")
print(f"  >950 (over cap): {sum(s>950 for s in sizes)}   <120 (thin): {sum(s<120 for s in sizes)}")

empty = [r['chunk_id'] for r in rows if not r['text'].strip()]
texts = [r['text'].strip() for r in rows]
dupes = [t for t,c in Counter(texts).items() if c > 1]
print(f"\n== Integrity ==")
print(f"  empty chunks: {len(empty)}   exact-duplicate chunks: {len(dupes)}")

required = ["chunk_id","source_id","source_title","source_url","scope",
            "topic","content_version","change_frequency","date_accessed","text"]
missing = 0
for r in rows:
    for c in required:
        if not str(r.get(c,"")).strip():
            missing += 1
bad_url = [r['chunk_id'] for r in rows if not r['source_url'].startswith("https://")]
print(f"  empty metadata fields: {missing}   non-https source_url: {len(bad_url)}")
print(f"  distinct sources: {len(set(r['source_id'] for r in rows))}")

# ---------- 2. boilerplate leakage ----------
BOILER = ["Navigate to","Jump to","tiktok","Search CMU Heinz","© 2026",
          "In This Section","![","](http"]
leaks = {b: sum(b in r['text'] for r in rows) for b in BOILER}
leaks = {k:v for k,v in leaks.items() if v}
print(f"\n== Boilerplate leakage ==")
print("  none detected" if not leaks else f"  LEAKS: {leaks}")

# ---------- 3. retrieval sanity test (TF-IDF cosine, stdlib only) ----------
def toks(s):
    return re.findall(r"[a-z0-9]+", s.lower())
STOP = set("the a an of to for and or in on is are do i my me you your we can it that this "
           "what how much many need with be as at from by will not".split())

docs = [toks(r['text']) for r in rows]
df = Counter()
for d in docs:
    for w in set(d):
        if w not in STOP: df[w]+=1
N = len(docs)
idf = {w: math.log((N+1)/(c+1))+1 for w,c in df.items()}
def vec(tokens):
    tf = Counter(w for w in tokens if w not in STOP)
    return {w: (1+math.log(f))*idf.get(w,math.log(N+1)+1) for w,f in tf.items()}
def cos(a,b):
    if not a or not b: return 0.0
    dot = sum(a[w]*b.get(w,0) for w in a)
    na = math.sqrt(sum(v*v for v in a.values())); nb = math.sqrt(sum(v*v for v in b.values()))
    return dot/(na*nb) if na and nb else 0.0
dvecs = [vec(d) for d in docs]

# ---------- near-duplicate detection (program pages overlap) ----------
print("\n== Near-duplicate chunks (cosine > 0.90) ==")
dups = 0
for i in range(len(dvecs)):
    for j in range(i+1, len(dvecs)):
        s = cos(dvecs[i], dvecs[j])
        if s > 0.90:
            dups += 1
            if dups <= 8:
                print(f"  {rows[i]['chunk_id']}({rows[i]['source_id']}) ~ "
                      f"{rows[j]['chunk_id']}({rows[j]['source_id']})  cos={s:.2f}")
print(f"  near-duplicate pairs: {dups}"
      + ("  (review: mostly boilerplate essay/AI-policy text across program pages)" if dups else ""))

tests = [
    # program format / duration
    ("How long is the AIM program?", "src19|src25"),
    ("How many semesters is the MSPPM program?", "src21"),
    ("Is the MISM program STEM designated?", "src20|src26|src03"),
    # deadlines
    ("What are the application deadlines for the AI program?", "src19|src25|src02"),
    ("When is the MSHCA round 1 deadline?", "src29|src23"),
    ("Where is the MEIM entertainment program located?", "src31"),
    ("Can I submit a video essay for the entertainment program?", "src32"),
    # tuition / cost / aid
    ("How much is tuition for MSPPM?", "src13"),
    ("What scholarships are available for the AI program?", "src15"),
    ("Do I get a partner scholarship for Teach For America?", "src11"),
    # requirements / process
    ("Do I need to submit GRE scores for AIM?", "src25|src02"),
    ("Is there an application fee to apply?", "src01|src02|src03"),
    ("How many letters of recommendation are required?", "src06|src01|src02|src25|src29"),
    ("What are the prerequisites for the AI program?", "src25"),
    ("Do I need to take the TOEFL?", "src08|src02"),
    # differences among programs
    ("What is the difference between MISM and MSHCA?", "src20|src23|src12"),
    # contacts / escalation
    ("Who do I contact about my application status?", "src10|src02"),
    # out-of-scope / applicant-specific -> should score LOW (escalate):
    ("Will I be admitted with a 3.2 GPA and 3 years of work experience?", "ESCALATE"),
    ("Can you review my resume and tell me my chances?", "ESCALATE"),
]
THRESH = 0.12  # below this -> fallback/escalation
print("\n== Retrieval sanity test (TF-IDF cosine) ==")
ok = 0
for q, expect in tests:
    qv = vec(toks(q))
    scored = sorted(((cos(qv,dv), rows[i]) for i,dv in enumerate(dvecs)),
                    key=lambda x: x[0], reverse=True)
    top_s, top = scored[0]
    hit_src = top['source_id']
    if expect == "ESCALATE":
        verdict = "PASS (low score -> escalate)" if top_s < THRESH else f"CHECK (scored {top_s:.2f})"
        ok += top_s < THRESH
    else:
        good = hit_src in expect.split("|") and top_s >= THRESH
        verdict = "PASS" if good else "CHECK"
        ok += good
    print(f"  Q: {q}")
    print(f"     top={hit_src} score={top_s:.2f} [{top['source_title']}]  -> {verdict}")
print(f"\n  {ok}/{len(tests)} checks passed")
