#!/usr/bin/env python3
"""
verify_text.py — Phase 1 gate: check cleaned raw_pages/*.txt before chunking.

Checks each file for:
  * CLEAN   — no site boilerplate / nav / markdown-link or image syntax
  * ACCURATE(structural) — non-trivial length, matches a manifest entry
  * LOGICAL — ends on sentence punctuation (no mid-sentence truncation),
              no obviously empty sections
Also cross-checks manifest <-> files (every source has a file and vice versa).
"""
import os, re, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw_pages")
MANIFEST = os.path.join(HERE, "sources_manifest.json")

man = json.load(open(MANIFEST, encoding="utf-8"))
man_files = {s["file"] for s in man["sources"]}
disk_files = {os.path.basename(p) for p in glob.glob(os.path.join(RAW, "*.txt"))}

BOILER = ["Navigate to", "Jump to", "tiktok", "Search CMU Heinz", "In This Section",
          "© 20", "](http", "![", "Skip to", "chevronhamburger"]

print("== Manifest <-> files ==")
missing_file = sorted(man_files - disk_files)
orphan_file = sorted(disk_files - man_files)
print(f"  manifest entries: {len(man_files)}   files on disk: {len(disk_files)}")
print(f"  missing files (in manifest, no .txt): {missing_file or 'none'}")
print(f"  orphan files (no manifest entry): {orphan_file or 'none'}")

print("\n== Per-file checks ==")
problems = 0
for fn in sorted(disk_files):
    txt = open(os.path.join(RAW, fn), encoding="utf-8").read().strip()
    issues = []
    hits = [b for b in BOILER if b in txt]
    if hits:
        issues.append(f"boilerplate{hits}")
    if len(txt) < 150:
        issues.append(f"short({len(txt)})")
    # logical: should end with sentence punctuation
    if txt and txt[-1] not in ".!?)\"":
        issues.append(f"ends-oddly('...{txt[-20:]}')")
    # crude truncation check: trailing ' the'/' and'/' to'
    if re.search(r"\b(the|and|to|of|a|for|with|in|on)$", txt):
        issues.append("dangling-word")
    status = "OK " if not issues else "!! "
    if issues:
        problems += 1
    print(f"  {status}{fn:40s} {len(txt):5d} chars  {'; '.join(issues)}")

print(f"\n{len(disk_files)-problems}/{len(disk_files)} files clean; {problems} flagged")
