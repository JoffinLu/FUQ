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
import time
import urllib.parse
import urllib.request
from pathlib import Path

BIB = Path(__file__).resolve().parent / "refs.bib"
OUT = Path(__file__).resolve().parent / "refs_checked.json"
MAILTO = "fuq.repro@example.com"

# Entries that the OpenAlex index does not contain but that are verified elsewhere.
MANUAL = {
    "roy2026uq": (
        "UAI 2026 proceedings (PMLR 337:5845-5865) are not indexed by OpenAlex; "
        "verified against the published PDF and the 2023 arXiv version 2304.13950"
    ),
}


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

    last_exc: Exception | None = None
    for delay in (0, 4, 10):
        try:
            return _get(query)
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code == 400:
                # some titles (e.g. containing '?') are rejected; retry stripped
                cleaned = re.sub(r"[^A-Za-z0-9 ]", " ", query)
                return _get(cleaned)
            if exc.code != 429 and exc.code < 500:
                raise
        except urllib.error.URLError as exc:  # transient DNS/timeouts
            last_exc = exc
        time.sleep(delay)
    raise last_exc  # type: ignore[misc]


def check_crossref(entry: dict) -> dict | None:
    """Resolve a DOI through Crossref when OpenAlex is rate-limited."""
    doi = (entry.get("doi") or "").strip()
    if not doi:
        return None
    doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": f"fuq-check/1.0 (mailto:{MAILTO})"})
    for delay in (0, 4):
        try:
            with urllib.request.urlopen(req, timeout=45) as f:
                msg = json.load(f)["message"]
            break
        except Exception:  # noqa: BLE001
            time.sleep(delay)
    else:
        return None
    title = (msg.get("title") or [""])[0]
    subtitle = msg.get("subtitle") or []
    if subtitle:
        title = title + ": " + " ".join(subtitle)
    ratio = difflib.SequenceMatcher(None, norm(entry.get("title", "")), norm(title)).ratio()
    year = (msg.get("issued", {}).get("date-parts") or [[0]])[0][0]
    authors = [(a.get("family") or "").lower() for a in msg.get("author", [])]
    author_str = norm(entry.get("author", ""))
    author_ok = bool(authors) and any(
        norm(a).split()[-1] in author_str for a in authors if norm(a).strip()
    )
    try:
        year_ok = abs(int(year) - int(entry.get("year", 0))) <= 1
    except (TypeError, ValueError):
        year_ok = False
    if ratio >= 0.85 and author_ok and year_ok:
        verdict = "exact"
    else:
        verdict = "near"
    result = {
        "key": entry["key"],
        "verdict": verdict,
        "source": "crossref",
        "score": round(ratio, 3),
        "title_ratio": round(ratio, 3),
        "oa_title": title,
        "oa_year": year,
        "oa_venue": msg.get("publisher"),
        "doi": "https://doi.org/" + doi,
    }
    if verdict == "near" and ratio < 0.85 and author_ok and year_ok:
        result["note"] = (
            "DOI resolves with matching author and year; the Crossref record's "
            "title omits the subtitle used in refs.bib"
        )
    return result


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
    force = "--refresh" in sys.argv
    for e in entries:
        title = e.get("title", "")
        year = e.get("year", "")
        first_author = (e.get("author", "").split(",")[0] or "").strip().lower()
        # Reuse a previously stored verdict unless the entry changed: this keeps the
        # script usable when the free OpenAlex endpoint is rate-limited.  --refresh
        # forces a fresh network query for every entry.
        prev_entry = prev_verdicts.get(e["key"])
        if (
            not force
            and prev_entry is not None
            and prev_entry.get("verdict") in ("exact", "near", "missing")
            and prev_entry.get("bib_title") in (None, "", title)
        ):
            reused = dict(prev_entry)
            reused["cached"] = True
            results.append(reused)
            print(f"  {reused['verdict']:8s} {e['key']:14s} reused from refs_checked.json")
            continue
        try:
            cands = search_openalex(title)
        except Exception as exc:  # noqa: BLE001
            if e["key"] in MANUAL:
                results.append({"key": e["key"], "verdict": "missing",
                                "note": MANUAL[e["key"]], "doi": e.get("doi")})
                print(f"  missing  {e['key']:14s} manual verification note")
                continue
            fallback = check_crossref(e)
            if fallback is not None:
                results.append(fallback)
                print(f"  {fallback['verdict']:8s} {e['key']:14s} via crossref "
                      f"(OpenAlex error: {str(exc)[:40]})")
                continue
            prev = prev_verdicts.get(e["key"])
            if prev is not None and prev.get("verdict") in ("exact", "near", "missing"):
                cached = dict(prev)
                cached["cached"] = True
                results.append(cached)
                print(f"  {prev['verdict']:8s} {e['key']:14s} cached (API error: {str(exc)[:50]})")
            else:
                results.append({"key": e["key"], "verdict": "error", "error": str(exc)})
            continue
        time.sleep(0.4)  # be polite to the OpenAlex API
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
    titles = {e["key"]: e.get("title", "") for e in entries}
    for r in results:
        r.setdefault("bib_title", titles.get(r["key"], ""))
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
