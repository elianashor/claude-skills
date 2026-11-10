#!/usr/bin/env python3
"""Whole-workbook integrity sweep (QC gates 1-4, mechanical part) for ANY citation-table workbook.

Usage: python sweep_workbook.py TABLE.xlsx [--ids-prefix S A] [--detail-sheet Detail]
Checks EVERY cell of EVERY sheet. Exit code 1 if any finding. Findings printed one per line:
SHEET!CELL | CODE | excerpt

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
Review each finding; a consciously accepted one must be listed in the run ledger with its reason.
"""
import sys, re, collections
import openpyxl

def main():
    path = sys.argv[1]
    wb = openpyxl.load_workbook(path)
    findings = []
    seen = collections.Counter()
    id_cols = {}
    for sn in wb.sheetnames:
        ws = wb[sn]
        # find header row (first row whose first cell is 'ID'), else treat all as prose
        hdr_row = None
        for r in range(1, min(6, ws.max_row+1)):
            if str(ws.cell(r,1).value).strip() == "ID": hdr_row = r; break
        headers = [str(ws.cell(hdr_row,c).value or "") for c in range(1, ws.max_column+1)] if hdr_row else []
        for row in ws.iter_rows():
            for cell in row:
                v = cell.value
                if not isinstance(v, str) or not v.strip(): continue
                s = v.strip(); loc = f"{sn}!{cell.coordinate}"
                is_header_band = hdr_row and cell.row <= hdr_row
                is_section_hdr = s.startswith("§") or s.startswith("NO CURRENT")
                if len(s) > 120: seen[s] += 1
                if re.search(r"\bTODO\b|\bFIXME\b|\[INCOMPLETE|\bXXX\b|lorem ipsum|<placeholder>|see ask-|per the QC", s, re.I):
                    findings.append((loc, "ARTIFACT", s[:60]))
                if re.match(r"^(Background|Objective|Methods|Design|Results)\s*:", s) and "no published abstract" not in s[:200]:
                    findings.append((loc, "SCAFFOLD", s[:60]))
                if "  " in v or v != v.rstrip():
                    findings.append((loc, "DOUBLESPACE", s[:60]))
                if not is_header_band and not is_section_hdr and len(s) > 80:
                    if s[-1] in ",;:—-(“‘" or (s[-1] == '"' and s.count('"') % 2 == 1) or (s[-1] == "'" and s.count("'") % 2 == 1) or s.endswith("…and") or s.endswith(" the"):
                        findings.append((loc, "TRUNC-COMMA", "..."+s[-60:]))
                    elif s[-1] not in ".!?\"'’”)]%" and not s[-1].isdigit():
                        findings.append((loc, "TRUNC-PUNCT", "..."+s[-60:]))
                    m = re.search(r"[A-Za-z]{5,}[ ]([a-z]{1,3})$", s)
                    if m and m.group(1) not in ("is","it","of","to","on","in","by","at","or","as","up","us","so","no"):
                        findings.append((loc, "TRUNC-MIDWORD", "..."+s[-40:]))
                    for o,c2 in [("(",")"),("[","]")]:
                        if s.count(o) != s.count(c2):
                            findings.append((loc, "UNBALANCED", f"{o}{c2} " + s[-40:])); break
                    for q in ["“”"]:
                        if s.count(q[0]) != s.count(q[1]):
                            findings.append((loc, "UNBALANCED", "quotes ..." + s[-40:])); break
        # required cells + links + IDs on data rows
        if hdr_row:
            ids = []
            for r in range(hdr_row+1, ws.max_row+1):
                idv = ws.cell(r,1).value
                if idv is None: continue
                sv = str(idv)
                if sv.startswith("§") or sv.startswith("NO CURRENT"): continue
                ids.append(sv)
                for c in range(1, ws.max_column+1):
                    if not str(ws.cell(hdr_row,c).value or ""): continue
                    if ws.cell(r,c).value in (None,""):
                        findings.append((f"{sn}!{ws.cell(r,c).coordinate}", "EMPTY-REQ", headers[c-1][:40]))
                if len(headers) > 1 and ("itation" in headers[1] or "eference" in headers[1]) and not ws.cell(r,2).hyperlink:
                    findings.append((f"{sn}!{ws.cell(r,2).coordinate}", "NOLINK", str(ws.cell(r,2).value)[:50]))
            id_cols[sn] = ids
    for s_, n in seen.items():
        if n >= 3: findings.append(("(multiple)", "DUPCELL", f"{n}x: " + s_[:60]))
    main_sheets = [s for s in id_cols if s.lower() not in ("detail","notes","method")]
    if "Detail" in id_cols and main_sheets:
        main_ids = sorted(set().union(*[set(id_cols[s]) for s in main_sheets]))
        if sorted(set(id_cols["Detail"])) != main_ids:
            findings.append(("Detail", "ID-MISMATCH", f"main={len(main_ids)} detail={len(set(id_cols['Detail']))}"))
    for loc, code, ex in findings:
        print(f"{loc} | {code} | {ex}")
    print(f"-- {len(findings)} finding(s) across {len(wb.sheetnames)} sheet(s)")
    sys.exit(1 if findings else 0)

if __name__ == "__main__": main()
