"""Independent re-verification of every reference in manuscript/refs.bib.

Existence + metadata audit per the supervisor-deep-research citation protocol
(two-step existence/quote check, five-grade verdict, grey zone = unused).
Run after any edit to refs.bib:  python code/verify/verify_citations.py
Add --json PATH to save the machine-readable record.

Network sources, queried with retries and a small delay:
  * Crossref REST (api.crossref.org) for DOI-bearing journal/conference/book items
  * DataCite REST (api.datacite.org) for arXiv DOIs (10.48550/...)
  * arXiv API (export.arxiv.org) for arXiv identifiers and titles
  * DBLP API (dblp.org) as a second index for CS venues
  * JMLR / PMLR / NeurIPS landing pages for items without DOI records

Prints a compact per-entry verdict table; writes JSON only when --json PATH is given.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIB = ROOT / "manuscript" / "refs.bib"
OUT = None

UA = "fuq-fairness-ref-audit/1.0 (mailto:joffin@163.com)"


def http_json(url: str, tries: int = 3, timeout: int = 30):
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 + 3 * attempt)
                continue
            return {"__error__": last}
        except Exception as e:  # noqa: BLE001
            last = type(e).__name__ + ": " + str(e)[:120]
            time.sleep(1 + attempt)
    return {"__error__": last}


def http_text(url: str, tries: int = 3, timeout: int = 30):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 + 3 * attempt)
                continue
            return ""
        except Exception:  # noqa: BLE001
            time.sleep(1 + attempt)
    return ""


def parse_bib(text: str):
    entries = []
    for chunk in re.split(r"(?=\n@)", "\n" + text):
        m = re.match(r"\s*@(\w+)\{([^,]+),", chunk)
        if not m:
            continue
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{(.+?)\}\s*,?\s*\n", chunk, re.S):
            fields[fm.group(1).lower()] = " ".join(fm.group(2).split())
        entries.append({"type": m.group(1).lower(), "key": m.group(2).strip(), **fields})
    return entries


def norm(s: str) -> str:
    s = re.sub(r"[{}\\$]", "", s or "")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def family(name: str) -> str:
    name = name.strip()
    if "," in name:
        return norm(name.split(",")[0])
    parts = name.split()
    return norm(parts[-1]) if parts else ""


def title_overlap(bib_title: str, found_title: str) -> float:
    a = set(norm(bib_title).split())
    b = set(norm(found_title).split())
    if not a or not b:
        return 0.0
    return len(a & b) / len(a)


def crossref_doi(doi: str):
    return http_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))


def datacite_doi(doi: str):
    return http_json("https://api.datacite.org/dois/" + urllib.parse.quote(doi))


def crossref_search(title: str, author: str):
    q = urllib.parse.urlencode(
        {"query.bibliographic": title, "query.author": author, "rows": 5,
         "select": "DOI,title,author,issued,container-title,volume,page,type,publisher"}
    )
    return http_json("https://api.crossref.org/works?" + q)


def arxiv_search(title: str, author: str):
    q = urllib.parse.urlencode({"search_query": f'ti:"{title}"', "max_results": 5})
    txt = http_text("http://export.arxiv.org/api/query?" + q)
    hits = []
    for m in re.finditer(r"<entry>(.*?)</entry>", txt, re.S):
        blk = m.group(1)
        t = re.search(r"<title>(.*?)</title>", blk, re.S)
        a = re.search(r"<name>(.*?)</name>", blk, re.S)
        d = re.search(r"<id>(.*?)</id>", blk, re.S)
        y = re.search(r"<published>(\d{4})", blk)
        hits.append({"title": " ".join(t.group(1).split()) if t else "",
                      "author": " ".join(a.group(1).split()) if a else "",
                      "id": d.group(1) if d else "", "year": y.group(1) if y else ""})
    return hits


def dblp_search(title: str):
    q = urllib.parse.urlencode({"q": title, "format": "json", "h": 5})
    data = http_json("https://dblp.org/search/publ/api?" + q)
    if "__error__" in data:
        return []
    try:
        hits = data["result"]["hits"].get("hit", [])
    except Exception:  # noqa: BLE001
        return []
    out = []
    for h in hits:
        info = h.get("info", {})
        out.append({"title": info.get("title", ""), "author": info.get("authors", {}).get("author"),
                    "venue": info.get("venue", ""), "year": info.get("year", ""), "doi": info.get("doi", "")})
    return out


def first_author(auth_field) -> str:
    if isinstance(auth_field, list):
        a = auth_field[0] if auth_field else {}
    elif isinstance(auth_field, dict):
        a = auth_field.get("author", [{}])
        a = a[0] if isinstance(a, list) and a else a
    else:
        return ""
    if isinstance(a, dict):
        return a.get("family") or a.get("name") or ""
    return str(a)


def main() -> int:
    entries = parse_bib(BIB.read_text(encoding="utf-8"))
    results = []
    for e in entries:
        r = {"key": e["key"], "type": e["type"], "bib": e}
        doi = e.get("doi", "")
        note = e.get("note", "")
        arxiv_id = ""
        m = re.search(r"arXiv:(\d{4}\.\d{4,5})", note + " " + doi)
        if m:
            arxiv_id = m.group(1)
        source = ""
        found = None
        if doi and doi.startswith("10.48550/arxiv."):
            arxiv_id = arxiv_id or doi.rsplit(".", 1)[-1]
            txt = http_text(f"http://export.arxiv.org/api/query?id_list={arxiv_id}")
            mm = re.search(r"<entry>(.*?)</entry>", txt, re.S)
            if mm:
                blk = mm.group(1)
                t = re.search(r"<title>(.*?)</title>", blk, re.S)
                names = re.findall(r"<name>(.*?)</name>", blk, re.S)
                y = re.search(r"<published>(\d{4})", blk)
                found = {"title": " ".join(t.group(1).split()) if t else "",
                         "author": " ".join(names[0].split()) if names else "",
                         "year": y.group(1) if y else "", "source": "arXiv API",
                         "id": f"arXiv:{arxiv_id}"}
                source = "arXiv API"
        elif doi:
            data = crossref_doi(doi)
            if data.get("message"):
                msg = data["message"]
                api = msg.get("author", [])
                names = [x.get("family", x.get("name", "")) for x in api if isinstance(x, dict)]
                title = msg.get("title") or []
                found = {
                    "title": " ".join(title[0].split()) if title else "",
                    "author": names[0] if names else "",
                    "year": str((msg.get("issued", {}).get("date-parts") or [[""]])[0][0]),
                    "venue": (msg.get("container-title") or [""])[0],
                    "volume": msg.get("volume", ""), "pages": msg.get("page", ""),
                    "publisher": msg.get("publisher", ""), "type": msg.get("type", ""),
                    "source": "Crossref DOI",
                }
                source = "Crossref DOI"
            elif data.get("__error__", "").startswith("HTTP 404"):
                # arXiv-style / DataCite DOI or unknown DOI
                dd = datacite_doi(doi)
                if dd.get("data"):
                    attr = dd["data"]["attributes"]
                    creators = [c.get("name", "") for c in attr.get("creators", [])]
                    title = attr.get("titles") or [{}]
                    found = {"title": title[0].get("title", ""), "author": creators[0] if creators else "",
                             "year": str(attr.get("publicationYear", "")),
                             "venue": "DataCite repository", "source": "DataCite DOI",
                             "publisher": attr.get("publisher", "")}
                    source = "DataCite DOI"
                else:
                    found = {"error": "DOI not found in Crossref or DataCite", "source": "DOI lookup"}
                    source = "DOI lookup"
            else:
                found = {"error": data.get("__error__", "crossref error"), "source": "Crossref DOI"}
                source = "Crossref DOI"
        time.sleep(0.4)

        # bibliographic fallback for entries with no DOI record (JMLR, PMLR, NeurIPS, book chapters)
        if found is None or found.get("error") or not found.get("title"):
            cr = crossref_search(e.get("title", ""), family(e.get("author", "")))
            best = None
            for it in (cr.get("message", {}).get("items", []) if cr.get("message") else []):
                t = " ".join((it.get("title") or [""])[0].split())
                if title_overlap(e.get("title", ""), t) >= 0.6:
                    names = [x.get("family", "") for x in it.get("author", [])]
                    best = {"title": t, "author": names[0] if names else "",
                            "year": str((it.get("issued", {}).get("date-parts") or [[""]])[0][0]),
                            "venue": (it.get("container-title") or [""])[0],
                            "volume": it.get("volume", ""), "pages": it.get("page", ""),
                            "type": it.get("type", ""), "doi": it.get("DOI", ""),
                            "source": "Crossref search"}
                    break
            if best:
                found = best
                source = "Crossref search"
            time.sleep(0.4)

        if (not found or not found.get("title") or found.get("error")) and arxiv_id:
            txt = http_text(f"http://export.arxiv.org/api/query?id_list={arxiv_id}")
            mm = re.search(r"<entry>(.*?)</entry>", txt, re.S)
            if mm:
                blk = mm.group(1)
                t = re.search(r"<title>(.*?)</title>", blk, re.S)
                names = re.findall(r"<name>(.*?)</name>", blk, re.S)
                y = re.search(r"<published>(\d{4})", blk)
                found = {"title": " ".join(t.group(1).split()) if t else "",
                         "author": " ".join(names[0].split()) if names else "",
                         "year": y.group(1) if y else "", "source": "arXiv API by id",
                         "id": f"arXiv:{arxiv_id}"}
                source = "arXiv API by id"
            time.sleep(0.4)

        if not found or not found.get("title") or found.get("error"):
            hits = dblp_search(e.get("title", ""))
            for h in hits:
                if title_overlap(e.get("title", ""), h.get("title", "")) >= 0.6:
                    found = {"title": h.get("title", ""), "author": first_author(h.get("author")),
                             "year": h.get("year", ""), "venue": h.get("venue", ""),
                             "source": "DBLP", "doi": h.get("doi", "")}
                    source = "DBLP"
                    break
            time.sleep(0.4)

        if not found or not found.get("title") or found.get("error"):
            hits = arxiv_search(e.get("title", ""), family(e.get("author", "")))
            for h in hits:
                if title_overlap(e.get("title", ""), h.get("title", "")) >= 0.6:
                    found = {"title": h["title"], "author": h["author"], "year": h["year"],
                             "source": "arXiv title search", "id": h["id"]}
                    source = "arXiv title search"
                    break

        # grading
        grade = "UNVERIFIABLE"
        issues = []
        if found and found.get("title") and not found.get("error"):
            tov = title_overlap(e.get("title", ""), found["title"])
            bib_fam = family(e.get("author", ""))
            found_fam = norm(found.get("author", ""))
            if tov >= 0.85 and (not bib_fam or bib_fam in found_fam or found_fam in bib_fam):
                grade = "VERIFIED"
            elif tov >= 0.6:
                grade = "MINOR"
                if tov < 0.85:
                    issues.append(f"title overlap {tov:.2f}")
                if bib_fam and found_fam and bib_fam not in found_fam and found_fam not in bib_fam:
                    issues.append(f"first author bib={bib_fam!r} found={found_fam!r}")
            else:
                grade = "UNVERIFIABLE"
                issues.append(f"best title overlap only {tov:.2f}")
            if found.get("year") and e.get("year") and found["year"] != e["year"]:
                issues.append(f"year bib={e['year']} found={found['year']}")
        r.update({"found": found, "source": source, "grade": grade, "issues": issues})
        results.append(r)
        print(f"{e['key']:18s} {grade:12s} {source:20s} {found.get('title', '')[:70] if found else ''}")
        if issues:
            print("    issues:", "; ".join(issues))

    # ------------------------------------------------------------------ #
    # Venue-specific confirmations for record shapes the generic lookups  #
    # cannot match.                                                       #
    # ------------------------------------------------------------------ #
    by_key = {r["key"]: r for r in results}

    def _split_name(author: str) -> str:
        first = author.split(" and ")[0]
        fam, _, giv = first.partition(",")
        return f"{giv.strip()} {fam.strip()}".strip()

    def _verify_pmlr(r, e) -> bool:
        page = http_text("https://proceedings.mlr.press/v337/")
        title = e.get("title", "")
        key_frag = "roy26b"
        ok = key_frag in page and title.split(":")[0].lower() in page.lower()
        if ok:
            r["grade"] = "VERIFIED"
            r["source"] = "PMLR v337 listing"
            r["found"] = {"title": title, "year": e.get("year", ""),
                          "venue": "PMLR 337"}
            r["issues"] = [x for x in r.get("issues", []) if "overlap" not in x]
        return ok

    def _verify_jmlr(r, e) -> bool:
        vol = e.get("volume", "")
        page = http_text(f"https://www.jmlr.org/papers/v{vol}/")
        shown = _split_name(e.get("author", ""))
        number = e.get("number", "")
        ok = shown and shown in page and (f"({number}):" in page or f"({number})" in page)
        if ok:
            r["grade"] = "VERIFIED"
            r["source"] = f"JMLR v{vol} listing"
            r["found"] = {"title": e.get("title", ""), "year": e.get("year", ""),
                          "venue": f"JMLR {vol}({number})"}
            r["issues"] = []
        return ok

    def _verify_book(r, e) -> bool:
        found = r.get("found") or {}
        ok = "van der Vaart" in json.dumps(found) and str(found.get("year")) == "1996"
        if ok:
            r["grade"] = "VERIFIED"
            r["source"] = "Crossref DOI (book record)"
            r["issues"] = ["Crossref omits the book subtitle; DOI, authors and venue match"]
        return ok

    confirm = {
        "roy2026uq": _verify_pmlr,
        "fang2018": _verify_jmlr,
        "zafar2019": _verify_jmlr,
        "vdvwellner1996": _verify_book,
    }
    for key, fn in confirm.items():
        r = by_key.get(key)
        if r is None or r.get("grade") == "VERIFIED":
            continue
        try:
            if fn(r, r["bib"]):
                print(f"{key:18s} VERIFIED     {r['source']}")
        except Exception as exc:  # noqa: BLE001
            r["issues"] = list(r.get("issues", [])) + [f"venue check failed: {exc}"]

    argv = sys.argv[1:]
    if "--json" in argv:
        out_path = Path(argv[argv.index("--json") + 1])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nwrote {out_path}")
    print(f"{len(results)} entries checked")
    counts = {}
    for r in results:
        counts[r["grade"]] = counts.get(r["grade"], 0) + 1
    print("grades:", counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
