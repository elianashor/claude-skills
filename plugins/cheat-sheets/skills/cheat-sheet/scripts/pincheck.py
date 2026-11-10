#!/usr/bin/env python3
"""
Mechanically verify every (pin cite, fact) pair against the source, and prove
the checker works with a negative control.

A cheat sheet, brief, or table that says "the rate fell to 12% (¶ 42)" makes
two promises: the number is in the source, and it is at ¶ 42. This tool checks
both. When a fact is missing from its pin it searches the whole source and
tells you whether the pin is wrong (found at ¶ 47) or the fact is a phantom
(found nowhere), which are very different failures.

Sources it reads
----------------
    .docx   numbered paragraphs reconstructed from Word's own list numbering
            (the auto-numbering the text layer does not contain), with
            unnumbered block quotes and lists attached to the paragraph above;
            footnotes indexed as n. 1, n. 2, ...
    .pdf    pages as p. 1, p. 2, ... (needs pdfplumber); --unit para splits
            numbered paragraphs out of the text instead
    .txt/.md  numbered paragraphs ("12." or "¶ 12" at line start), or pages
            split on form feeds

Two ways to name the claims
---------------------------
    pincheck check SOURCE --claims claims.json
        [{"pin": "¶¶ 42–44", "text": "The rate fell to 12% by 2019."}, ...]
        Optional per claim: "numbers": [...], "quotes": [...] to pin exactly
        which facts must appear; otherwise both are pulled from "text".

    pincheck check SOURCE --scan sheet.pdf|.md|.txt|.html|.docx
        Finds every sentence or table cell in a rendered sheet that carries a
        pin cite and checks the numbers and quotations in it.

Proving the checker
-------------------
    --negative-control N   corrupts N facts in memory (a digit changed, a
                           quoted word swapped), re-runs, and requires every
                           corruption to fail. A checker that passes a
                           corrupted fact has proven nothing, so that exits 3.

Inspecting units first
----------------------
    pincheck units SOURCE [--expect-count 231]
        Prints the reconstructed numbering so you can validate it before
        citing: count, first and last unit, and any gaps.

Exit codes: 0 all verified · 1 a fact failed · 2 usage or input error ·
3 negative control did not catch every corruption.
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import sys
import unicodedata
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

__all__ = [
    "Claim",
    "Result",
    "Unit",
    "check_claims",
    "extract_facts",
    "load_units",
    "main",
    "negative_control",
    "parse_pin",
    "scan_claims",
]

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# ------------------------------------------------------------------- units


@dataclass
class Unit:
    kind: str  # "para" | "page" | "note"
    number: int
    text: str

    @property
    def label(self) -> str:
        return {"para": "¶", "page": "p.", "note": "n."}[self.kind] + f" {self.number}"


def _docx_text(p) -> str:
    parts = []
    for node in p.iter():
        if node.tag == W + "t" and node.text:
            parts.append(node.text)
        elif node.tag in (W + "tab",):
            parts.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            parts.append(" ")
    return "".join(parts)


def _docx_styles(z: zipfile.ZipFile) -> tuple[dict, dict]:
    """style id -> (numId, ilvl) for styles that carry numbering; style id -> name."""
    numbered, names = {}, {}
    if "word/styles.xml" not in z.namelist():
        return numbered, names
    root = ET.fromstring(z.read("word/styles.xml"))
    for st in root.iter(W + "style"):
        sid = st.get(W + "styleId")
        name = st.find(W + "name")
        names[sid] = name.get(W + "val") if name is not None else sid
        num = st.find(f"{W}pPr/{W}numPr")
        if num is not None:
            nid = num.find(W + "numId")
            lvl = num.find(W + "ilvl")
            numbered[sid] = (
                nid.get(W + "val") if nid is not None else None,
                lvl.get(W + "val") if lvl is not None else "0",
            )
    return numbered, names


def _docx_starts(z: zipfile.ZipFile) -> dict:
    """(numId, ilvl) -> start value, honoring startOverride."""
    starts = {}
    if "word/numbering.xml" not in z.namelist():
        return starts
    root = ET.fromstring(z.read("word/numbering.xml"))
    abstract = {}
    for a in root.iter(W + "abstractNum"):
        aid = a.get(W + "abstractNumId")
        for lvl in a.iter(W + "lvl"):
            s = lvl.find(W + "start")
            abstract[(aid, lvl.get(W + "ilvl"))] = int(s.get(W + "val")) if s is not None else 1
    for num in root.iter(W + "num"):
        nid = num.get(W + "numId")
        aref = num.find(W + "abstractNumId")
        aid = aref.get(W + "val") if aref is not None else None
        for (a_id, ilvl), start in abstract.items():
            if a_id == aid:
                starts[(nid, ilvl)] = start
        for ov in num.iter(W + "lvlOverride"):
            so = ov.find(W + "startOverride")
            if so is not None:
                starts[(nid, ov.get(W + "ilvl"))] = int(so.get(W + "val"))
    return starts


EXPLICIT_PARA = re.compile(r"^\s*(?:¶\s*(?P<a>\d{1,4})[.:]?|\(?(?P<b>\d{1,4})[.)])\s+(?=\S)")


def _para_no(m: re.Match) -> int:
    return int(m.group("a") or m.group("b"))


def _load_docx(path: Path, attach: bool = True) -> list[Unit]:
    with zipfile.ZipFile(path) as z:
        styled, names = _docx_styles(z)
        starts = _docx_starts(z)
        root = ET.fromstring(z.read("word/document.xml"))
        body = root.find(W + "body")
        paras = []  # (numkey or None, is_heading, text, footnote ids)
        for p in body.iter(W + "p"):
            ppr = p.find(W + "pPr")
            key, style = None, None
            if ppr is not None:
                ps = ppr.find(W + "pStyle")
                style = ps.get(W + "val") if ps is not None else None
                num = ppr.find(W + "numPr")
                if num is not None:
                    nid, lvl = num.find(W + "numId"), num.find(W + "ilvl")
                    key = (
                        nid.get(W + "val") if nid is not None else None,
                        lvl.get(W + "val") if lvl is not None else "0",
                    )
                elif style in styled:
                    key = styled[style]
            if key and key[0] == "0":  # numId 0 switches numbering off
                key = None
            heading = bool(style and re.match(r"(?i)heading|title", names.get(style, style) or ""))
            fns = [r.get(W + "id") for r in p.iter(W + "footnoteReference")]
            paras.append((key, heading, _docx_text(p).strip(), fns))

        counts = Counter(k for k, h, t, _ in paras if k and not h and t)
        units: list[Unit] = []
        if counts:
            dominant = counts.most_common(1)[0][0]
            n = starts.get(dominant, 1) - 1
            current = None
            for key, heading, text, _ in paras:
                if key == dominant and not heading:
                    n += 1
                    current = Unit("para", n, text)
                    units.append(current)
                elif heading:
                    current = None
                elif current is not None and attach and text:
                    current.text += "\n" + text
        else:  # no list numbering: fall back to numbers typed into the text
            current = None
            for _, heading, text, _ in paras:
                m = EXPLICIT_PARA.match(text)
                if m and not heading:
                    current = Unit("para", _para_no(m), text[m.end() :])
                    units.append(current)
                elif heading:
                    current = None
                elif current is not None and attach and text:
                    current.text += "\n" + text

        if "word/footnotes.xml" in z.namelist():
            froot = ET.fromstring(z.read("word/footnotes.xml"))
            for fn in froot.iter(W + "footnote"):
                fid = int(fn.get(W + "id"))
                if fid <= 0:  # separator and continuation notes
                    continue
                units.append(Unit("note", fid, " ".join(_docx_text(p) for p in fn.iter(W + "p")).strip()))
    return units


def _split_numbered(text: str) -> list[Unit]:
    units: list[Unit] = []
    current = None
    for line in text.splitlines():
        m = EXPLICIT_PARA.match(line)
        if m and (not units or _para_no(m) == units[-1].number + 1):
            current = Unit("para", _para_no(m), line[m.end() :])
            units.append(current)
        elif current is not None:
            current.text += "\n" + line
    return units


def load_units(path: str | Path, unit: str = "auto") -> list[Unit]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".docx":
        units = _load_docx(path)
        return units if unit in ("auto", "para") else [u for u in units if u.kind == unit]
    if suffix == ".pdf":
        try:
            import pdfplumber
        except ImportError:  # pragma: no cover
            sys.exit("pdfplumber required for PDF sources:  pip install pdfplumber")
        with pdfplumber.open(path) as pdf:
            pages = [pg.extract_text() or "" for pg in pdf.pages]
        if unit == "para":
            return _split_numbered("\n".join(pages))
        return [Unit("page", i, t) for i, t in enumerate(pages, 1)]
    text = path.read_text(encoding="utf-8", errors="replace")
    if unit == "page" or (unit == "auto" and "\f" in text):
        return [Unit("page", i, t) for i, t in enumerate(text.split("\f"), 1)]
    return _split_numbered(text)


# --------------------------------------------------------------------- pins

_SYM = r"¶¶?|paras?\.|pp?\.|nn?\.|fns?\.?"
_NUMS = r"\d{1,4}(?:\s*(?:[-–—]|to)\s*\d{1,4})?(?:\s*,\s*\d{1,4}(?:\s*[-–—]\s*\d{1,4})?)*"
PIN_RE = re.compile(rf"(?P<sym>{_SYM})\s*(?P<nums>{_NUMS})", re.I)
_PIN_BARE = rf"(?:{_SYM})\s*(?:{_NUMS})"


def parse_pin(pin: str) -> list[tuple[str, int]]:
    """'¶¶ 42–44, 47' -> [('para',42),('para',43),('para',44),('para',47)]."""
    out: list[tuple[str, int]] = []
    for m in PIN_RE.finditer(pin):
        sym = m.group("sym").lower()
        kind = "para" if sym.startswith(("¶", "para")) else "page" if sym.startswith("p") else "note"
        for part in re.split(r"\s*,\s*", m.group("nums")):
            r = re.split(r"\s*(?:[-–—]|to)\s*", part)
            lo = int(r[0])
            hi = int(r[1]) if len(r) > 1 else lo
            if hi < lo and len(r[1]) < len(r[0]):  # "142–7" style abbreviation
                hi = int(r[0][: len(r[0]) - len(r[1])] + r[1])
            out += [(kind, n) for n in range(lo, min(hi, lo + 400) + 1)]
    return out


# -------------------------------------------------------------------- facts

QUOTE_RE = re.compile(r"[“\"]([^”\"]{8,})[”\"]")
NUM_RE = re.compile(r"(?<![\w.])[$€£]?\d{1,3}(?:,\d{3})+(?:\.\d+)?%?|(?<![\w.])[$€£]?\d+(?:\.\d+)?%?")
SCALE = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    s = re.sub(r"[‐-‒–—―]", "-", s)
    s = s.replace("­", "")
    s = re.sub(r"-\s*\n\s*", "", s)  # hyphenation across lines
    return re.sub(r"\s+", " ", s).strip().lower()


def _num_value(tok: str) -> float | None:
    t = tok.strip("$€£%").replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


def _numbers_in(text: str) -> set[float]:
    vals: set[float] = set()
    for m in NUM_RE.finditer(text):
        v = _num_value(m.group(0))
        if v is None:
            continue
        vals.add(round(v, 6))
        after = text[m.end() : m.end() + 12].lower()
        for word, mult in SCALE.items():
            if after.lstrip().startswith(word):
                vals.add(round(v * mult, 6))
    return vals


def strip_pins(text: str) -> str:
    return re.sub(rf"\(?\s*{_PIN_BARE}(?:\s*[;,]\s*{_PIN_BARE})*\s*\)?", " ", text, flags=re.I)


def extract_facts(text: str) -> tuple[list[str], list[str]]:
    """Numbers and quotations a sentence asserts, with its pin cites removed."""
    body = strip_pins(text)
    quotes = [q.strip() for q in QUOTE_RE.findall(body)]
    unquoted = QUOTE_RE.sub(" ", body)
    numbers = [m.group(0) for m in NUM_RE.finditer(unquoted)]
    return numbers, quotes


# ------------------------------------------------------------------ checking


@dataclass
class Claim:
    pin: str
    text: str = ""
    numbers: list[str] = field(default_factory=list)
    quotes: list[str] = field(default_factory=list)
    where: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> Claim:
        c = cls(pin=str(d["pin"]), text=str(d.get("text", "")), where=str(d.get("where", "")))
        if "numbers" in d or "quotes" in d:
            c.numbers = [str(x) for x in d.get("numbers", [])]
            c.quotes = [str(x) for x in d.get("quotes", [])]
        else:
            c.numbers, c.quotes = extract_facts(c.text)
        return c


@dataclass
class Result:
    claim: Claim
    fact: str
    kind: str  # "number" | "quote" | "pin"
    ok: bool
    detail: str


def _quote_in(quote: str, text: str) -> bool:
    segs = [s for s in re.split(r"\s*(?:…|\.\.\.)\s*", _norm(quote)) if s]
    hay, pos = _norm(text), 0
    for s in segs:
        i = hay.find(s, pos)
        if i < 0:
            return False
        pos = i + len(s)
    return bool(segs)


def _number_in(tok: str, text: str, cache: dict) -> bool:
    v = _num_value(tok)
    if v is None:
        return False
    if id(text) not in cache:
        cache[id(text)] = _numbers_in(text)
    return round(v, 6) in cache[id(text)]


def check_claims(units: list[Unit], claims: list[Claim]) -> list[Result]:
    index = {(u.kind, u.number): u for u in units}
    cache: dict = {}
    results: list[Result] = []
    for c in claims:
        pins = parse_pin(c.pin)
        if not pins:
            results.append(Result(c, c.pin, "pin", False, "could not parse a pin cite"))
            continue
        missing = [f"{k}:{n}" for k, n in pins if (k, n) not in index]
        if missing:
            results.append(
                Result(c, c.pin, "pin", False, f"pin points past the source's units ({', '.join(missing[:4])})")
            )
            continue
        cited = "\n".join(index[p].text for p in pins)
        facts = [("number", n) for n in c.numbers] + [("quote", q) for q in c.quotes]
        for kind, fact in facts:
            ok = _quote_in(fact, cited) if kind == "quote" else _number_in(fact, cited, cache)
            if ok:
                results.append(Result(c, fact, kind, True, "found at the cited pin"))
                continue
            elsewhere = [
                u.label
                for u in units
                if (_quote_in(fact, u.text) if kind == "quote" else _number_in(fact, u.text, cache))
            ]
            detail = (
                f"not at {c.pin}; found at {', '.join(elsewhere[:5])}"
                if elsewhere
                else "not found anywhere in the source"
            )
            results.append(Result(c, fact, kind, False, detail))
    return results


# ---------------------------------------------------------------- scanning


def _sheet_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            return "\n".join(pg.extract_text() or "" for pg in pdf.pages)
    if suffix == ".docx":
        return "\n".join(u.text for u in _docx_all_paragraphs(path))
    text = path.read_text(encoding="utf-8", errors="replace")
    if suffix in (".html", ".htm"):
        text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
        text = re.sub(r"(?i)<\s*(br|/p|/td|/th|/li|/h\d|/div)\s*/?>", "\n", text)
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return text


def _docx_all_paragraphs(path: Path) -> list[Unit]:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    return [Unit("para", i, _docx_text(p)) for i, p in enumerate(root.iter(W + "p"), 1)]


SENT_SPLIT = re.compile(r"(?:(?<=[.!?])|(?<=[.!?][\"”)]))\s+(?=[A-Z“\"(])|\n{2,}")
PIN_END = re.compile(rf"{_PIN_BARE}\)?[.;,]?\s*$", re.I)
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")


def scan_claims(sheet: str | Path) -> list[Claim]:
    """Every sentence or table cell carrying a pin cite becomes a claim."""
    text = _sheet_text(Path(sheet))
    # A table row is one claim: its pin cite usually sits in its own column,
    # apart from the cell that states the fact.
    rows = [ln for ln in text.splitlines() if TABLE_ROW.match(ln)]
    prose = "\n".join("" if TABLE_ROW.match(ln) else ln for ln in text.splitlines())
    prose = re.sub(r"(?<=[a-z,])\n(?=[a-z])", " ", prose)  # rejoin wrapped lines
    chunks = SENT_SPLIT.split(prose) + [" ; ".join(c.strip() for c in r.strip().strip("|").split("|")) for r in rows]
    # Rendered tables (from a PDF) arrive as one line per row with the pin at
    # the end; cut after every line that ends on a pin so rows stay separate.
    split: list[str] = []
    for chunk in chunks:
        group: list[str] = []
        for line in chunk.splitlines():
            group.append(line)
            if PIN_END.search(line):
                split.append(" ".join(group))
                group = []
        if group:
            split.append(" ".join(group))
    chunks = split
    claims = []
    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        pins = [m.group(0) for m in PIN_RE.finditer(chunk)]
        if not pins:
            continue
        numbers, quotes = extract_facts(chunk)
        claims.append(Claim(pin="; ".join(pins), text=chunk, numbers=numbers, quotes=quotes, where=f"segment {i}"))
    return claims


# ---------------------------------------------------------- negative control


def _corrupt_number(tok: str, rng: random.Random) -> str:
    digits = [i for i, ch in enumerate(tok) if ch.isdigit()]
    i = digits[-1] if digits else 0
    new = str((int(tok[i]) + rng.randint(1, 8)) % 10)
    return tok[:i] + new + tok[i + 1 :]


def _corrupt_quote(q: str, rng: random.Random) -> str:
    words = q.split()
    targets = [i for i, w in enumerate(words) if len(re.sub(r"\W", "", w)) >= 4] or list(range(len(words)))
    i = rng.choice(targets)
    words[i] = "never" if words[i].lower() != "never" else "always"
    return " ".join(words)


def negative_control(units: list[Unit], claims: list[Claim], n: int, seed: int = 7) -> tuple[int, int, list[str]]:
    """Corrupt n verified facts in memory; return (caught, tried, notes)."""
    rng = random.Random(seed)
    passing = [r for r in check_claims(units, claims) if r.ok and r.kind in ("number", "quote")]
    if not passing:
        return 0, 0, ["no verified facts to corrupt"]
    picks = rng.sample(passing, min(n, len(passing)))
    caught, notes = 0, []
    for r in picks:
        bad = _corrupt_number(r.fact, rng) if r.kind == "number" else _corrupt_quote(r.fact, rng)
        probe = Claim(
            pin=r.claim.pin, numbers=[bad] if r.kind == "number" else [], quotes=[bad] if r.kind == "quote" else []
        )
        res = check_claims(units, [probe])
        ok_at_pin = any(x.ok for x in res)
        if not ok_at_pin:
            caught += 1
        notes.append(f"{'caught' if not ok_at_pin else 'MISSED'}: {r.kind} {r.fact!r} -> {bad!r} at {r.claim.pin}")
    return caught, len(picks), notes


# ---------------------------------------------------------------------- CLI


def _report(results: list[Result]) -> str:
    fails = [r for r in results if not r.ok]
    lines = []
    for r in fails:
        where = f" [{r.claim.where}]" if r.claim.where else ""
        lines.append(f"FAIL {r.kind:<6} {r.fact!r} @ {r.claim.pin}{where}: {r.detail}")
        if r.claim.text:
            lines.append(f"     in: {r.claim.text[:160]}")
    claims = {id(r.claim) for r in results}
    lines.append(
        f"-- {len(claims)} claim(s), {len(results)} check(s): {len(results) - len(fails)} verified, {len(fails)} failed"
    )
    return "\n".join(lines)


def cmd_units(a) -> int:
    units = load_units(a.source, a.unit)
    by_kind: dict[str, list[Unit]] = {}
    for u in units:
        by_kind.setdefault(u.kind, []).append(u)
    status = 0
    for kind, us in by_kind.items():
        nums = [u.number for u in us]
        gaps = sorted(set(range(min(nums), max(nums) + 1)) - set(nums))
        print(f"{kind}: {len(us)} units, {us[0].label} … {us[-1].label}; gaps: {gaps[:20] or 'none'}")
        if a.show:
            for u in us:
                print(f"  {u.label:>8}  {u.text[:110].replace(chr(10), ' / ')}")
    if a.expect_count is not None:
        paras = len(by_kind.get("para", []))
        ok = paras == a.expect_count
        print(f"expected {a.expect_count} paragraphs, reconstructed {paras}: {'OK' if ok else 'MISMATCH'}")
        status = 0 if ok else 1
    return status


def cmd_check(a) -> int:
    units = load_units(a.source, a.unit)
    if not units:
        print("error: no citable units found in the source", file=sys.stderr)
        return 2
    if a.claims:
        raw = json.loads(Path(a.claims).read_text(encoding="utf-8"))
        claims = [Claim.from_dict(d) for d in raw]
    elif a.scan:
        claims = scan_claims(a.scan)
    else:
        print("error: give --claims or --scan", file=sys.stderr)
        return 2
    results = check_claims(units, claims)
    print(_report(results))
    status = 1 if any(not r.ok for r in results) else 0
    if a.negative_control:
        caught, tried, notes = negative_control(units, claims, a.negative_control, a.seed)
        for n in notes:
            print("  " + n)
        print(f"-- negative control: {caught}/{tried} corruptions caught")
        if tried == 0 or caught < tried:
            status = 3
    if a.json:
        Path(a.json).write_text(
            json.dumps([{**asdict(r), "claim": asdict(r.claim)} for r in results], indent=1, ensure_ascii=False),
            encoding="utf-8",
        )
    return status


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="pincheck", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("units", help="show the source's reconstructed pin units")
    u.add_argument("source")
    u.add_argument("--unit", default="auto", choices=["auto", "para", "page", "note"])
    u.add_argument("--expect-count", type=int)
    u.add_argument("--show", action="store_true", help="print every unit's opening text")
    u.set_defaults(func=cmd_units)
    c = sub.add_parser("check", help="verify pin-cited facts against the source")
    c.add_argument("source")
    c.add_argument("--unit", default="auto", choices=["auto", "para", "page", "note"])
    g = c.add_mutually_exclusive_group()
    g.add_argument("--claims", help="JSON list of {pin, text[, numbers, quotes]}")
    g.add_argument("--scan", help="rendered sheet to scan for pin-cited sentences")
    c.add_argument("--negative-control", type=int, default=0, metavar="N")
    c.add_argument("--seed", type=int, default=7)
    c.add_argument("--json", help="write per-check results here")
    c.set_defaults(func=cmd_check)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
