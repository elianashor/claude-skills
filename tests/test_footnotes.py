import json

from pincite.footnotes import build_quotes, extract, split_concatenated_markers


def test_extracts_every_footnote_and_marker(footnoted_pdf, tmp_path):
    notes, _ = extract(str(footnoted_pdf), str(tmp_path / "out"))
    assert sorted(map(int, notes)) == [1, 2, 3, 4, 5, 6]
    body = (tmp_path / "out" / "body_marked.txt").read_text()
    assert all(f"[[{n}]]" in body for n in range(1, 7))
    report = (tmp_path / "out" / "extract_report.txt").read_text()
    assert "Gaps in footnote series : none" in report
    assert "Footnotes w/o a marker  : none" in report


def test_footnote_straddling_a_page_break_is_joined_with_a_space(footnoted_pdf, tmp_path):
    notes, _ = extract(str(footnoted_pdf), str(tmp_path / "out"))
    assert notes["3"] == ("Lee (2021) and Park (2022); both rely on independent claims data, not the sample used here.")


def test_running_header_is_removed_by_position_not_frequency(footnoted_pdf, tmp_path):
    _, quotes = extract(str(footnoted_pdf), str(tmp_path / "out"))
    assert all("SYNTHETIC EXPERT REPORT" not in q["quote"] for q in quotes.values())
    body = (tmp_path / "out" / "body_marked.txt").read_text()
    assert "Filler text alpha" in body  # repeated body text is never mistaken for a header


def test_quotes_are_complete_sentences_on_both_sides_of_the_marker(footnoted_pdf, tmp_path):
    _, quotes = extract(str(footnoted_pdf), str(tmp_path / "out"))
    # marker mid-sentence: the sentence is completed from the text after it
    assert quotes["2"]["quote"] == "Entry by a second supplier changed bargaining in every region studied."
    # marker at sentence end: the following sentence is NOT appended
    assert quotes["1"]["quote"] == "Prices fell sharply after entry."
    assert quotes["4"]["page"] == 2
    saved = json.loads((tmp_path / "out" / "quotes.json").read_text())
    assert saved["6"]["quote"] == "A final robustness check confirms the result."


def test_adjacent_markers_split_only_when_consecutive():
    assert split_concatenated_markers("x[[158159]]", 200) == "x[[158]][[159]]"
    assert split_concatenated_markers("x[[1580]]", 200) == "x[[1580]]"


def test_long_quote_is_trimmed_to_a_clause_with_an_ellipsis():
    body = "<<<PAGE 1>>>\n" + ("Lead clause words, " * 30) + "the final finding holds firmly.[[1]]"
    plain = body.replace("<<<PAGE 1>>>", " ")
    q = build_quotes(plain, body, {"1": "x"}, max_quote=80)["1"]["quote"]
    assert q.startswith("…") and q.endswith("holds firmly.") and len(q) <= 80
