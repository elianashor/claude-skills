#!/usr/bin/env python3
"""
Semantic QC for a finished citation table: the defects that get caught in front
of someone hostile. Works on every mode's layout (supporting, audit, opposing,
adverse) by finding columns by their header names.

The companion sweep (sweep_workbook.py) checks every cell mechanically. This
file checks what the cells *mean*:

  mangled quotation   a quote starting or ending mid-word signals the column was
                      cut from a character window rather than read
  header leak         one opening fragment shared by many quotations means a
                      running header leaked across a page break
  bare flag           a ⚠ or ◐ with no explanation names a problem without
                      saying what it is
  unread but rated    an ○ Unverified row that still summarizes or judges the
                      source asserts a read that never happened (gate 14)
  thin risk column    a Limitations cell too short to carry funding, conceded
                      limits, and later rebuttals (gate 12)
  bad relevance       relevance outside the integer scale 1–5
  venue inflation     prestige language in the Credibility column (gate 15)
  silent duplicate    near-identical references, flagged for judgment: a working
                      paper and its published version are different documents
  process residue     memo names, "pull list", "intake", reviewer shorthand in a
                      deliverable cell (gate 20)
  unearned claim      superlatives on the Method or Notes sheet (gate 20)

ERROR findings fail the run. ADVISORY findings need a human decision and fail
only with --strict.

Usage
-----
    python qc.py Table.xlsx
    python qc.py Table.xlsx --strict --expect-footnotes 120
    python qc.py Table.xlsx --check-links          # network, slow
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import openpyxl
except ImportError:  # pragma: no cover
    sys.exit("openpyxl required:  pip install openpyxl")

__all__ = ["Finding", "main", "qc"]

QUOTE_COLS = ("Proposed excerpt (verbatim)", "Citing paragraph(s)", "Their quote vs. the source")
REF_COLS = ("Citation", "Reference")
READ_DEPENDENT = ("Summary", "Role in manuscript / result cited", "What this source is", "Findings")
UNREAD_TEXT = "Not assessed — source unread"
ENDS_OK = re.compile(r'[.!?]["”’)\]]*$|…["”]?$')
MIDWORD_END = re.compile(r"\w…$")
CAPTION = re.compile(r"^[\"“]?(Figure|Table)\s*\d")
QUOTED = re.compile(r"[“\"]([^”\"]{12,})[”\"]")
INFLATION = re.compile(r"(?i)\btop[- ]?(5|five|tier)\b|\bleading\b|\bprestigious\b|\belite\b|\bpremier\b")
RESIDUE = re.compile(
    r"(?i)\bpull list\b|\bintake\b|\bper (the )?QC\b|\bescalated\b|\bask-\w+|\bdecisions\.md\b|"
    r"\brunledger\b|\bsnapshot v\d|\bTBD\b"
)
SUPERLATIVE = re.compile(
    r"(?i)\b(the )?most (relevant|important|comprehensive)\b|\ball (the )?relevant\b|\bexhaustive\b|"
    r"\bdefinitive\b|\bevery (relevant|published) (study|source)\b"
)


@dataclass
class Finding:
    where: str
    severity: str  # ERROR | ADVISORY
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.severity:<8} {self.code:<14} {self.where:<22} {self.message}"


def _norm_letters(s: str) -> str:
    return re.sub(r"[^A-Za-z]", "", s.upper())


def _norm_ref(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", s.upper())


def _header_map(ws) -> tuple[int | None, dict[str, int]]:
    for r in range(1, min(6, ws.max_row + 1)):
        if str(ws.cell(r, 1).value).strip() == "ID":
            cols = {}
            for c in range(1, ws.max_column + 1):
                h = str(ws.cell(r, c).value or "").strip()
                cols[re.sub(r"\s*\(.*\d{4}.*\)$", "", h) if h.startswith("In draft") else h] = c
            return r, cols
    return None, {}


def _data_rows(ws, hdr: int):
    for r in range(hdr + 1, ws.max_row + 1):
        v = ws.cell(r, 1).value
        if v is None or str(v).startswith(("§", "NO CURRENT")):
            continue
        yield r


def _quotes_in(cell: str, col: str) -> list[str]:
    if col == "Citing paragraph(s)":
        m = re.match(r'^"(?P<q>.*)"\s*\((?P<meta>.*)\)\s*$', cell.strip(), re.S)
        return [m.group("q")] if m else []
    found = QUOTED.findall(cell)
    return found or ([cell.strip()] if col == "Proposed excerpt (verbatim)" else [])


def qc(
    path: str | Path,
    check_links: bool = False,
    expect_footnotes: int | None = None,
    max_quote: int = 320,
    min_limitations: int = 80,
) -> list[Finding]:
    wb = openpyxl.load_workbook(path)
    out: list[Finding] = []
    any_main = False

    for sn in wb.sheetnames:
        ws = wb[sn]
        hdr, cols = _header_map(ws)
        if not hdr or sn == "Detail":
            continue
        any_main = True
        quotes_all: list[str] = []
        refs: dict[str, str] = {}
        footnotes: set[int] = set()

        for r in _data_rows(ws, hdr):
            rid = str(ws.cell(r, 1).value)
            where = f"{sn}!{rid}"

            def cell(name: str, ws=ws, r=r, cols=cols) -> str:
                c = cols.get(name)
                return str(ws.cell(r, c).value or "").strip() if c else ""

            acc = cell("Accuracy")
            unread = acc.startswith("○")
            if acc and not acc.startswith("✓") and " — " not in acc:
                out.append(Finding(where, "ERROR", "BARE-FLAG", f"flag with no explanation: {acc[:40]!r}"))
            if unread:
                for name in READ_DEPENDENT:
                    v = cell(name)
                    if v and not v.startswith(UNREAD_TEXT):
                        out.append(
                            Finding(where, "ERROR", "UNREAD-RATED", f"{name!r} asserts content for an unread source")
                        )

            for col in QUOTE_COLS:
                v = cell(col)
                if not v:
                    continue
                if col == "Citing paragraph(s)" and not re.match(r'^".*"\s*\(.*\)\s*$', v, re.S):
                    out.append(
                        Finding(where, "ERROR", "CITING-FORM", 'citing cell not in "quote" (§section, fns …) form')
                    )
                    continue
                if col == "Citing paragraph(s)":
                    footnotes |= {int(x) for x in re.findall(r"\bfns?\s+([\d, ]+)", v) for x in re.findall(r"\d+", x)}
                for q in _quotes_in(v, col):
                    q = q.strip()
                    if not q:
                        continue
                    quotes_all.append(q)
                    if not ENDS_OK.search(q) and not re.search(r"\(.*\)$", q):
                        out.append(Finding(where, "ERROR", "QUOTE-END", f"does not end on a sentence: …{q[-45:]!r}"))
                    if MIDWORD_END.search(q) or (q[:1].islower() and not q.startswith("…")):
                        out.append(Finding(where, "ERROR", "QUOTE-MIDWORD", f"cut mid-word: {q[:30]!r}…{q[-30:]!r}"))
                    if CAPTION.match(q):
                        out.append(Finding(where, "ADVISORY", "QUOTE-CAPTION", "quotation is a figure/table caption"))
                    if col == "Citing paragraph(s)" and len(q) > max_quote:
                        out.append(
                            Finding(where, "ADVISORY", "QUOTE-LONG", f"{len(q)} chars, over the {max_quote} ceiling")
                        )

            lim = cell("Limitations / conflicts / later rebuttals")
            if "Limitations / conflicts / later rebuttals" in cols and not unread and len(lim) < min_limitations:
                out.append(
                    Finding(
                        where,
                        "ADVISORY",
                        "THIN-RISK",
                        f"Limitations is {len(lim)} chars; funding, conceded limits and rebuttals belong here",
                    )
                )

            if "Relevance" in cols:
                rel = ws.cell(r, cols["Relevance"]).value
                if (
                    not (isinstance(rel, int) or (isinstance(rel, str) and rel.strip().isdigit()))
                    or not 1 <= int(rel) <= 5
                ):
                    out.append(Finding(where, "ERROR", "RELEVANCE", f"relevance must be an integer 1–5, got {rel!r}"))

            cred = cell("Credibility")
            if cred and INFLATION.search(cred):
                out.append(
                    Finding(
                        where,
                        "ADVISORY",
                        "VENUE-INFLATION",
                        f"check the label is earned: {INFLATION.search(cred).group(0)!r}",
                    )
                )

            for c in range(1, ws.max_column + 1):
                v = ws.cell(r, c).value
                if isinstance(v, str) and RESIDUE.search(v):
                    out.append(Finding(where, "ERROR", "RESIDUE", f"process residue: {RESIDUE.search(v).group(0)!r}"))

            ref_col = next((c for c in REF_COLS if c in cols), None)
            if ref_col:
                ref = cell(ref_col)
                key = _norm_ref(ref)[:60]
                if key and key in refs:
                    out.append(
                        Finding(
                            where,
                            "ADVISORY",
                            "NEAR-DUP",
                            f"reference near-identical to {refs[key]}: same document (merge) or two "
                            "different ones with similar titles (leave)?",
                        )
                    )
                refs.setdefault(key, rid)
                link = ws.cell(r, cols[ref_col]).hyperlink
                if link is not None and not str(link.target or "").startswith(("http://", "https://")):
                    out.append(Finding(where, "ERROR", "BAD-LINK", f"malformed hyperlink target {link.target!r}"))

        openings: dict[str, int] = {}
        for q in quotes_all:
            if len(q) > 40:
                frag = _norm_letters(q)[:32]
                openings[frag] = openings.get(frag, 0) + 1
        for frag, n in openings.items():
            if n >= max(5, len(quotes_all) * 0.12):
                out.append(
                    Finding(sn, "ERROR", "HEADER-LEAK", f"{n} of {len(quotes_all)} quotations open with {frag!r}")
                )

        if expect_footnotes and "Citing paragraph(s)" in cols:
            missing = [i for i in range(1, expect_footnotes + 1) if i not in footnotes]
            if missing:
                out.append(
                    Finding(
                        sn,
                        "ADVISORY",
                        "FOOTNOTE-GAP",
                        f"footnotes not represented: {missing[:30]}{' …' if len(missing) > 30 else ''} "
                        "(fine only if those notes carry no citation)",
                    )
                )

        if check_links:
            import urllib.request

            ref_col = next((c for c in REF_COLS if c in cols), None)
            for r in _data_rows(ws, hdr):
                h = ws.cell(r, cols[ref_col]).hyperlink if ref_col else None
                if not h:
                    continue
                req = urllib.request.Request(h.target, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
                try:
                    urllib.request.urlopen(req, timeout=12)
                except Exception as e:
                    out.append(Finding(f"{sn}!{ws.cell(r, 1).value}", "ERROR", "DEAD-LINK", e.__class__.__name__))

    for sn in ("Method", "Notes"):
        if sn in wb.sheetnames:
            for row in wb[sn].iter_rows():
                for c in row:
                    if isinstance(c.value, str) and SUPERLATIVE.search(c.value):
                        out.append(
                            Finding(
                                f"{sn}!{c.coordinate}",
                                "ADVISORY",
                                "UNEARNED-CLAIM",
                                f"superlative needs proof or softer wording: {SUPERLATIVE.search(c.value).group(0)!r}",
                            )
                        )
    if not any_main:
        out.append(Finding("(workbook)", "ERROR", "NO-TABLE", "no sheet with an ID header row was found"))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx")
    ap.add_argument("--strict", action="store_true", help="advisory findings also fail the run")
    ap.add_argument("--check-links", action="store_true", help="resolve every hyperlink (network, slow)")
    ap.add_argument("--expect-footnotes", type=int, help="highest footnote number in the manuscript (audit mode)")
    ap.add_argument("--max-quote", type=int, default=320)
    a = ap.parse_args(argv)
    findings = qc(a.xlsx, a.check_links, a.expect_footnotes, a.max_quote)
    for f in findings:
        print(f)
    errors = sum(f.severity == "ERROR" for f in findings)
    advisories = len(findings) - errors
    print(f"-- {errors} error(s), {advisories} advisory finding(s)")
    return 1 if errors or (a.strict and advisories) else 0


if __name__ == "__main__":
    sys.exit(main())
