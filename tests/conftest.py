"""Synthetic fixtures. Nothing here comes from a real matter: every document is generated."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

W_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
R_NS = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_docx(
    path: Path,
    blocks: list[tuple[str, str]],
    start: int = 1,
    footnotes: dict[int, str] | None = None,
    style_numbering: bool = False,
) -> Path:
    """blocks: (kind, text) with kind in {"num", "plain", "heading", "fnref:<id>"}.

    "num" paragraphs carry Word list numbering (numId 7, ilvl 0), the way
    expert reports number their paragraphs; the number never appears in the
    text layer. With style_numbering the numbering comes from a paragraph style
    instead of direct formatting, as in many firm templates.
    """
    body = []
    for kind, text in blocks:
        ppr = ""
        if kind == "num":
            ppr = (
                '<w:pPr><w:pStyle w:val="NumPara"/></w:pPr>'
                if style_numbering
                else '<w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="7"/></w:numPr></w:pPr>'
            )
        elif kind == "heading":
            ppr = '<w:pPr><w:pStyle w:val="Heading2"/></w:pPr>'
        runs = f'<w:r><w:t xml:space="preserve">{_esc(text)}</w:t></w:r>'
        if kind.startswith("fnref:"):
            fid = kind.split(":")[1]
            ppr = '<w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="7"/></w:numPr></w:pPr>'
            runs += f'<w:r><w:footnoteReference w:id="{fid}"/></w:r>'
        body.append(f"<w:p>{ppr}{runs}</w:p>")
    document = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W_NS} {R_NS}>'
        f"<w:body>{''.join(body)}</w:body></w:document>"
    )
    numbering = (
        f'<?xml version="1.0" encoding="UTF-8"?><w:numbering {W_NS}>'
        '<w:abstractNum w:abstractNumId="3"><w:lvl w:ilvl="0"><w:start w:val="1"/>'
        '<w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/></w:lvl></w:abstractNum>'
        '<w:num w:numId="7"><w:abstractNumId w:val="3"/>'
        f'<w:lvlOverride w:ilvl="0"><w:startOverride w:val="{start}"/></w:lvlOverride></w:num>'
        "</w:numbering>"
    )
    styles = (
        f'<?xml version="1.0" encoding="UTF-8"?><w:styles {W_NS}>'
        '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/></w:style>'
        '<w:style w:type="paragraph" w:styleId="NumPara"><w:name w:val="Numbered Paragraph"/>'
        '<w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="7"/></w:numPr></w:pPr></w:style>'
        "</w:styles>"
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )
        z.writestr("word/document.xml", document)
        z.writestr("word/numbering.xml", numbering)
        z.writestr("word/styles.xml", styles)
        if footnotes:
            notes = "".join(
                f'<w:footnote w:id="{i}"><w:p><w:r><w:t>{_esc(t)}</w:t></w:r></w:p></w:footnote>'
                for i, t in footnotes.items()
            )
            z.writestr(
                "word/footnotes.xml",
                f'<?xml version="1.0"?><w:footnotes {W_NS}>'
                '<w:footnote w:id="-1"><w:p/></w:footnote><w:footnote w:id="0"><w:p/></w:footnote>'
                f"{notes}</w:footnotes>",
            )
    return path


REPORT_BLOCKS = [
    ("heading", "III.A Market Structure"),
    ("num", "The study period runs from 2015 through 2019 and covers 412 plans."),
    ("num", "Average net prices fell 12.5% over the period, a decline of $1,240 per member."),
    ("plain", "“Competition among the actual substitutes disciplined price throughout the period.”"),
    ("num", "The decline was concentrated in the final two years of the period."),
    ("heading", "III.B Pass-Through"),
    ("num", "Measured on the sample plans only, pass-through averaged 87 percent."),
    ("fnref:1", "Prior estimates in the literature range from 60 to 95 percent."),
]


@pytest.fixture
def report_docx(tmp_path: Path) -> Path:
    """A numbered report starting at ¶ 40, with a block quote, headings and a footnote."""
    return make_docx(
        tmp_path / "report.docx",
        REPORT_BLOCKS,
        start=40,
        footnotes={1: "See the survey of 31 studies cited in Appendix B."},
    )


FILLER = [
    "alpha",
    "bravo",
    "charlie",
    "delta",
    "echo",
    "foxtrot",
    "golf",
    "hotel",
    "india",
    "juliet",
    "kilo",
    "lima",
    "mike",
]


def make_footnoted_pdf(path: Path) -> Path:
    """Three typeset pages with a running header, superscript markers in the body
    face, footnotes in a smaller face, and footnote 3 straddling a page break."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    _, height = letter
    header = "SYNTHETIC EXPERT REPORT OF A WITNESS"

    def body_line(y, segments):
        x = 72
        for seg in segments:
            if isinstance(seg, int):
                c.setFont("Helvetica", 7)
                c.drawString(x, y + 3, str(seg))
                x += c.stringWidth(str(seg), "Helvetica", 7)
            else:
                c.setFont("Helvetica", 11)
                c.drawString(x, y, seg)
                x += c.stringWidth(seg, "Helvetica", 11)

    def note(y, num, text):
        x = 72
        if num is not None:
            c.setFont("Times-Roman", 6)
            c.drawString(x, y + 2, str(num))
            x += c.stringWidth(str(num), "Times-Roman", 6) + 1
        c.setFont("Times-Roman", 9)
        c.drawString(x, y, text)

    pages = [
        dict(
            lines=[
                ["Prices fell sharply after entry.", 1, " The effect persisted for three years."],
                ["Entry by a second supplier changed bargaining", 2, " in every region studied."],
                ["Rebuttal studies reached the same conclusion on different data.", 3],
            ],
            notes=[
                (1, "Smith and Jones (2018), Table 2."),
                (2, "Agency staff report (2020) at 14."),
                (3, "Lee (2021) and Park (2022); both rely on"),
            ],
        ),
        dict(
            lines=[
                ["Capacity constraints did not bind at any point.", 4, " Utilization stayed low."],
                ["The second period shows the same pattern.", 5],
            ],
            notes=[
                (None, "independent claims data, not the sample used here."),
                (4, "Plant census, 2019 edition, p. 7."),
                (5, "Same source, p. 9."),
            ],
        ),
        dict(
            lines=[
                ["A final robustness check confirms the result.", 6],
                ["No further adjustments were needed for this analysis."],
            ],
            notes=[(6, "Appendix C, Table C-4.")],
        ),
    ]
    for page in pages:
        c.setFont("Helvetica", 11)
        c.drawString(72, height - 50, header)
        y = height - 100
        for segs in page["lines"]:
            body_line(y, segs)
            y -= 16
        for i in range(12):  # filler body text so the body face dominates the upper page
            c.setFont("Helvetica", 11)
            c.drawString(72, y, f"Filler text {FILLER[i % len(FILLER)]} keeps the body face dominant here.")
            y -= 16
        ny = 110
        for num, text in page["notes"]:
            note(ny, num, text)
            ny -= 12
        c.showPage()
    c.save()
    return path


