import json

import pytest

from conftest import REPORT_BLOCKS, make_docx
from pincite.pincheck import (
    Claim,
    check_claims,
    extract_facts,
    load_units,
    main,
    negative_control,
    parse_pin,
    scan_claims,
)


def test_docx_numbering_is_reconstructed_from_word_lists(report_docx):
    units = load_units(report_docx)
    paras = [u for u in units if u.kind == "para"]
    assert [u.number for u in paras] == [40, 41, 42, 43, 44]  # startOverride honored
    assert "disciplined price" in paras[1].text  # block quote attached to ¶ 41
    assert not any("Market Structure" in u.text for u in paras)  # headings are not paragraphs
    notes = [u for u in units if u.kind == "note"]
    assert notes[0].label == "n. 1" and "31 studies" in notes[0].text


def test_style_based_numbering(tmp_path):
    path = make_docx(tmp_path / "s.docx", REPORT_BLOCKS[:3], style_numbering=True)
    assert [u.number for u in load_units(path) if u.kind == "para"] == [1, 2]


def test_text_numbering_fallback(tmp_path):
    src = tmp_path / "r.txt"
    src.write_text("1. First point at 3 percent.\n2. Second point.\ncontinued 2019 line\n3. Third.\n")
    units = load_units(src)
    assert [u.number for u in units] == [1, 2, 3]
    assert "continued 2019 line" in units[1].text


@pytest.mark.parametrize(
    "pin,expected",
    [
        ("¶ 42", [("para", 42)]),
        ("¶¶ 42–44, 47", [("para", 42), ("para", 43), ("para", 44), ("para", 47)]),
        ("pp. 142–4", [("page", n) for n in (142, 143, 144)]),
        ("paras. 3-4", [("para", 3), ("para", 4)]),
        ("n. 17", [("note", 17)]),
    ],
)
def test_parse_pin(pin, expected):
    assert parse_pin(pin) == expected


def test_extract_facts_ignores_pin_numbers():
    nums, quotes = extract_facts("Prices fell 12.5% ($1,240) by 2019 (¶¶ 41–42; n. 1), “a sharp and sustained fall.”")
    assert nums == ["12.5%", "$1,240", "2019"]
    assert quotes == ["a sharp and sustained fall."]


def test_verified_wrong_pin_and_phantom_are_told_apart(report_docx):
    units = load_units(report_docx)
    claims = [
        Claim.from_dict({"pin": "¶ 41", "text": "Net prices fell 12.5%, or $1,240 per member."}),
        Claim.from_dict({"pin": "¶ 40", "text": "Pass-through averaged 87 percent."}),
        Claim.from_dict({"pin": "¶ 43", "text": "Pass-through averaged 91 percent."}),
        Claim.from_dict({"pin": "¶ 41", "quotes": ["Competition among the actual substitutes disciplined price"]}),
        Claim.from_dict({"pin": "¶ 99", "text": "Anything at 5 percent."}),
    ]
    results = check_claims(units, claims)
    by = {(r.claim.pin, r.fact): r for r in results}
    assert by[("¶ 41", "12.5%")].ok and by[("¶ 41", "$1,240")].ok
    assert not by[("¶ 40", "87")].ok and "found at ¶ 43" in by[("¶ 40", "87")].detail
    assert not by[("¶ 43", "91")].ok and "not found anywhere" in by[("¶ 43", "91")].detail
    assert by[("¶ 41", "Competition among the actual substitutes disciplined price")].ok
    assert any(r.kind == "pin" and not r.ok and "past the source" in r.detail for r in results)


def test_quote_with_ellipsis_matches_segments_in_order(report_docx):
    units = load_units(report_docx)
    ok = check_claims(units, [Claim(pin="¶ 41", quotes=["Average net prices fell … a decline of $1,240"])])
    bad = check_claims(units, [Claim(pin="¶ 41", quotes=["a decline of $1,240 … Average net prices fell"])])
    assert ok[0].ok and not bad[0].ok


def test_negative_control_catches_every_corruption(report_docx):
    units = load_units(report_docx)
    claims = [
        Claim.from_dict({"pin": "¶ 40", "text": "From 2015 through 2019, 412 plans."}),
        Claim.from_dict({"pin": "¶ 41", "text": "Prices fell 12.5% (“a decline of $1,240 per member”)."}),
    ]
    caught, tried, notes = negative_control(units, claims, n=4)
    assert tried == 4 and caught == 4, notes


def test_scan_a_rendered_sheet(report_docx, tmp_path):
    sheet = tmp_path / "sheet.md"
    sheet.write_text(
        "# Section III\n\nNet prices fell 12.5% over the period (¶ 41). "
        "Pass-through averaged 87 percent on the sample plans (¶ 43).\n\n"
        "| Subsection | The point | ¶¶ |\n|---|---|---|\n| Prices | A $1,240 decline per member | ¶ 42 |\n"
    )
    claims = scan_claims(sheet)
    results = check_claims(load_units(report_docx), claims)
    failed = [r for r in results if not r.ok]
    assert len(claims) >= 3
    assert [r.fact for r in failed] == ["$1,240"] and "found at ¶ 41" in failed[0].detail


def test_cli_exit_codes(report_docx, tmp_path, capsys):
    good = tmp_path / "good.json"
    good.write_text(json.dumps([{"pin": "¶ 41", "text": "Prices fell 12.5%."}]))
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([{"pin": "¶ 41", "text": "Prices fell 14%."}]))
    assert main(["check", str(report_docx), "--claims", str(good), "--negative-control", "1"]) == 0
    assert main(["check", str(report_docx), "--claims", str(bad)]) == 1
    assert main(["units", str(report_docx), "--expect-count", "5"]) == 0
    assert main(["units", str(report_docx), "--expect-count", "6"]) == 1
    out = capsys.readouterr().out
    assert "negative control: 1/1 corruptions caught" in out
    assert "MISMATCH" in out


def test_scan_rendered_pdf_keeps_table_rows_apart(report_docx, tmp_path):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table

    sheet = tmp_path / "sheet.pdf"
    style = getSampleStyleSheet()["Normal"]
    SimpleDocTemplate(str(sheet), pagesize=letter).build(
        [
            Paragraph(
                "Net prices fell 12.5% over the study period (¶ 41). Pass-through averaged 87 percent (¶ 43).", style
            ),
            Table(
                [
                    ["Subsection", "The point", "¶¶"],
                    ["Prices", "A $1,240 decline per member", "¶ 41"],
                    ["Pass-through", "Measured on 412 plans", "¶ 43"],
                ]
            ),
        ]
    )
    results = check_claims(load_units(report_docx), scan_claims(sheet))
    failed = [(r.fact, r.detail) for r in results if not r.ok]
    assert failed == [("412", "not at ¶ 43; found at ¶ 40")]
    assert sum(r.ok for r in results) == 3
