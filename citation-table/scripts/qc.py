#!/usr/bin/env python3
"""
Check a finished citation table for the defects that actually get caught.

These are not stylistic checks. Each one corresponds to a way a cite-check has
failed in practice, usually in front of someone hostile:

  mangled quotation   a quote that starts or ends mid-word signals the whole
                      column was cut from a character window rather than read
  header leak         running-header text inside a quotation means the quote
                      spans a page break and was never actually read
  bare flag           a ⚠ or ◐ with no explanation tells the reader a row is a
                      problem without telling them what the problem is, which
                      is worse than no flag at all
  dead link           column 1 is a click-through; a broken link is a citation
                      the reader cannot verify
  unread but rated    an accuracy judgment on a source nobody opened is the
                      exact failure the table exists to prevent

Usage
-----
    python qc.py CitationTable.xlsx
    python qc.py CitationTable.xlsx --check-links     # network, slow
    python qc.py CitationTable.xlsx --expect-footnotes 120
"""

import argparse
import re
import sys

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl required:  pip install openpyxl --break-system-packages")

CITING = re.compile(r'^"(?P<q>.*)"\s*\((?P<meta>.*)\)\s*$', re.S)
ENDS_OK = re.compile(r'[.!?]["”")]?$|…$')
MIDWORD = re.compile(r"\w…$")
CAPTION = re.compile(r"^(Figure|Table)\s*\d")


def normletters(s):
    """Letters only. For prose comparison, where digits are noise."""
    return re.sub(r"[^A-Za-z]", "", s.upper())


def normref(s):
    """Letters AND digits, for comparing references.

    The year is often the only thing separating two works by the same author
    on the same topic, so stripping digits here would merge them.
    """
    return re.sub(r"[^A-Za-z0-9]", "", s.upper())


def qc(path, check_links=False, expect_footnotes=None, max_quote=320):
    wb = openpyxl.load_workbook(path)
    if "Citations" not in wb.sheetnames:
        sys.exit("No 'Citations' sheet found.")
    ws = wb["Citations"]
    n = ws.max_row - 3
    problems, fns, refs = [], set(), []

    # Longest repeated opening fragment across quotes ~ a leaked running header.
    quotes = []
    for r in range(4, ws.max_row + 1):
        cite = ws.cell(r, 4).value or ""
        m = CITING.match(cite.strip())
        quotes.append(m.group("q") if m else "")

    for r in range(4, ws.max_row + 1):
        ref = (ws.cell(r, 1).value or "").strip()
        summ = (ws.cell(r, 2).value or "").strip()
        role = (ws.cell(r, 3).value or "").strip()
        cite = (ws.cell(r, 4).value or "").strip()
        acc = (ws.cell(r, 5).value or "").strip()
        link = ws.cell(r, 1).hyperlink
        refs.append(ref)

        if not ref:
            problems.append((r, "empty Reference"))
        if not summ:
            problems.append((r, "empty Summary"))
        elif len(summ) < 60:
            problems.append((r, f"Summary suspiciously short ({len(summ)} chars) "
                                "— check it was written from a read, not a title"))
        if not role:
            problems.append((r, "empty Role"))

        m = CITING.match(cite)
        if not m:
            problems.append((r, "Citing cell not in  \"quote\" (§section, fns …)  form"))
        else:
            q, meta = m.group("q").strip(), m.group("meta")
            if not ENDS_OK.search(q):
                problems.append((r, f"quotation does not end on a sentence: …{q[-45:]!r}"))
            if MIDWORD.search(q):
                problems.append((r, f"quotation truncated mid-word: …{q[-45:]!r}"))
            if CAPTION.match(q):
                problems.append((r, "quotation is a figure/table caption, not prose"))
            if len(q) > max_quote:
                problems.append((r, f"quotation {len(q)} chars — over the {max_quote} ceiling"))
            for x in re.findall(r"\d+", meta):
                fns.add(int(x))

        if not acc:
            problems.append((r, "empty Accuracy"))
        elif not acc.startswith("✓") and "—" not in acc:
            problems.append((r, f"flagged row carries no explanation: {acc[:40]!r}"))

        if link and not str(link.target).startswith(("http://", "https://")):
            problems.append((r, f"malformed hyperlink target: {link.target!r}"))

    # Near-identical references: a sign deduplication silently failed.
    # Advisory only -- two genuinely different documents can share a title
    # (a talk given at two venues, a working paper and its published version),
    # and merging those is a worse error than leaving a duplicate row. Flag for
    # judgment; do not auto-merge.
    seen = {}
    for i, ref in enumerate(refs, start=4):
        k = normref(ref)[:60]
        if k and k in seen:
            problems.append((i, f"Reference near-identical to row {seen[k]} — check whether "
                                "these are the same document (merge) or two different ones "
                                "with similar titles (leave)"))
        seen[k] = i

    # Header leak: one opening fragment shared by a large share of quotations.
    # Several footnotes legitimately sitting in one long sentence will share an
    # opening, so the threshold has to be well above that before it means
    # anything.
    openings = {}
    for q in quotes:
        if len(q) > 40:
            frag = normletters(q)[:32]
            openings[frag] = openings.get(frag, 0) + 1
    for frag, c in openings.items():
        if c >= max(5, len(quotes) * 0.12):
            problems.append((0, f"{c} of {len(quotes)} quotations share the opening fragment "
                                f"{frag!r} — check for a running header leaking into the column"))

    links_checked = dead = 0
    if check_links:
        import urllib.request
        for r in range(4, ws.max_row + 1):
            h = ws.cell(r, 1).hyperlink
            if not h:
                continue
            links_checked += 1
            req = urllib.request.Request(h.target, method="HEAD",
                                         headers={"User-Agent": "Mozilla/5.0"})
            try:
                urllib.request.urlopen(req, timeout=12)
            except Exception as e:
                dead += 1
                problems.append((r, f"link did not resolve: {e.__class__.__name__}"))

    hyper = sum(1 for r in range(4, ws.max_row + 1) if ws.cell(r, 1).hyperlink)
    print(f"Rows                    : {n}")
    print(f"Hyperlinked references  : {hyper}/{n}")
    print(f"Distinct footnotes cited: {len(fns)}")
    if expect_footnotes:
        missing = [i for i in range(1, expect_footnotes + 1) if i not in fns]
        print(f"Footnotes not represented: {missing if missing else 'none'}")
        print("  (Gaps are fine if those notes carry no citation — confirm which.)")
    if check_links:
        print(f"Links checked           : {links_checked}  dead: {dead}")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for row, msg in problems:
            where = f"row {row}" if row else "table"
            print(f"  {where:>9}: {msg}")
    else:
        print("\nNo problems found.")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("--check-links", action="store_true",
                    help="resolve every hyperlink (network, slow)")
    ap.add_argument("--expect-footnotes", type=int,
                    help="highest footnote number in the source document")
    ap.add_argument("--max-quote", type=int, default=320)
    a = ap.parse_args()
    problems = qc(a.xlsx, a.check_links, a.expect_footnotes, a.max_quote)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
