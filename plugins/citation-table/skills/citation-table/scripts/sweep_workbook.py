#!/usr/bin/env python3
"""Whole-workbook integrity sweep (QC gates 1-4, mechanical part) for ANY citation-table workbook.

Usage: python sweep_workbook.py TABLE.xlsx [--accept accepted.txt]

Checks EVERY cell of EVERY sheet. Exit code 1 if any unaccepted finding. Findings
print one per line as  SHEET!CELL | CODE | excerpt

Codes:
  TRUNC-PUNCT   long prose cell (>80 chars) not ending in . ! ? " ' ) ] % or digit
  TRUNC-COMMA   cell ends in , ; : — - ( or an opening quote
  TRUNC-MIDWORD cell's last token is a 1-3 letter lowercase fragment after a longer word (heuristic)
  UNBALANCED    unbalanced quotes or parentheses
  SCAFFOLD      cell begins with Background:/Objective:/Methods:/Design:/Results: scaffolding
  ARTIFACT      TODO/FIXME/[INCOMPLETE]/lorem/XXX/<placeholder>/see ask-/per the QC
  DOUBLESPACE   double spaces or trailing whitespace
  DUPCELL       identical >120-char cell appears in 3+ rows (template rot)
  EMPTY-REQ     empty cell in a required column of a data row
  ID-MISMATCH   main-sheet IDs vs detail-sheet IDs not 1:1
  NOLINK        citation cell without hyperlink

Review each finding. A consciously accepted one goes in the run ledger with its
reason, and can be listed in an --accept file ("SHEET!CELL CODE" per line) so
the sweep stays green without hiding anything new.
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:  # pragma: no cover
    sys.exit("openpyxl required:  pip install openpyxl")

__all__ = ["main", "sweep"]

ARTIFACT = re.compile(r"\bTODO\b|\bFIXME\b|\[INCOMPLETE|\bXXX\b|lorem ipsum|<placeholder>|see ask-|per the QC", re.I)
SCAFFOLD = re.compile(r"^(Background|Objective|Methods|Design|Results)\s*:")
SHORT_OK = {"is", "it", "of", "to", "on", "in", "by", "at", "or", "as", "up", "us", "so", "no"}
SIDE_SHEETS = {"detail", "notes", "method"}


def _is_band(s: str) -> bool:
    return s.startswith("§") or s.startswith("NO CURRENT")


def sweep(path: str | Path) -> list[tuple[str, str, str]]:
    wb = openpyxl.load_workbook(path)
    findings: list[tuple[str, str, str]] = []
    seen: collections.Counter[str] = collections.Counter()
    id_cols: dict[str, list[str]] = {}

    for sn in wb.sheetnames:
        ws = wb[sn]
        hdr_row = next((r for r in range(1, min(6, ws.max_row + 1)) if str(ws.cell(r, 1).value).strip() == "ID"), None)
        headers = [str(ws.cell(hdr_row, c).value or "") for c in range(1, ws.max_column + 1)] if hdr_row else []

        for row in ws.iter_rows():
            for cell in row:
                v = cell.value
                if not isinstance(v, str) or not v.strip():
                    continue
                s = v.strip()
                loc = f"{sn}!{cell.coordinate}"
                header_band = bool(hdr_row and cell.row <= hdr_row)
                if len(s) > 120:
                    seen[s] += 1
                if ARTIFACT.search(s):
                    findings.append((loc, "ARTIFACT", s[:60]))
                if SCAFFOLD.match(s) and "no published abstract" not in s[:200]:
                    findings.append((loc, "SCAFFOLD", s[:60]))
                if "  " in v or v != v.rstrip():
                    findings.append((loc, "DOUBLESPACE", s[:60]))
                if header_band or _is_band(s) or len(s) <= 80:
                    continue
                if (
                    s[-1] in ",;:—-(“‘"
                    or (s[-1] == '"' and s.count('"') % 2 == 1)
                    or (s[-1] == "'" and s.count("'") % 2 == 1)
                    or s.endswith("…and")
                    or s.endswith(" the")
                ):
                    findings.append((loc, "TRUNC-COMMA", "..." + s[-60:]))
                elif s[-1] not in ".!?\"'’”)]%" and not s[-1].isdigit():
                    findings.append((loc, "TRUNC-PUNCT", "..." + s[-60:]))
                m = re.search(r"[A-Za-z]{5,}[ ]([a-z]{1,3})$", s)
                if m and m.group(1) not in SHORT_OK:
                    findings.append((loc, "TRUNC-MIDWORD", "..." + s[-40:]))
                for o, c2 in (("(", ")"), ("[", "]")):
                    if s.count(o) != s.count(c2):
                        findings.append((loc, "UNBALANCED", f"{o}{c2} " + s[-40:]))
                        break
                if s.count("“") != s.count("”"):
                    findings.append((loc, "UNBALANCED", "quotes ..." + s[-40:]))

        if hdr_row:
            ids = []
            for r in range(hdr_row + 1, ws.max_row + 1):
                idv = ws.cell(r, 1).value
                if idv is None or _is_band(str(idv)):
                    continue
                ids.append(str(idv))
                for c in range(1, ws.max_column + 1):
                    if headers[c - 1] and ws.cell(r, c).value in (None, ""):
                        findings.append((f"{sn}!{ws.cell(r, c).coordinate}", "EMPTY-REQ", headers[c - 1][:40]))
                if (
                    len(headers) > 1
                    and ("itation" in headers[1] or "eference" in headers[1])
                    and not ws.cell(r, 2).hyperlink
                ):
                    findings.append((f"{sn}!{ws.cell(r, 2).coordinate}", "NOLINK", str(ws.cell(r, 2).value)[:50]))
            id_cols[sn] = ids

    for s_, n in seen.items():
        if n >= 3:
            findings.append(("(multiple)", "DUPCELL", f"{n}x: " + s_[:60]))
    main_sheets = [s for s in id_cols if s.lower() not in SIDE_SHEETS]
    if "Detail" in id_cols and main_sheets:
        main_ids = sorted(set().union(*[set(id_cols[s]) for s in main_sheets]))
        if sorted(set(id_cols["Detail"])) != main_ids:
            findings.append(("Detail", "ID-MISMATCH", f"main={len(main_ids)} detail={len(set(id_cols['Detail']))}"))
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx")
    ap.add_argument("--accept", help='file of accepted findings, one "SHEET!CELL CODE" per line')
    a = ap.parse_args(argv)
    accepted = set()
    if a.accept:
        accepted = {" ".join(line.split()[:2]) for line in Path(a.accept).read_text().splitlines() if line.strip()}
    wb = openpyxl.load_workbook(a.xlsx, read_only=True)
    nsheets = len(wb.sheetnames)
    wb.close()
    findings = sweep(a.xlsx)
    open_ = [f for f in findings if f"{f[0]} {f[1]}" not in accepted]
    for loc, code, ex in findings:
        tag = " (accepted)" if f"{loc} {code}" in accepted else ""
        print(f"{loc} | {code} | {ex}{tag}")
    print(f"-- {len(findings)} finding(s) across {nsheets} sheet(s); {len(open_)} unaccepted")
    return 1 if open_ else 0


if __name__ == "__main__":
    sys.exit(main())
