#!/usr/bin/env python3
"""
Build the citation-table workbook from verified row data.

Input: a JSON array, one object per UNIQUE source (not per footnote):

    {
      "fns":        [12, 19, 27],
      "reference":  "Author & Coauthor (Year). Title of the cited
                     work. Venue, volume(issue), pages.",
      "url":        "https://...",           # hyperlinked on the Reference cell
      "summary":    "What the source is and what it found, from having read it.",
      "role":       "The proposition it carries here, with a pin cite.",
      "quote":      "Complete sentence spanning the marker.",
      "section":    "Section heading from the manuscript",
      "accuracy":   "accurate" | "partial" | "issue" | "unverified",
      "acc_note":   "Required unless accuracy is 'accurate'.",
      "read_status":"full" | "partial: ..." | "paywalled" | "unreachable: ..."
    }

Usage
-----
    python build_table.py rows.json --out CitationTable.xlsx \\
        --title "Citation Table — Author (Year)" \\
        --notes notes.md
"""

import argparse
import json
import re
import sys

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError:
    sys.exit("openpyxl required:  pip install openpyxl --break-system-packages")


GLYPH = {
    "accurate":   "✓ Accurate",
    "partial":    "◐ Partial",
    "issue":      "⚠ Issue",
    "unverified": "○ Unverified",
}

# Column widths from the reference example. Accuracy is wider than the example's
# because every non-clean rating has to carry its explanation in the cell -- a
# bare glyph tells the reader a row is a problem without telling them what it is.
WIDTHS = {"A": 21.5, "B": 48.66, "C": 34.16, "D": 45.5, "E": 40.0}

FILL = {
    "accurate":   None,
    "partial":    PatternFill("solid", fgColor="FFF2CC"),
    "issue":      PatternFill("solid", fgColor="FCE4EC"),
    "unverified": PatternFill("solid", fgColor="EDEDED"),
}


def fn_label(fns):
    if not fns:
        return ""
    return ("fn " if len(fns) == 1 else "fns ") + ", ".join(str(f) for f in fns)


def citing_cell(r):
    """Quotation plus section and every footnote number the source appears at.

    Consolidating repeat citations into one row saves re-reading a source nine
    times, but it costs traceability unless every footnote number travels with
    the row. Listing them all -- not truncating with '+N more' -- is what lets
    someone check any single citation against the manuscript.
    """
    q = (r.get("quote") or "").strip().strip('"')
    sec = r.get("section") or ""
    bits = [b for b in (f"§{sec}" if sec else "", fn_label(r.get("fns", []))) if b]
    return f'"{q}" ({", ".join(bits)})' if bits else f'"{q}"'


def accuracy_cell(r):
    acc = (r.get("accuracy") or "unverified").strip().lower()
    glyph = GLYPH.get(acc, GLYPH["unverified"])
    if acc == "accurate":
        return glyph
    note = (r.get("acc_note") or "").strip()
    return f"{glyph} — {note}" if note else glyph


def sort_key(r):
    return re.sub(r"^[^A-Za-z]+", "", r.get("reference", "")).lower()


def build(rows, out, title, notes_text=None):
    rows = sorted(rows, key=sort_key)
    counts = {k: sum(1 for r in rows
                     if (r.get("accuracy") or "unverified").lower() == k)
              for k in GLYPH}

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Citations"

    thin = Side(border_style="thin", color="BFBFBF")
    bd = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")
    body_font = Font(name="Calibri", size=10)
    link_font = Font(name="Calibri", size=10, color="0563C1", underline="single")

    ws.merge_cells("A1:E1")
    ws["A1"] = title
    ws["A1"].font = Font(name="Calibri", bold=True, size=13)
    ws["A1"].alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 20

    ws.merge_cells("A2:E2")
    ws["A2"] = (
        f"{counts['accurate']} ✓ Accurate · {counts['partial']} ◐ Partial · "
        f"{counts['issue']} ⚠ Issue · {counts['unverified']} ○ Unverified.  "
        f"Total: {len(rows)} unique references (repeat citations consolidated; "
        f"every footnote number is listed in the citing-paragraph column).  "
        f"○ Unverified = source could not be read; the reason is stated in that "
        f"row's Accuracy cell."
    )
    ws["A2"].font = Font(name="Calibri", size=9, italic=True)
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = 50

    headers = ["Reference", "Summary", "Role in manuscript / result cited",
               "Citing paragraph(s)", "Accuracy"]
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=3, column=i, value=h)
        c.font = Font(name="Calibri", bold=True, size=11)
        c.fill = PatternFill("solid", fgColor="D9E2F3")
        c.border = bd
        c.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[3].height = 30

    for i, r in enumerate(rows):
        rw = i + 4
        a = ws.cell(row=rw, column=1, value=r.get("reference", ""))
        if r.get("url"):
            a.hyperlink = r["url"]
            a.font = link_font
        else:
            a.font = body_font
        a.alignment = wrap
        a.border = bd

        cc, ac = citing_cell(r), accuracy_cell(r)
        for col, val in ((2, r.get("summary", "")), (3, r.get("role", "")),
                         (4, cc), (5, ac)):
            c = ws.cell(row=rw, column=col, value=val)
            c.font = body_font
            c.alignment = wrap
            c.border = bd

        acc = (r.get("accuracy") or "unverified").lower()
        if FILL.get(acc):
            ws.cell(row=rw, column=5).fill = FILL[acc]

        longest = max(len(r.get("reference", "")) / 21.5,
                      len(r.get("summary", "")) / 48.7,
                      len(r.get("role", "")) / 34.2,
                      len(cc) / 45.5, len(ac) / 40)
        ws.row_dimensions[rw].height = max(30, min(230, longest * 13))

    for col, w in WIDTHS.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:E{3 + len(rows)}"

    if notes_text:
        n = wb.create_sheet("Notes")
        n["A1"] = "Method and coverage"
        n["A1"].font = Font(name="Calibri", bold=True, size=12)
        n["A2"] = notes_text
        n["A2"].alignment = Alignment(wrap_text=True, vertical="top")
        n["A2"].font = Font(name="Calibri", size=10)
        n.column_dimensions["A"].width = 118
        n.row_dimensions[2].height = 1000

    wb.save(out)
    print(f"Wrote {out}  ({len(rows)} rows)")
    print("  " + " · ".join(f"{v} {GLYPH[k]}" for k, v in counts.items()))
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rows")
    ap.add_argument("--out", default="CitationTable.xlsx")
    ap.add_argument("--title", default="Citation Table")
    ap.add_argument("--notes", help="path to a text/markdown file for the Notes sheet")
    a = ap.parse_args()
    rows = json.load(open(a.rows))
    notes = open(a.notes).read() if a.notes else None
    build(rows, a.out, a.title, notes)


if __name__ == "__main__":
    main()
