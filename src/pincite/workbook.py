#!/usr/bin/env python3
"""
Build a citation-table workbook from row JSON, to the schema in references/schema.md.

One builder for every mode the skill ships:

    supporting  Mode B  Supporting Authority + Detail + Method   (13 columns)
    audit       Mode A  Citations + Notes (+ Detail)              (7 columns)
    opposing    Mode C  Opposing Citations + Detail + Method      (13 columns)
    adverse     internal companion: Adverse Evidence + Detail + Notes

Design rules this file enforces rather than documents:

  * The workbook is always rebuilt from a model, never patched. openpyxl's
    insert_rows/delete_rows silently corrupt sheets with merged rows, so this
    builder never calls them.
  * Row JSON keys are the exact column headers. A key the schema does not know
    is an error, not a guess: a drafting agent that emits nonconforming keys is
    re-run, never silently mapped. (Pass --aliases to map known variants.)
  * IDs are assigned upstream and never renumbered here. Gaps stay gaps.
  * The result is verified by reloading the saved file, not by trusting the
    write.

Usage
-----
    python build_workbook.py spec.json
    python build_workbook.py spec.json --out Table.xlsx --aliases aliases.json

spec.json
---------
    {
      "mode": "supporting",
      "title": "Additional Supporting Literature — Defense Expert Report",
      "note": "Every source was opened and read in full ...",
      "draft_date": "2026-08-17",
      "sections": [{"key": "III.A", "heading": "Exact heading from the TOC"}],
      "rows": "rows/",                 # a directory of <ID>.json, or a list
      "method": {"READING AND VERIFICATION STANDARD": "..."},
      "out": "Supporting_Authority.xlsx"
    }

Each row also carries "section" (a key from "sections", or the literal
"NO CURRENT ANCHOR"), "hyperlink", and optional "credibility_class" (1 = top
journal ... 5 = advocacy/press) used for sorting.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    sys.exit("openpyxl required:  pip install openpyxl")

__all__ = ["MODES", "build", "load_spec", "main"]

# ----------------------------------------------------------------- the schema

DARK = "1F4E79"
HEADER_FILL = "D9E2F3"
RELEVANCE_FILL = "FFE699"
LINK = "0563C1"
NO_ANCHOR = "NO CURRENT ANCHOR"
NO_ANCHOR_TEXT = "NO CURRENT ANCHOR — included for completeness; not recommended for citation in the report"

GLYPH = {
    "accurate": "✓ Accurate",
    "partial": "◐ Partial",
    "issue": "⚠ Issue",
    "unverified": "○ Unverified",
}
GLYPH_FILL = {"partial": "FFF2CC", "issue": "FCE4EC", "unverified": "EDEDED"}

DETAIL_HEADERS = [
    "ID",
    "Full abstract (or written summary where none published)",
    "Relevance rationale (case fit)",
    "Reading/verification notes",
]
DETAIL_WIDTHS = [8, 110, 60, 50]
DETAIL_KEYS = ["detail_abstract", "detail_relevance_rationale", "detail_verification_notes"]

META_KEYS = {
    "section",
    "hyperlink",
    "read_depth",
    "flags",
    "credibility_class",
    "detail_abstract",
    "detail_relevance_rationale",
    "detail_rationale",
    "detail_verification_notes",
    "accuracy",
    "acc_note",
}

METHOD_SECTIONS = [
    "METHOD AND COVERAGE",
    "READING AND VERIFICATION STANDARD",
    "COVERAGE AND ORGANIZATION",
    "NOTES ON VERIFICATION LABELS",
    "SOURCE-SPECIFIC NOTES",
]
AUDIT_NOTES_SECTIONS = [
    "SOURCE PAPER",
    "EXTRACTION",
    "DEDUPLICATION",
    "READING",
    "ACCURACY RATINGS",
    "RECURRING PATTERNS",
    "HARD ERRORS FOUND",
]
ACCURACY_DEFINITIONS = (
    "✓ Accurate: the source says what the manuscript cites it for, at the strength claimed. "
    "◐ Partial: the source supports part of the proposition, or supports it more weakly than stated. "
    "⚠ Issue: the citation is wrong, the quotation is altered, or the source does not support the "
    "proposition. ○ Unverified: the source could not be read; the reason is stated on the row and no "
    "accuracy judgment is asserted."
)


@dataclass(frozen=True)
class Mode:
    name: str
    sheet: str
    headers: list[str]
    widths: list[float]
    freeze: str
    side_sheets: tuple[str, ...]
    note: str = ""
    relevance_col: str | None = None
    required: frozenset[str] = field(default_factory=frozenset)


SUPPORTING = Mode(
    name="supporting",
    sheet="Supporting Authority",
    headers=[
        "ID",
        "Citation",
        "What this source is",
        "Claim it supports",
        "How we would use it",
        "Findings",
        "Proposed excerpt (verbatim)",
        "Limitations / conflicts / later rebuttals",
        "Data",
        "Methods / test",
        "Relevance",
        "Credibility",
        "In draft",
    ],
    widths=[6, 36, 34, 34, 36, 38, 38, 38, 30, 28, 9, 26, 30],
    freeze="C4",
    side_sheets=("Detail", "Method"),
    relevance_col="Relevance",
)

AUDIT = Mode(
    name="audit",
    sheet="Citations",
    headers=[
        "ID",
        "Reference",
        "Summary",
        "Role in manuscript / result cited",
        "Citing paragraph(s)",
        "Accuracy",
        "Limitations / conflicts / later rebuttals",
    ],
    widths=[6, 40, 44, 40, 48, 34, 44],
    freeze="C4",
    side_sheets=("Notes", "Detail"),
)

OPPOSING = Mode(
    name="opposing",
    sheet="Opposing Citations",
    headers=[
        "ID",
        "Citation",
        "What this source is",
        "How they use it / what it actually proves",
        "Their quote vs. the source",
        "Weaknesses",
        "Limitations / conflicts / later rebuttals",
        "Data",
        "Methods / test",
        "Relevance",
        "Rebuttal available",
        "Section of their report",
        "Credibility",
    ],
    widths=[6, 36, 32, 40, 42, 34, 38, 30, 28, 9, 30, 22, 26],
    freeze="C4",
    side_sheets=("Detail", "Method"),
    relevance_col="Relevance",
)

ADVERSE = Mode(
    name="adverse",
    sheet="Adverse Evidence",
    headers=[
        "ID",
        "Citation",
        "What this source is",
        "What it finds",
        "Why it cuts against us",
        "Anticipation strategy (how the report should meet it)",
        "Limitations / conflicts / later rebuttals",
        "Section it bears on",
        "Credibility",
    ],
    widths=[6, 36, 30, 42, 42, 42, 38, 18, 26],
    freeze="C4",
    side_sheets=("Detail", "Notes"),
    note=(
        "Recorded because opposing counsel has these; the report is better off meeting them "
        "than being met with them. All rows read in full."
    ),
)

MODES = {m.name: m for m in (SUPPORTING, AUDIT, OPPOSING, ADVERSE)}

# Credibility classes, high to low, for sorting when a row gives no explicit class.
CREDIBILITY_PATTERNS = [
    (1, r"top|flagship|general[- ]science|econometrica|american economic review|nejm|jama\b|lancet"),
    (2, r"peer[- ]reviewed (field )?journal|peer-reviewed article|journal"),
    (3, r"government|agency|gao|oig|cdc|nchs|cbo|congress|federal"),
    (4, r"working paper|nber|ssrn|commentary|preprint"),
    (5, r"policy|consult|advocacy|press|trade|industry|news"),
]


def credibility_class(row: dict) -> int:
    explicit = row.get("credibility_class")
    if isinstance(explicit, int) and 1 <= explicit <= 5:
        return explicit
    label = str(row.get("Credibility", "")).lower()
    for rank, pat in CREDIBILITY_PATTERNS:
        if re.search(pat, label):
            return rank
    return 5


# ------------------------------------------------------------------ loading


class SpecError(ValueError):
    """The spec or a row breaks the schema contract."""


def load_rows(source, base: Path) -> list[dict]:
    if isinstance(source, list):
        return source
    path = (base / source).resolve()
    if path.is_dir():
        files = sorted(path.glob("*.json"))
        if not files:
            raise SpecError(f"no row JSON files in {path}")
        return [json.loads(f.read_text(encoding="utf-8")) for f in files]
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SpecError(f"{path} must hold a JSON array of rows")
    return data


def load_spec(path: str | Path) -> tuple[dict, list[dict]]:
    path = Path(path)
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("mode") not in MODES:
        raise SpecError(f"mode must be one of {sorted(MODES)}, got {spec.get('mode')!r}")
    rows = load_rows(spec.get("rows", []), path.parent)
    return spec, rows


def canonicalize(rows: list[dict], mode: Mode, aliases: dict[str, str] | None = None) -> list[dict]:
    """Enforce the row-JSON contract: exact headers plus known meta keys only."""
    aliases = aliases or {}
    known = set(mode.headers) | META_KEYS
    out, problems = [], []
    seen_ids: set[str] = set()
    for i, raw in enumerate(rows):
        row = {}
        for k, v in raw.items():
            k2 = aliases.get(k, k)
            if mode.name == "supporting" and re.fullmatch(r"In draft.*", k2):
                k2 = "In draft"
            if k2 not in known:
                problems.append(f"row {raw.get('ID', i)}: unknown key {k!r}")
                continue
            row[k2] = v
        rid = str(row.get("ID", "")).strip()
        if not rid:
            problems.append(f"row {i}: missing ID")
        elif rid in seen_ids:
            problems.append(f"row {rid}: duplicate ID")
        seen_ids.add(rid)
        if mode.relevance_col and row.get(mode.relevance_col) not in (None, ""):
            try:
                rel = int(row[mode.relevance_col])
            except (TypeError, ValueError):
                rel = -1
            if not 1 <= rel <= 5:
                problems.append(f"row {rid}: Relevance must be an integer 1–5")
            else:
                row[mode.relevance_col] = rel
        if mode.name == "audit":
            acc = str(row.get("accuracy") or row.get("Accuracy") or "unverified").strip().lower()
            acc = {"✓": "accurate", "◐": "partial", "⚠": "issue", "○": "unverified"}.get(acc[:1], acc)
            if acc not in GLYPH:
                problems.append(f"row {rid}: accuracy must be one of {sorted(GLYPH)}")
                acc = "unverified"
            note = str(row.get("acc_note") or "").strip()
            if acc != "accurate" and not note and " — " not in str(row.get("Accuracy", "")):
                problems.append(f"row {rid}: a {acc} rating needs acc_note (bare glyphs are forbidden)")
            row["accuracy"] = acc
            row["Accuracy"] = GLYPH[acc] + (f" — {note}" if note and acc != "accurate" else "")
        out.append(row)
    if problems:
        raise SpecError("row contract violations:\n  " + "\n  ".join(problems))
    return out


# ----------------------------------------------------------------- building

THIN = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP_TOP = Alignment(wrap_text=True, vertical="top")
BODY = Font(name="Calibri", size=10)
BOLD = Font(name="Calibri", size=10, bold=True)
LINK_FONT = Font(name="Calibri", size=10, color=LINK, underline="single")


def _title_rows(ws, ncols: int, title: str, note: str) -> None:
    last = get_column_letter(ncols)
    ws.merge_cells(f"A1:{last}1")
    ws["A1"] = title
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    ws["A1"].alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 24
    ws.merge_cells(f"A2:{last}2")
    ws["A2"] = note
    ws["A2"].font = Font(name="Calibri", size=9, italic=True)
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = max(30, 12 * (1 + len(note) // 260))


def _header_row(ws, headers: list[str], row: int = 3) -> None:
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font = Font(name="Calibri", size=10, bold=True)
        cell.fill = PatternFill("solid", fgColor=HEADER_FILL)
        cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
        cell.border = BORDER


def _band(ws, row: int, ncols: int, text: str) -> None:
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=DARK)
    cell.alignment = Alignment(vertical="center")
    ws.row_dimensions[row].height = 18


def _row_height(row: dict, headers: list[str], widths: list[float]) -> float:
    lines = 1
    for h, w in zip(headers, widths, strict=False):
        text = str(row.get(h, "") or "")
        est = sum(max(1, -(-len(part) // max(1, int(w * 1.15)))) for part in text.split("\n"))
        lines = max(lines, est)
    return min(409, max(52, 13 * lines))


def _write_data_row(ws, r: int, row: dict, mode: Mode) -> None:
    for c, h in enumerate(mode.headers, 1):
        cell = ws.cell(row=r, column=c, value=row.get(h, ""))
        cell.alignment = WRAP_TOP
        cell.border = BORDER
        cell.font = BODY
        if h == "ID":
            cell.font = BOLD
        elif c == 2 and row.get("hyperlink"):
            cell.hyperlink = row["hyperlink"]
            cell.font = LINK_FONT
        elif h == mode.relevance_col:
            cell.fill = PatternFill("solid", fgColor=RELEVANCE_FILL)
            cell.alignment = Alignment(horizontal="center", vertical="top")
        elif h == "Accuracy" and row.get("accuracy") in GLYPH_FILL:
            cell.fill = PatternFill("solid", fgColor=GLYPH_FILL[row["accuracy"]])
    ws.row_dimensions[r].height = _row_height(row, mode.headers, mode.widths)


def _sort_key(mode: Mode):
    def key(row: dict):
        rel = row.get(mode.relevance_col, 0) if mode.relevance_col else 0
        first_author = re.sub(r"^[^A-Za-z]+", "", str(row.get("Citation") or row.get("Reference") or ""))
        return (-(rel or 0), credibility_class(row), first_author.lower(), str(row.get("ID")))

    return key


def _group(rows: list[dict], sections: list[dict]) -> list[tuple[str | None, list[dict]]]:
    if not sections:
        return [(None, rows)]
    order = [s["key"] for s in sections]
    heading = {s["key"]: s.get("heading", "") for s in sections}
    buckets: dict[str, list[dict]] = {k: [] for k in order}
    anchorless, problems = [], []
    for row in rows:
        key = row.get("section")
        if key == NO_ANCHOR:
            anchorless.append(row)
        elif key in buckets:
            buckets[key].append(row)
        else:
            problems.append(f"row {row.get('ID')}: section {key!r} is not in the spec's TOC")
    if problems:
        raise SpecError("section keys must come from the manuscript's actual TOC:\n  " + "\n  ".join(problems))
    groups: list[tuple[str | None, list[dict]]] = []
    for k in order:
        if buckets[k]:
            label = f"§ {k} — {heading[k]}" if heading[k] else f"§ {k}"
            groups.append((label, buckets[k]))
    if anchorless:
        groups.append((NO_ANCHOR_TEXT, anchorless))
    return groups


def _prose_sheet(wb, name: str, blocks: list[tuple[str, str]], width: int = 120) -> None:
    ws = wb.create_sheet(name)
    ws.column_dimensions["A"].width = width
    r = 1
    for label, body in blocks:
        cell = ws.cell(row=r, column=1, value=label)
        cell.font = Font(name="Calibri", size=11, bold=True, color=DARK)
        r += 1
        cell = ws.cell(row=r, column=1, value=body)
        cell.font = BODY
        cell.alignment = WRAP_TOP
        ws.row_dimensions[r].height = max(15, 13.5 * (1 + len(body) // 150))
        r += 2


def _detail_sheet(wb, rows: list[dict], adverse: bool) -> None:
    ws = wb.create_sheet("Detail")
    _header_row(ws, DETAIL_HEADERS, row=1)
    for i, w in enumerate(DETAIL_WIDTHS, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "B2"
    for r, row in enumerate(rows, 2):
        rationale = row.get("detail_rationale" if adverse else "detail_relevance_rationale") or row.get(
            "detail_relevance_rationale", ""
        )
        vals = [row.get("ID"), row.get("detail_abstract", ""), rationale, row.get("detail_verification_notes", "")]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = BOLD if c == 1 else BODY
            cell.alignment = WRAP_TOP
            cell.border = BORDER


def _method_blocks(spec: dict, rows: list[dict], mode: Mode) -> list[tuple[str, str]]:
    given = dict(spec.get("method") or {})
    if "METHOD AND COVERAGE" not in given:
        n = len(rows)
        extra = ""
        if mode.name == "supporting":
            cited = sum(1 for r in rows if str(r.get("In draft", "")).lower().startswith("cited"))
            extra = f" {cited} are cited in the draft dated {spec.get('draft_date', '(date not given)')}; {n - cited} are not yet cited."
        given["METHOD AND COVERAGE"] = (
            f"This workbook holds {n} source row{'s' if n != 1 else ''} on the {mode.sheet} sheet, "
            f"with one Detail row per source.{extra}"
        )
    missing = [s for s in METHOD_SECTIONS if s not in given]
    if missing:
        raise SpecError("method text missing required sections: " + ", ".join(missing))
    return [(s, str(given[s])) for s in METHOD_SECTIONS]


def _audit_notes(spec: dict, rows: list[dict]) -> list[tuple[str, str]]:
    given = dict(spec.get("notes") or {})
    given.setdefault("ACCURACY RATINGS", ACCURACY_DEFINITIONS)
    if "READING" not in given:
        depth: dict[str, int] = {}
        for r in rows:
            d = str(r.get("read_depth") or "unrecorded").split(":")[0]
            depth[d] = depth.get(d, 0) + 1
        given["READING"] = "Read depth by source: " + "; ".join(f"{k} {v}" for k, v in sorted(depth.items())) + "."
    given.setdefault(
        "SOURCE PAPER", str(spec.get("source_paper") or spec.get("title") or "The manuscript under audit.")
    )
    given.setdefault(
        "EXTRACTION",
        "Every footnote was extracted from the manuscript with its in-text marker "
        "position; each citing sentence was then read in context.",
    )
    given.setdefault(
        "DEDUPLICATION",
        "One row per unique source, matched on normalized first author, year and "
        "title. Near-matches were judged by hand, never merged automatically.",
    )
    given.setdefault("RECURRING PATTERNS", "None recorded.")
    hard = spec.get("hard_errors") or []
    if "HARD ERRORS FOUND" not in given:
        given["HARD ERRORS FOUND"] = "\n".join(hard) if hard else "None found."
    missing = [s for s in AUDIT_NOTES_SECTIONS if s not in given]
    if missing:
        raise SpecError("audit notes missing required sections: " + ", ".join(missing))
    return [(s, str(given[s])) for s in AUDIT_NOTES_SECTIONS]


def build(spec: dict, rows: list[dict], out: str | Path, aliases: dict[str, str] | None = None) -> dict:
    """Build the workbook and return a verification summary from the reloaded file."""
    mode = MODES[spec["mode"]]
    rows = canonicalize(rows, mode, aliases)
    headers = list(mode.headers)
    if mode.name == "supporting":
        headers[-1] = f"In draft ({spec['draft_date']})" if spec.get("draft_date") else "In draft"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = mode.sheet
    ncols = len(headers)

    if mode.name == "audit":
        counts = {k: sum(1 for r in rows if r["accuracy"] == k) for k in GLYPH}
        note = (
            f"{counts['accurate']} ✓ Accurate · {counts['partial']} ◐ Partial · {counts['issue']} ⚠ Issue · "
            f"{counts['unverified']} ○ Unverified. Total: {len(rows)} unique references."
        )
    else:
        note = (
            spec.get("note")
            or mode.note
            or (
                "Every source in this table was opened and read in full. Rows are grouped by the "
                "report's actual table of contents. The excerpt column is verbatim. Relevance measures "
                "fit to this case, not venue prestige."
            )
        )
    _title_rows(ws, ncols, spec.get("title") or mode.sheet, note)
    _header_row(ws, headers)
    for i, w in enumerate(mode.widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = mode.freeze

    r = 4
    ordered: list[dict] = []
    for label, group in _group(rows, spec.get("sections") or []):
        if label:
            _band(ws, r, ncols, label)
            r += 1
        for row in sorted(group, key=_sort_key(mode)):
            row = dict(row)
            if mode.name == "supporting":
                row[headers[-1]] = row.get("In draft", "")
            _write_data_row(ws, r, row, mode if mode.name != "supporting" else _with_headers(mode, headers))
            ordered.append(row)
            r += 1

    if "Detail" in mode.side_sheets and (mode.name != "audit" or any(k in rw for rw in rows for k in DETAIL_KEYS)):
        _detail_sheet(wb, ordered, adverse=mode.name == "adverse")
    if "Method" in mode.side_sheets:
        _prose_sheet(wb, "Method", _method_blocks(spec, rows, mode))
    if "Notes" in mode.side_sheets:
        if mode.name == "audit":
            _prose_sheet(wb, "Notes", _audit_notes(spec, rows))
        else:
            _prose_sheet(
                wb,
                "Notes",
                [
                    ("PROVENANCE", str(spec.get("provenance", "Built from verified row JSON."))),
                    (
                        "INTENDED USE",
                        str(
                            spec.get(
                                "intended_use",
                                "Internal only. Delivered to the user alongside the main workbook; never to third parties.",
                            )
                        ),
                    ),
                ],
            )

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return verify(out, mode, [str(x.get("ID")) for x in ordered])


def _with_headers(mode: Mode, headers: list[str]) -> Mode:
    return Mode(
        mode.name, mode.sheet, headers, mode.widths, mode.freeze, mode.side_sheets, mode.note, mode.relevance_col
    )


def verify(path: str | Path, mode: Mode, expected_ids: list[str]) -> dict:
    """Reload the saved file and confirm what was written is what was meant."""
    wb = openpyxl.load_workbook(path)
    ws = wb[mode.sheet]
    ids = [
        str(ws.cell(r, 1).value)
        for r in range(4, ws.max_row + 1)
        if ws.cell(r, 1).value is not None and not str(ws.cell(r, 1).value).startswith(("§", "NO CURRENT"))
    ]
    problems = []
    if ids != expected_ids:
        problems.append(f"row IDs on reload {ids} differ from the model {expected_ids}")
    links = sum(1 for r in range(4, ws.max_row + 1) if ws.cell(r, 2).hyperlink)
    if "Detail" in wb.sheetnames:
        detail_ids = [str(wb["Detail"].cell(r, 1).value) for r in range(2, wb["Detail"].max_row + 1)]
        if sorted(detail_ids) != sorted(ids):
            problems.append("Detail sheet IDs are not one-to-one with the main sheet")
    if problems:
        raise SpecError("reload verification failed:\n  " + "\n  ".join(problems))
    return {"path": str(path), "sheets": wb.sheetnames, "rows": len(ids), "hyperlinked": links}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="build spec JSON")
    ap.add_argument("--out", help="output .xlsx (overrides spec 'out')")
    ap.add_argument("--aliases", help="JSON map of nonconforming key -> canonical header")
    a = ap.parse_args(argv)
    try:
        spec, rows = load_spec(a.spec)
        aliases = json.loads(Path(a.aliases).read_text()) if a.aliases else None
        out = a.out or spec.get("out") or f"{MODES[spec['mode']].sheet.replace(' ', '_')}.xlsx"
        summary = build(spec, rows, out, aliases)
    except SpecError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(
        f"Wrote {summary['path']}: {summary['rows']} rows, {summary['hyperlinked']} hyperlinked, "
        f"sheets {', '.join(summary['sheets'])}. Reload verification passed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
