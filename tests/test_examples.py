"""The shipped examples must keep working exactly as examples/README.md says."""

from conftest import ROOT
from pincite import qc, sweep
from pincite.pincheck import check_claims, load_units, negative_control, scan_claims
from pincite.workbook import build, load_spec


def test_citation_table_example_builds_clean(tmp_path):
    spec, rows = load_spec(ROOT / "examples/citation-table/spec.json")
    out = tmp_path / "SA.xlsx"
    assert build(spec, rows, out)["rows"] == 3
    assert sweep.sweep(out) == []
    assert qc.qc(out) == []


def test_pincheck_example_finds_exactly_the_planted_error():
    units = load_units(ROOT / "examples/pincheck/report.txt")
    claims = scan_claims(ROOT / "examples/pincheck/sheet.md")
    failed = [(r.fact, r.detail) for r in check_claims(units, claims) if not r.ok]
    assert failed == [("412", "not at ¶ 43; found at ¶ 40")]
    caught, tried, _ = negative_control(units, claims, 6)
    assert caught == tried >= 4
