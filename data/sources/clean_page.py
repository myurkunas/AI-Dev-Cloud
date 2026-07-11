#!/usr/bin/env python3
"""
clean_page.py — rule-based boilerplate remover for fetched CMU/Heinz pages.

Reproducible cleaning step of the pipeline. Reads fetched page markdown and
strips site chrome (nav menus, sidebars, breadcrumbs, footers, social links,
images), converts inline [text](url) links to plain text, and writes one
raw_pages/<file>.txt per source, matched to sources_manifest.json by URL.

Inputs (either/both):
  * persisted web-fetch tool-result JSON files (auto-discovered under /sessions)
  * raw markdown files in ./raw_html/*.md  (name or first lines contain the URL)

Usage:
  python3 clean_page.py                 # auto-discover + clean all matches
  python3 clean_page.py --only mism     # only files whose matched name contains 'mism'
  python3 clean_page.py --list          # show what would be matched, write nothing

Pages that arrive inline (small) and are never persisted to disk are cleaned by
hand (hybrid method) and noted in the README provenance table.
"""
import argparse, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_OUT = os.path.join(HERE, "raw_pages")
RAW_HTML = os.path.join(HERE, "raw_html")
MANIFEST = os.path.join(HERE, "sources_manifest.json")

FOOTER_MARKERS = ["\ntiktok", "\n- [Legal Info]", "\n- [Consumer Information]",
                  "\n© 20", "\nStudent Financial Services", "\n Office of Graduate"]
START_MARKERS = ["\n1. [Home]", "\n1. Home", "In This Section", "\n# "]

def norm_url(u):
    u = u.strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"(index)?(\.php|\.html)?/?$", "", u)
    return u.rstrip("/")

def load_manifest():
    m = json.load(open(MANIFEST, encoding="utf-8"))
    return {norm_url(s["url"]): s["file"] for s in m["sources"]}

def extract_text_and_url(blob):
    """From a persisted tool-result JSON or raw md, return (text, url)."""
    try:
        j = json.loads(blob)
        text = j[0]["text"] if isinstance(j, list) else j.get("text", blob)
    except Exception:
        text = blob
    url = ""
    for ln in text.splitlines()[:6]:
        m = re.search(r"https?://[^\s)]+", ln)
        if m:
            url = m.group(0); break
    return text, url

def clean(text):
    # cut to main content: earliest start marker -> earliest footer after it
    start = 0
    for mk in START_MARKERS:
        i = text.find(mk)
        if i != -1:
            start = i; break
    end = len(text)
    for mk in FOOTER_MARKERS:
        i = text.find(mk, start + 1)
        if i != -1:
            end = min(end, i)
    seg = text[start:end]

    out = []
    for ln in seg.splitlines():
        s = ln.strip()
        if not s:
            out.append(""); continue
        if "Navigate to" in s: continue
        if "Jump to" in s and s.startswith("["): continue
        if s in ("Search CMU Heinz", "Search", "Search this site only"): continue
        if s.startswith("![") or s.startswith("!["): continue
        if re.match(r"^[-*+]\s*\[", s) and "](" in s and len(s) < 180: continue   # nav link items
        if re.match(r"^\d+\.\s*\[", s): continue                                   # breadcrumb links
        if re.match(r"^\[[^\]]+\]\([^)]+\)$", s) and len(s) < 180: continue        # lone link
        if re.match(r"^https?://\S+$", s): continue                                # bare url
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)   # inline links -> text
        s = s.replace("`", "").strip("#").strip()
        s = re.sub(r"^-+$", "", s).strip()               # md hr
        s = re.sub(r"\s+", " ", s).strip()
        if s:
            out.append(s)
    txt = "\n".join(out)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    return txt

def discover_inputs():
    # os.walk traverses hidden dirs (e.g. .claude) that glob '**' skips by default
    files = []
    for base in ["/sessions"]:
        for dirpath, _dirs, names in os.walk(base):
            if os.path.basename(dirpath) == "tool-results":
                files += [os.path.join(dirpath, n) for n in names if n.endswith(".json")]
    if os.path.isdir(RAW_HTML):
        files += glob.glob(os.path.join(RAW_HTML, "*.md"))
    return files

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    url2file = load_manifest()
    os.makedirs(RAW_OUT, exist_ok=True)
    seen, wrote = {}, 0
    for path in discover_inputs():
        try:
            blob = open(path, encoding="utf-8").read()
        except Exception:
            continue
        text, url = extract_text_and_url(blob)
        if not url:
            continue
        fn = url2file.get(norm_url(url))
        if not fn:
            continue
        if args.only and args.only.lower() not in fn.lower():
            continue
        # prefer the largest capture of a given URL (most complete)
        if fn in seen and len(blob) <= seen[fn]:
            continue
        seen[fn] = len(blob)
        if args.list:
            print(f"MATCH {fn:42s} <- {os.path.basename(path)}  ({len(text)} chars)")
            continue
        cleaned = clean(text)
        open(os.path.join(RAW_OUT, fn), "w", encoding="utf-8").write(cleaned + "\n")
        print(f"WROTE {fn:42s} ({len(cleaned)} chars)")
        wrote += 1
    if not args.list:
        print(f"\nCleaned {wrote} page(s) -> {RAW_OUT}")

if __name__ == "__main__":
    main()
