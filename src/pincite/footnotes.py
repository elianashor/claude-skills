#!/usr/bin/env python3
"""
Extract footnotes, body text, and exact in-text marker positions from a PDF.

Why this exists
---------------
The naive approach -- pull page text, split on a leading number, grab a
character window around each footnote reference -- fails in two ways that
matter for a cite-check:

  1. Footnotes that straddle a page break get dropped or merged.
  2. Citing "quotations" start and end mid-word, because a character window
     has no idea where a sentence begins.

Both problems disappear once you stop treating the page as flat text. In a
typeset PDF the body, the footnotes, and the superscript markers are set in
*different font sizes*. Separating by font gives exact marker positions, so a
quotation can be taken as the complete sentence spanning the marker rather
than a blind slice.

Sizes are detected automatically, so this works on documents it was never
tuned against. Override with --body-size / --note-size if a document does
something unusual.

Usage
-----
    python extract_footnotes.py paper.pdf --outdir out/
    python extract_footnotes.py paper.pdf --outdir out/ --max-quote 300

Outputs (all in --outdir)
-------------------------
    footnotes.json     {footnote number: full footnote text}
    body_marked.txt    body text with [[N]] markers at exact positions
    quotes.json        {footnote number: {page, quote}} complete sentences
    extract_report.txt what was detected, what is missing, and why
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber required:  pip install pdfplumber")

__all__ = ["build_quotes", "detect_sizes", "extract", "main"]


# ---------------------------------------------------------------- watermarks


def is_decoration(ch, max_body_size):
    """Rotated text, oversized glyphs, and stamped headers are not content.

    Preprint services stamp rotated watermarks across every page; those chars
    interleave with real text in reading order and produce the stray single
    letters ('d e w e i v') that pollute naive extraction.
    """
    m = ch.get("matrix")
    if m and abs(m[1]) > 0.01:  # rotated
        return True
    if ch["size"] > max_body_size * 1.4:  # display/watermark sizing
        return True
    return False


# ------------------------------------------------------------ size detection


def detect_sizes(pdf, sample_pages=12):
    """Infer body / footnote / marker / note-number font sizes.

    Body text is whatever dominates the upper two-thirds of the page.
    Footnote text is whatever dominates the bottom third. Markers are the
    small superscripts sharing the body's typeface; note numbers are the
    small glyphs sharing the footnote typeface.
    """
    upper, lower = Counter(), Counter()
    pages = pdf.pages[: min(sample_pages, len(pdf.pages))]
    for pg in pages:
        cut = pg.height * 0.68
        for ch in pg.chars:
            m = ch.get("matrix")
            if m and abs(m[1]) > 0.01:
                continue
            if ch["size"] > 30:
                continue
            key = (ch["fontname"], round(ch["size"], 1))
            (upper if ch["top"] <= cut else lower)[key] += 1

    if not upper:
        raise SystemExit("Could not read any text; is this a scanned PDF? Try OCR first.")

    body_font, body_size = upper.most_common(1)[0][0]

    note_font, note_size = None, None
    for (fn, sz), _ in lower.most_common():
        if sz < body_size - 0.3:
            note_font, note_size = fn, sz
            break
    if note_size is None:  # no separate footnote face
        note_font, note_size = body_font, body_size

    def smaller_sibling(font_stem, ref_size, counter):
        """Smallest size sharing a typeface stem -- i.e. the superscripts."""
        stem = re.sub(r"^[A-Z]{6,7}\+", "", font_stem).split("-")[0][:12]
        best = None
        for (fn, sz), _ in counter.items():
            if sz >= ref_size - 0.3:
                continue
            if stem and stem in fn:
                if best is None or sz < best:
                    best = sz
        return best

    marker_size = smaller_sibling(body_font, body_size, upper) or smaller_sibling(body_font, body_size, lower)
    number_size = smaller_sibling(note_font, note_size, lower)

    return {
        "body_font": body_font,
        "body_size": body_size,
        "note_font": note_font,
        "note_size": note_size,
        "marker_size": marker_size,
        "number_size": number_size,
    }


def near(value, target, tol=0.45):
    return target is not None and abs(value - target) <= tol


# ------------------------------------------------------------------ assembly


def rows_to_text(chars, ybucket=3.0):
    """Reassemble chars into reading order (top-to-bottom, left-to-right)."""
    rows = defaultdict(list)
    for c in chars:
        rows[round(c["top"] / ybucket)].append(c)
    out = []
    for y in sorted(rows):
        line = sorted(rows[y], key=lambda c: c["x0"])
        out.append("".join(c["text"] for c in line))
    return "\n".join(out)


def split_concatenated_markers(text, max_fn):
    """`[[158159]]` is two adjacent markers, not footnote 158,159.

    Consecutive superscripts render with no separator. Split only when the
    halves are genuinely consecutive integers, which is what adjacent
    footnote markers always are.
    """

    def repl(m):
        s = m.group(1)
        if len(s) > 3:
            for cut in range(1, len(s)):
                a, b = s[:cut], s[cut:]
                if a.isdigit() and b.isdigit() and int(b) == int(a) + 1 and 1 <= int(a) <= max_fn:
                    return f"[[{a}]][[{b}]]"
        return m.group(0)

    return re.sub(r"\[\[(\d+)\]\]", repl, text)


def extract(pdf_path, outdir, max_quote=300, body_size=None, note_size=None):
    os.makedirs(outdir, exist_ok=True)
    report = []

    with pdfplumber.open(pdf_path) as pdf:
        sizes = detect_sizes(pdf)
        if body_size:
            sizes["body_size"] = body_size
        if note_size:
            sizes["note_size"] = note_size

        report.append("Detected font sizes")
        for k, v in sizes.items():
            report.append(f"  {k:14} {v}")

        max_size = max(v for k, v in sizes.items() if isinstance(v, (int, float)))
        body_pages, footnotes, running_note = [], defaultdict(str), None

        for pno, pg in enumerate(pdf.pages, 1):
            chars = [c for c in pg.chars if not is_decoration(c, max_size)]

            body = [c for c in chars if near(c["size"], sizes["body_size"])]
            notes = [
                c
                for c in chars
                if near(c["size"], sizes["note_size"]) and not near(sizes["note_size"], sizes["body_size"])
            ]
            marks = [c for c in chars if near(c["size"], sizes["marker_size"])]
            numnos = [c for c in chars if near(c["size"], sizes["number_size"])]

            # ---- body, with markers spliced in at their true positions ----
            # Keep one output line per typeset line. Line structure is what makes
            # running-header removal possible later; flattening the page to a
            # single string throws that away.
            tagged = [(c, "b") for c in body] + [(c, "m") for c in marks]
            rows = defaultdict(list)
            for c, k in tagged:
                rows[round(c["top"] / 3.0)].append((c, k))

            lines = []
            for y in sorted(rows):
                row = sorted(rows[y], key=lambda t: t[0]["x0"])
                buf, kind, chunks = "", None, []
                for c, k in row:
                    if k != kind:
                        if buf:
                            chunks.append((kind, buf))
                        buf, kind = "", k
                    buf += c["text"]
                if buf:
                    chunks.append((kind, buf))

                line = ""
                for k, txt in chunks:
                    if k == "m":
                        for n in re.findall(r"\d+", txt):
                            line += f"[[{n}]]"
                    else:
                        line += txt
                lines.append(line)
            body_pages.append((pno, "\n".join(lines)))

            # ---- footnotes, carried across page breaks ----
            # Each typeset line ends in a space: a note that wraps onto a new
            # line, or continues on the next page, must not fuse its last word
            # on one line to its first word on the next.
            fitems = [(c, "n") for c in numnos] + [(c, "t") for c in notes]
            fitems.sort(key=lambda t: (round(t[0]["top"] / 3), t[0]["x0"]))
            buf, kind, row = "", None, None
            fchunks = []
            for c, k in fitems:
                r = round(c["top"] / 3)
                if row is not None and r != row and kind == "t":
                    buf += " "
                row = r
                if k != kind:
                    if buf:
                        fchunks.append((kind, buf))
                    buf, kind = "", k
                buf += c["text"]
            if buf:
                fchunks.append((kind, buf))

            for k, txt in fchunks:
                if k == "n":
                    nums = re.findall(r"\d+", txt)
                    if nums:
                        running_note = int(nums[-1])
                elif running_note is not None:
                    sep = " " if footnotes[running_note] and not footnotes[running_note].endswith(" ") else ""
                    footnotes[running_note] += sep + txt

    # ---- strip the running header BEFORE flattening ----
    # Do this at the line level, while line structure still exists. A watermark
    # can inject stray characters into the header line, so pages rarely match
    # byte-for-byte; compare on a letters-only normal form instead.
    header_norm = guess_running_header(body_pages)
    if header_norm:
        cleaned = []
        for p, t in body_pages:
            keep = []
            for line in t.split("\n"):
                if line_is_header(line, header_norm):
                    continue
                keep.append(line)
            cleaned.append((p, "\n".join(keep)))
        body_pages = cleaned
        report.append(f"\nRunning header removed (normalised): {header_norm[:60]!r}")

    body_text = "".join(f"\n<<<PAGE {p}>>>\n{t}" for p, t in body_pages)
    max_fn = max(footnotes) if footnotes else 0
    body_text = split_concatenated_markers(body_text, max_fn)

    footnotes = {str(k): re.sub(r"\s+", " ", v).strip() for k, v in sorted(footnotes.items())}

    plain = re.sub(r"<<<PAGE \d+>>>", " ", body_text)
    plain = re.sub(r"\s+", " ", plain)

    quotes = build_quotes(plain, body_text, footnotes, max_quote)

    with open(os.path.join(outdir, "footnotes.json"), "w") as f:
        json.dump(footnotes, f, indent=1)
    with open(os.path.join(outdir, "body_marked.txt"), "w") as f:
        f.write(body_text)
    with open(os.path.join(outdir, "quotes.json"), "w") as f:
        json.dump(quotes, f, indent=1)

    found = set(int(k) for k in footnotes)
    missing = [n for n in range(1, (max(found) if found else 0) + 1) if n not in found]
    marked = set(int(x) for x in re.findall(r"\[\[(\d+)\]\]", body_text))

    report += [
        "",
        f"Footnotes captured      : {len(footnotes)}",
        f"Highest footnote number : {max(found) if found else 0}",
        f"Gaps in footnote series : {missing if missing else 'none'}",
        f"In-text markers found   : {len(marked)}",
        f"Footnotes w/o a marker  : {sorted(found - marked) or 'none'}",
        f"Quotations built        : {len(quotes)}",
        "",
        "A gap in the footnote series usually means the note is a pure author's",
        "note carrying no citation, or the page layout defeated detection. Check",
        "those specific pages by hand before reporting coverage.",
    ]
    txt = "\n".join(report)
    with open(os.path.join(outdir, "extract_report.txt"), "w") as f:
        f.write(txt)
    print(txt)
    return footnotes, quotes


def norm_letters(s):
    """Letters only, uppercased -- survives watermark characters injected mid-line."""
    return re.sub(r"[^A-Za-z]", "", s).upper()


def guess_running_header(body_pages):
    """Find the running header: the line that opens (or closes) most pages.

    A running header is defined by position, not frequency. Counting raw
    repeats would pick any boilerplate sentence the body happens to repeat,
    and then delete real text. So a candidate scores once per page, and only
    when it is that page's first or last line.

    Returned in normalised (letters-only) form because a watermark stamped
    across the page interleaves stray characters into the header text, so no
    two pages render it identically.
    """
    first, last = Counter(), Counter()
    for _, t in body_pages:
        lines = [norm_letters(re.sub(r"\[\[\d+\]\]", "", ln)) for ln in t.split("\n")]
        lines = [s for s in lines if 15 < len(s) < 120]
        if lines:
            first[lines[0]] += 1
            last[lines[-1]] += 1
    need = max(3, len(body_pages) * 0.35)
    for counter in (first, last):  # a header outranks a footer on ties
        if counter:
            cand, n = counter.most_common(1)[0]
            if n >= need:
                return cand
    return None


def line_is_header(line, header_norm):
    """True if this line is the running header, whole or fragmentary.

    Page breaks and watermarks can split the header, so a line counts as
    header if its normal form is a substantial substring of the header (or
    vice versa). The 12-character floor keeps short real sentences safe.
    """
    s = norm_letters(re.sub(r"\[\[\d+\]\]", "", line))
    if len(s) < 12:
        return False
    return s in header_norm or (len(s) >= 20 and header_norm in s)


# ------------------------------------------------------------------- quoting

SENT_BOUNDARY = re.compile(r'[.!?](?:["”])?\s+(?=[A-Z"“(])')
ENDS_SENTENCE = re.compile(r'[.!?]["”")]?\s*$')


def build_quotes(plain, body_text, footnotes, max_quote):
    """Take the complete sentence spanning each marker.

    Two cases the naive version gets wrong, both handled here:
      - marker sits mid-sentence  -> the sentence must be completed from the
        text *after* the marker, or the quote ends on a half clause
      - marker sits at a sentence end -> do NOT append the following sentence
    """
    pagemap = {}
    parts = re.split(r"<<<PAGE (\d+)>>>", body_text)
    for i in range(1, len(parts), 2):
        p = int(parts[i])
        for mm in re.finditer(r"\[\[(\d+)\]\]", parts[i + 1]):
            pagemap.setdefault(int(mm.group(1)), p)

    out = {}
    for fn in sorted(int(k) for k in footnotes):
        m = re.search(rf"\[\[{fn}\]\]", plain)
        if not m:
            continue
        left = re.sub(r"\[\[\d+\]\]", "", plain[max(0, m.start() - 2000) : m.start()])
        right = re.sub(r"\[\[\d+\]\]", "", plain[m.end() : m.end() + 900])

        starts = [x.end() for x in SENT_BOUNDARY.finditer(left)]
        head = left[starts[-1] :] if starts else left

        if ENDS_SENTENCE.search(head):
            tail = ""
        else:
            em = re.search(r'[.!?](?:["”])?(?=\s+[A-Z"“(]|\s*$)', right)
            tail = right[: em.end()] if em else ""

        q = (head + tail).strip()

        # a figure caption is not context; step back to the preceding sentence
        if re.match(r"^(Figure|Table)\s*\d", q) and len(starts) >= 2:
            prev = left[starts[-2] : starts[-1]].strip()
            if prev and not re.match(r"^(Figure|Table)\s*\d", prev):
                q = prev

        if len(q) > max_quote:
            inner = [x.end() for x in SENT_BOUNDARY.finditer(q)]
            if inner:
                cand = q[inner[-1] :].strip()
                if 45 < len(cand) <= max_quote:
                    q = cand
        if len(q) > max_quote:
            for c in [x.end() for x in re.finditer(r"[,;:]\s+|\)\s+|”\s+", q)]:
                cand = "…" + q[c:].strip()
                if len(cand) <= max_quote:
                    q = cand
                    break

        q = re.sub(r"\s+", " ", q).strip()
        if q and q[0].islower() and not q.startswith("…"):
            q = "…" + q
        out[str(fn)] = {"page": pagemap.get(fn), "quote": q}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--outdir", default="extract_out")
    ap.add_argument(
        "--max-quote", type=int, default=300, help="target ceiling for a citing quotation (default 300 chars)"
    )
    ap.add_argument("--body-size", type=float, help="override detected body font size")
    ap.add_argument("--note-size", type=float, help="override detected footnote font size")
    a = ap.parse_args(argv)
    extract(a.pdf, a.outdir, a.max_quote, a.body_size, a.note_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
