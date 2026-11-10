import json

import openpyxl
import pytest

from conftest import supporting_rows, supporting_spec
from pincite.workbook import SpecError, build, main


def test_supporting_layout_matches_schema(supporting_workbook):
    wb = openpyxl.load_workbook(supporting_workbook)
    assert wb.sheetnames == ["Supporting Authority", "Detail", "Method"]
    ws = wb["Supporting Authority"]
    assert ws.freeze_panes == "C4"
    assert ws["A1"].value == "Supporting Authority — Synthetic Report"
    headers = [ws.cell(3, c).value for c in range(1, 14)]
    assert headers[0] == "ID" and headers[-1] == "In draft (2026-01-15)"
    assert ws["A3"].fill.fgColor.rgb.endswith("D9E2F3")
    assert ws.column_dimensions["H"].width == 38
    # section bands, in TOC order, with rows sorted by relevance inside each
    col_a = [ws.cell(r, 1).value for r in range(4, ws.max_row + 1)]
    assert col_a == ["§ III.A — Market Structure", "S01", "S02", "§ III.B — Pass-Through", "S03"]
    assert ws["A4"].fill.fgColor.rgb.endswith("1F4E79")
    assert ws.cell(5, 2).hyperlink.target.startswith("https://doi.org/")
    assert ws.cell(5, 11).fill.fgColor.rgb.endswith("FFE699")
    assert ws.cell(6, 13).value == "Not yet cited"  # dated key canonicalized to "In draft"


def test_detail_and_method_sheets(supporting_workbook):
    wb = openpyxl.load_workbook(supporting_workbook)
    assert [wb["Detail"].cell(r, 1).value for r in range(2, 5)] == ["S01", "S02", "S03"]
    method = [c.value for c in wb["Method"]["A"] if c.value]
    labels = [v for v in method if v.isupper()]
    assert labels == [
        "METHOD AND COVERAGE",
        "READING AND VERIFICATION STANDARD",
        "COVERAGE AND ORGANIZATION",
        "NOTES ON VERIFICATION LABELS",
        "SOURCE-SPECIFIC NOTES",
    ]
    assert "2 are cited in the draft dated 2026-01-15; 1 are not yet cited" in method[1]


def test_unknown_keys_are_rejected_not_guessed(tmp_path):
    rows = supporting_rows()
    rows[0]["claim_supported"] = "x"
    with pytest.raises(SpecError, match="unknown key 'claim_supported'"):
        build(supporting_spec(), rows, tmp_path / "t.xlsx")
    ok = build(supporting_spec(), rows, tmp_path / "t.xlsx", aliases={"claim_supported": "Claim it supports"})
    assert ok["rows"] == 3


def test_invented_sections_and_bad_relevance_fail(tmp_path):
    rows = supporting_rows()
    rows[0]["section"] = "VIII.B"
    rows[1]["Relevance"] = 7
    with pytest.raises(SpecError) as e:
        build(supporting_spec(), rows, tmp_path / "t.xlsx")
    assert "Relevance must be an integer 1–5" in str(e.value)


def test_no_current_anchor_group_is_last(tmp_path):
    rows = supporting_rows()
    rows[0]["section"] = "NO CURRENT ANCHOR"
    build(supporting_spec(), rows, tmp_path / "t.xlsx")
    ws = openpyxl.load_workbook(tmp_path / "t.xlsx")["Supporting Authority"]
    assert ws.cell(ws.max_row - 1, 1).value.startswith("NO CURRENT ANCHOR")
    assert ws.cell(ws.max_row, 1).value == "S01"


def _audit_rows():
    base = {
        "Reference": "Delta, D. (2019). A study. Journal, 1, 1–9.",
        "hyperlink": "https://doi.org/10.0000/x",
        "Summary": "A panel study of supply markets, read in full.",
        "Role in manuscript / result cited": "Supports the entry effect at ¶ 41.",
        "Citing paragraph(s)": '"Prices fell after entry." (§III.A, fns 3, 9)',
        "Limitations / conflicts / later rebuttals": "Industry funded; disclosed at p. 2.",
    }
    return [
        {**base, "ID": "A01", "accuracy": "accurate"},
        {**base, "ID": "A02", "accuracy": "partial", "acc_note": "supports the direction, not the size"},
    ]