@pytest.fixture
def footnoted_pdf(tmp_path: Path) -> Path:
    return make_footnoted_pdf(tmp_path / "manuscript.pdf")


def supporting_rows() -> list[dict]:
    def lim(n: int) -> str:
        return (
            f"Funded by an industry association (disclosed at p. {n}). The authors concede the sample excludes "
            "small plans, and a later comment questions the price index used."
        )

    return [
        {
            "ID": "S01",
            "section": "III.A",
            "hyperlink": "https://doi.org/10.0000/example.1",
            "Citation": "Alpha, A. & Beta, B. (2020). Entry and prices. Journal of Examples, 12(3), 1–30.",
            "What this source is": "A peer-reviewed panel study of regional supply markets.",
            "Claim it supports": "Entry by a second supplier lowered prices.",
            "How we would use it": "Section III.A, second paragraph, to support the entry effect with its scope limits.",
            "Findings": "Prices fell 9.1% within two years of entry (Table 2).",
            "Proposed excerpt (verbatim)": "“Prices fell by 9.1 percent within two years of entry.” (p. 14)",
            "Limitations / conflicts / later rebuttals": lim(2),
            "Data": "Regional panel, 2010–2018, 212 markets.",
            "Methods / test": "Difference-in-differences.",
            "Relevance": 5,
            "Credibility": "Peer-reviewed field journal",
            "In draft": "Cited in draft",
            "detail_abstract": "A written summary of the study.",
            "detail_relevance_rationale": "Directly on point.",
            "detail_verification_notes": "Quote checked against the publisher PDF.",
        },
        {
            "ID": "S02",
            "section": "III.A",
            "hyperlink": "https://www.example.gov/report.pdf",
            "Citation": "Agency (2019). Staff report on supply markets. Government Printing Office.",
            "What this source is": "A government staff report.",
            "Claim it supports": "Market structure context.",
            "How we would use it": "Background for Section III.A.",
            "Findings": "Describes 14 regional markets (p. 3).",
            "Proposed excerpt (verbatim)": "“The markets studied vary widely in concentration.” (p. 3)",
            "Limitations / conflicts / later rebuttals": lim(5),
            "Data": "Agency survey.",
            "Methods / test": "Descriptive; no statistical analysis.",
            "Relevance": 3,
            "Credibility": "Government / agency source",
            "In draft (2026-01-15)": "Not yet cited",
            "detail_abstract": "This source carries no published abstract; the following is written from the reading.",
            "detail_relevance_rationale": "Background only.",
            "detail_verification_notes": "Read in full.",
        },
        {
            "ID": "S03",
            "section": "III.B",
            "hyperlink": "https://doi.org/10.0000/example.3",
            "Citation": "Gamma, C. (2022). Pass-through in practice. NBER Working Paper 30000.",
            "What this source is": "A working paper estimating pass-through.",
            "Claim it supports": "Pass-through is substantial.",
            "How we would use it": "Section III.B with the working-paper caveat.",
            "Findings": "Pass-through averaged 80% (Table 4).",
            "Proposed excerpt (verbatim)": "“Average pass-through is 80 percent.” (p. 22)",
            "Limitations / conflicts / later rebuttals": lim(9),
            "Data": "Claims data, 2016–2020.",
            "Methods / test": "Instrumental variables.",
            "Relevance": 4,
            "Credibility": "Working paper (NBER)",
            "In draft": "Cited in draft",
            "detail_abstract": "Abstract text.",
            "detail_relevance_rationale": "Case-central.",
            "detail_verification_notes": "Checked against the NBER PDF.",
        },
    ]


def supporting_spec(rows_path: str = "rows.json") -> dict:
    return {
        "mode": "supporting",
        "title": "Supporting Authority — Synthetic Report",
        "draft_date": "2026-01-15",
        "sections": [{"key": "III.A", "heading": "Market Structure"}, {"key": "III.B", "heading": "Pass-Through"}],
        "rows": rows_path,
        "method": {
            "READING AND VERIFICATION STANDARD": "Every source was read in full.",
            "COVERAGE AND ORGANIZATION": "Rows are grouped by section.",
            "NOTES ON VERIFICATION LABELS": "None open.",
            "SOURCE-SPECIFIC NOTES": "None.",
        },
    }


@pytest.fixture
def supporting_workbook(tmp_path: Path) -> Path:
    from pincite.workbook import build

    (tmp_path / "rows.json").write_text(json.dumps(supporting_rows()))
    out = tmp_path / "table.xlsx"
    build(supporting_spec(), supporting_rows(), out)
    return out
