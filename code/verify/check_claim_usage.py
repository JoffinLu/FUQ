"""Round 23 claim-level citation check.

For every in-text citation in manuscript/main.tex, pull the enclosing sentence,
resolve the bib entry, and fetch the cited work's abstract (Crossref, then
Semantic Scholar, then arXiv). Results land in notes/claim_check_r23.json for
manual verdicts (SUPPORTS / PARTIAL / OVERSTATED / MISATTRIBUTED).
"""

from __future__ import annotations

import json
import pathlib
import re
import textwrap
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEX = ROOT / "manuscript" / "main.tex"
BIB = ROOT / "manuscript" / "refs.bib"
OUT = ROOT / "notes" / "claim_check_r23.json"

UA = {"User-Agent": "fuq-fairness-audit/1.0 (mailto:joffin@163.com)"}


def http_json(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def parse_bib(text: str) -> dict[str, dict[str, str]]:
    entries = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, re.S):
        body = m.group(3)
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}", body):
            fields[fm.group(1).lower()] = " ".join(fm.group(2).split())
        entries[m.group(2).strip()] = fields
    return entries


def sentences_with_cites(tex: str):
    # strip comments
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    flat = re.sub(r"\s+", " ", tex)
    out = []
    for m in re.finditer(r"\\cite[a-z]*\{([^}]*)\}", flat):
        keys = [k.strip() for k in m.group(1).split(",")]
        # sentence bounds around the citation
        start = max(flat.rfind(". ", 0, m.start()), flat.rfind(".\n", 0, m.start()))
        end = flat.find(". ", m.end())
        sent = flat[start + 1 : (end + 1) if end > 0 else m.end() + 200].strip()
        line = flat.count("\n", 0, 0)
        out.append({"keys": keys, "sentence": sent})
    return out


def crossref(doi: str) -> dict:
    return http_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))


def semantic_scholar(doi: str) -> dict:
    fields = "title,abstract,year,venue,authors"
    return http_json(
        f"https://api.semanticscholar.org/graph/v1/paper/DOI:{urllib.parse.quote(doi)}?fields={fields}"
    )


def arxiv(arxiv_id: str) -> dict:
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        xml = r.read().decode("utf-8", "replace")
    title = re.search(r"<title>(.*?)</title>", xml, re.S)
    summ = re.search(r"<summary>(.*?)</summary>", xml, re.S)
    return {
        "title": " ".join(title.group(1).split()) if title else "",
        "abstract": " ".join(summ.group(1).split()) if summ else "",
    }


def main() -> None:
    bib = parse_bib(BIB.read_text(encoding="utf-8"))
    claims = sentences_with_cites(TEX.read_text(encoding="utf-8"))
    records = []
    for claim in claims:
        for key in claim["keys"]:
            fields = bib.get(key, {})
            rec = {
                "key": key,
                "sentence": claim["sentence"],
                "bib": {k: fields.get(k, "") for k in ("title", "author", "year", "doi", "journal", "eprint")},
                "source": None,
                "abstract": "",
            }
            try:
                doi = fields.get("doi", "")
                arx = fields.get("eprint", "")
                if doi:
                    cr = crossref(doi)["message"]
                    rec["source"] = "crossref"
                    rec["abstract"] = " ".join((cr.get("abstract") or "").split())
                    if not rec["abstract"]:
                        s2 = semantic_scholar(doi)
                        rec["source"] = "crossref+semanticscholar"
                        rec["abstract"] = " ".join((s2.get("abstract") or "").split())
                elif arx:
                    ax = arxiv(arx)
                    rec["source"] = "arxiv"
                    rec["abstract"] = ax["abstract"]
            except Exception as exc:  # noqa: BLE001 - report, do not crash
                rec["error"] = f"{type(exc).__name__}: {exc}"
            records.append(rec)
    OUT.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(records)} citation instances")
    for rec in records:
        print("-", rec["key"], "|", rec["source"] or "no-source", "|",
              textwrap.shorten(rec["abstract"], 100) or "(no abstract)")


if __name__ == "__main__":
    main()