def test_audit_mode_tally_glyphs_and_notes(tmp_path):
    out = tmp_path / "audit.xlsx"
    build(
        {"mode": "audit", "title": "Citation Table — Synthetic", "hard_errors": ["fn 9 → 12% → source says 21%"]},
        _audit_rows(),
        out,
    )
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Citations", "Notes"]
    ws = wb["Citations"]
    assert ws["A2"].value.startswith("1 ✓ Accurate · 1 ◐ Partial · 0 ⚠ Issue · 0 ○ Unverified")
    assert ws.cell(5, 6).value == "◐ Partial — supports the direction, not the size"
    notes = [c.value for c in wb["Notes"]["A"] if c.value]
    assert "HARD ERRORS FOUND" in notes and "fn 9 → 12% → source says 21%" in notes


def test_audit_bare_glyph_is_refused(tmp_path):
    rows = _audit_rows()
    rows[1].pop("acc_note")
    with pytest.raises(SpecError, match="bare glyphs are forbidden"):
        build({"mode": "audit"}, rows, tmp_path / "a.xlsx")


def test_adverse_and_opposing_modes(tmp_path):
    adverse = [
        {
            "ID": "A01",
            "Citation": "Epsilon (2021).",
            "hyperlink": "https://example.org/a",
            "What this source is": "A study.",
            "What it finds": "Higher prices.",
            "Why it cuts against us": "Opposite sign.",
            "Anticipation strategy (how the report should meet it)": "Distinguish the sample.",
            "Limitations / conflicts / later rebuttals": "Small sample.",
            "Section it bears on": "III.A",
            "Credibility": "Working paper",
            "detail_rationale": "Opposing counsel will cite it.",
        }
    ]
    build({"mode": "adverse", "title": "Adverse"}, adverse, tmp_path / "adv.xlsx")
    wb = openpyxl.load_workbook(tmp_path / "adv.xlsx")
    assert wb.sheetnames == ["Adverse Evidence", "Detail", "Notes"]
    assert "opposing counsel has these" in wb["Adverse Evidence"]["A2"].value
    assert wb["Detail"]["C2"].value == "Opposing counsel will cite it."

    opp = [
        {
            "ID": "O01",
            "Citation": "Zeta (2018).",
            "hyperlink": "https://example.org/z",
            "Relevance": 4,
            "Rebuttal available": "S01",
        }
    ]
    method = {
        k: "x."
        for k in (
            "READING AND VERIFICATION STANDARD",
            "COVERAGE AND ORGANIZATION",
            "NOTES ON VERIFICATION LABELS",
            "SOURCE-SPECIFIC NOTES",
        )
    }
    build({"mode": "opposing", "method": method}, opp, tmp_path / "opp.xlsx")
    assert openpyxl.load_workbook(tmp_path / "opp.xlsx").sheetnames == ["Opposing Citations", "Detail", "Method"]


def test_cli_reads_a_directory_of_row_files(tmp_path, capsys):
    rows_dir = tmp_path / "rows"
    rows_dir.mkdir()
    for r in supporting_rows():
        (rows_dir / f"{r['ID']}.json").write_text(json.dumps(r))
    spec = supporting_spec("rows")
    spec["out"] = "out/table.xlsx"
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    assert main([str(tmp_path / "spec.json"), "--out", str(tmp_path / "out" / "t.xlsx")]) == 0
    assert "Reload verification passed" in capsys.readouterr().out
    (tmp_path / "bad.json").write_text(json.dumps({"mode": "nope"}))
    assert main([str(tmp_path / "bad.json")]) == 2
