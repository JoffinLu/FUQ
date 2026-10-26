"""Verify every refs.bib entry against OpenAlex (title/author/year/venue + DOI).

Writes manuscript/refs_checked.json with per-entry verdicts:
  exact   -- title and first author last name match, year within 1
  near    -- title matches with high similarity but some metadata differs (record DOI for fixing)
  missing -- no OpenAlex match (flag for manual check)
Run:  python manuscript/check_refs.py
"""
from __future__ import annotations

import difflib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BIB = Path(__file__).resolve().parent / "refs.bib"
OUT = Path(__file__).resolve().parent / "refs_checked.json"
MAILTO = "fuq.repro@example.com"


def parse_bib(text: str) -> list[dict]:
    entries = []
    for block in re.split(r"\n@", "\n" + text.strip()):
        if "{" not in block:
            continue
        kind = block.split("{", 1)[0].strip().lower()
        m = re.match(r"[a-z]+\s*\{([^,]+),", block)
        if not m:
            continue
        key = m.group(1).strip()
        fields = {}
        for line in block.splitlines():
            fm = re.match(r"\s*(\w+)\s*=\s*\{(.*)\}\s*,?\s*$", line)
            if fm:
                fields[fm.group(1).lower()] = " ".join(fm.group(2).split())
        entries.append({"key": key, "type": kind, **fields})
    return entries


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower())


def search_openalex(query: str, n: int = 5) -> list[dict]:
    def _get(q: str) -> list[dict]:
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
            {"search": q, "per-page": n, "mailto": MAILTO}
        )
        req = urllib.request.Request(url, headers={"User-Agent": "fuq-check/1.0"})
        with urllib.request.urlopen(req, timeout=45) as f:
            return json.load(f).get("results", [])

    try:
        return _get(query)
    except urllib.error.HTTPError as exc:
        if exc.code != 400:
            raise
        # some titles (e.g. containing '?') are rejected; retry with punctuation stripped
        cleaned = re.sub(r"[^A-Za-z0-9 ]", " ", query)
        return _get(cleaned)


def main() -> int:
    entries = parse_bib(BIB.read_text(encoding="utf-8"))
    # previous verdicts are kept as a fallback when the API is unreachable
    prev_verdicts: dict[str, dict] = {}
    if OUT.exists():
        try:
            prev_verdicts = {r["key"]: r for r in json.loads(OUT.read_text(encoding="utf-8"))}
        except Exception:  # noqa: BLE001
            prev_verdicts = {}
    results = []
    for e in entries:
        title = e.get("title", "")
        year = e.get("year", "")
        first_author = (e.get("author", "").split(",")[0] or "").strip().lower()
        try:
            cands = search_openalex(title)
        except Exception as exc:  # noqa: BLE001
            prev = prev_verdicts.get(e["key"])
            if prev is not None:
                cached = dict(prev)
                cached["cached"] = True
                results.append(cached)
                print(f"  {prev['verdict']:8s} {e['key']:14s} cached (API error: {str(exc)[:50]})")
            else:
                results.append({"key": e["key"], "verdict": "error", "error": str(exc)})
            continue
        best = None
        for c in cands:
            t = c.get("title") or c.get("display_name") or ""
            ratio = difflib.SequenceMatcher(None, norm(title), norm(t)).ratio()
            names = [a.get("author", {}).get("display_name", "").lower()
                     for a in c.get("authorships", [])]
            author_ok = bool(names) and first_author.split()[-1] in names[0]
            year_ok = abs(int(c.get("publication_year", 0) or 0) - int(year)) <= 1
            score = ratio + 0.1 * author_ok + 0.1 * year_ok
            if best is None or score > best["score"]:
                best = {"score": score, "ratio": ratio, "author_ok": author_ok,
                        "year_ok": year_ok, "oa_title": t,
                        "oa_year": c.get("publication_year"), "doi": c.get("doi"),
                        "venue": (c.get("primary_location") or {}).get("source", {}).get("display_name") if (c.get("primary_location") or {}).get("source") else None}
        if best is None:
            results.append({"key": e["key"], "verdict": "missing", "title": title})
        else:
            if best["ratio"] >= 0.97 and best["author_ok"] and best["year_ok"]:
                verdict = "exact"
            elif best["ratio"] >= 0.9:
                verdict = "near"
            else:
                verdict = "missing"
            results.append({"key": e["key"], "verdict": verdict, "score": round(best["score"], 3),
                            "title_ratio": round(best["ratio"], 3),
                            "oa_title": best["oa_title"], "oa_year": best["oa_year"],
                            "oa_venue": best["venue"], "doi": best["doi"]})
    OUT.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    counts = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print("verdicts:", counts)
    for r in results:
        if r["verdict"] != "exact":
            print(f"  {r['verdict']:8s} {r['key']:14s} doi={r.get('doi')}")
            if r.get("oa_title") and r.get("oa_title") != r.get("title"):
                print(f"            found: {r['oa_title'][:90]}")
    print(f"saved {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
