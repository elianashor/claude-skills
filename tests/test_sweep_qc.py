import openpyxl

from pincite import qc, sweep


def _set(path, sheet, ref, value):
    wb = openpyxl.load_workbook(path)
    wb[sheet][ref] = value
    wb.save(path)


def test_clean_workbook_passes_both_gates(supporting_workbook):
    assert sweep.sweep(supporting_workbook) == []
    assert [f for f in qc.qc(supporting_workbook) if f.severity == "ERROR"] == []


def test_sweep_catches_truncation_and_artifacts(supporting_workbook):
    _set(
        supporting_workbook,
        "Supporting Authority",
        "F5",
        "Prices fell 9.1% within two years of entry across all regional markets, and the headline com",
    )
    _set(supporting_workbook, "Supporting Authority", "J5", "TODO: confirm method")
    codes = {code for _, code, _ in sweep.sweep(supporting_workbook)}
    assert {"TRUNC-PUNCT", "TRUNC-MIDWORD", "ARTIFACT"} <= codes


def test_sweep_detail_mismatch_and_accept_file(supporting_workbook, tmp_path, capsys):
    _set(supporting_workbook, "Detail", "A4", "S99")
    findings = sweep.sweep(supporting_workbook)
    assert ("Detail", "ID-MISMATCH") in {(loc, code) for loc, code, _ in findings}
    accept = tmp_path / "accept.txt"
    accept.write_text("Detail ID-MISMATCH  consciously accepted for the test\n")
    assert sweep.main([str(supporting_workbook), "--accept", str(accept)]) == 0
    assert "(accepted)" in capsys.readouterr().out


def test_qc_semantic_failures(supporting_workbook):
    ws_name = "Supporting Authority"
    _set(supporting_workbook, ws_name, "G5", "“prices fell by 9.1 percent within two years of entr…”")
    _set(supporting_workbook, ws_name, "E6", "Background per the QC pass; add to the pull list.")
    _set(supporting_workbook, ws_name, "K8", 9)
    _set(supporting_workbook, ws_name, "L8", "Top-5 economics journal")
    codes = {f.code for f in qc.qc(supporting_workbook)}
    assert {"QUOTE-MIDWORD", "RESIDUE", "RELEVANCE", "VENUE-INFLATION"} <= codes


def test_qc_unread_but_rated_and_bare_flag(tmp_path):
    from pincite.workbook import build

    row = {
        "ID": "A01",
        "Reference": "Eta (2017).",
        "hyperlink": "https://example.org/e",
        "Summary": "A careful panel study that finds large effects.",
        "Role in manuscript / result cited": "Not assessed — source unread (paywalled).",
        "Citing paragraph(s)": '"Effects were large." (§II, fns 4)',
        "Limitations / conflicts / later rebuttals": "Not assessed — source unread (paywalled).",
        "accuracy": "unverified",
        "acc_note": "paywalled; no lawful copy found",
    }
    out = tmp_path / "a.xlsx"
    build({"mode": "audit"}, [row], out)
    _set(out, "Citations", "F4", "⚠ Issue")
    findings = qc.qc(out, expect_footnotes=5)
    codes = {f.code for f in findings}
    assert "BARE-FLAG" in codes
    assert "FOOTNOTE-GAP" in codes
    _set(out, "Citations", "F4", "○ Unverified — paywalled")
    assert "UNREAD-RATED" in {f.code for f in qc.qc(out)}


def test_qc_header_leak(tmp_path):
    from pincite.workbook import build

    rows = []
    for i in range(1, 7):
        rows.append(
            {
                "ID": f"A0{i}",
                "Reference": f"Source {i} ({2000 + i}).",
                "hyperlink": "https://example.org",
                "Summary": "Summary of the source.",
                "Role in manuscript / result cited": "Role.",
                "Citing paragraph(s)": f'"Journal of Leaky Headers Volume Twelve finding {i} holds." (§I, fns {i})',
                "Limitations / conflicts / later rebuttals": "Limits.",
                "accuracy": "accurate",
            }
        )
    build({"mode": "audit"}, rows, tmp_path / "leak.xlsx")
    assert "HEADER-LEAK" in {f.code for f in qc.qc(tmp_path / "leak.xlsx")}


def test_qc_main_strict(supporting_workbook):
    _set(supporting_workbook, "Supporting Authority", "H5", "Short.")
    assert qc.main([str(supporting_workbook)]) == 0
    assert qc.main([str(supporting_workbook), "--strict"]) == 1
