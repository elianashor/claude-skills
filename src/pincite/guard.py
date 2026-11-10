#!/usr/bin/env python3
"""
Confidentiality guard: fail the build if case material leaks into a public repo.

Skills built on client work are only safe to publish if nothing traceable to the
matter rides along: party and expert names, case numbers, Bates ranges, dated
draft filenames, protective-order legends. This guard checks for two kinds of
leak.

1. A private denylist of terms that must never appear (party names, expert
   names, source titles from the matter). The list itself is confidential, so it
   never lives in the repo: it is read from the PINCITE_DENYLIST environment
   variable (a CI secret) and/or an untracked .denylist file, one term per line.
   Matching ignores case, punctuation and spacing, so "Acme_Corp", "AcmeCorp" and
   "ACME corp." all hit the term "acme corp".

2. Built-in patterns that need no secrets: case numbers, Bates numbers,
   protective-order legends, dated draft filenames, personal home-directory
   paths, and email addresses outside an allowlist.

In CI (or with --mask) every match is printed masked ("a*** c***"), because a
guard that echoes the secret term into a public build log is itself the leak.

Usage
-----
    python -m pincite.guard                    # tracked files in the current repo
    python -m pincite.guard path/ other.md     # specific paths
    python -m pincite.guard --history          # every blob in every commit
Allow a deliberate line with a trailing  pincite-guard: allow  comment.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

__all__ = ["Hit", "load_denylist", "main", "scan_text"]

ALLOW_MARK = "pincite-guard: allow"
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".xlsx", ".docx", ".zip", ".woff", ".woff2", ".ico"}
EMAIL_ALLOW = re.compile(r"(?i)noreply|no-reply|example\.(com|org)|users\.noreply\.github\.com|@anthropic\.com$")

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("CASE-NUMBER", re.compile(r"\b\d{1,2}:\d{2}-(?:cv|cr|md|mc|ap|bk)-\d{3,6}\b", re.I)),
    ("MDL-NUMBER", re.compile(r"\bMDL\s+No\.?\s*\d{3,5}\b", re.I)),
    ("BATES", re.compile(r"\b(?!(?:PMC|PMID|NBER|SSRN|ISBN|ISSN|DOI|CRS|GAO|OIG)\d)[A-Z]{2,8}[-_]?\d{7,10}\b")),
    (
        "PROTECTIVE-ORDER",
        re.compile(
            r"(?i)attorneys['’]? eyes only|highly confidential|subject to (a |the )?protective order|"  # pincite-guard: allow
            r"privileged (and|&) confidential|attorney work product"  # pincite-guard: allow
        ),
    ),
    ("DATED-DRAFT", re.compile(r"[\w ()-]*\d{4}[._-]\d{2}[._-]\d{2}[\w ()-]*\.(?:docx?|pdf|xlsx?)\b", re.I)),
    ("HOME-PATH", re.compile(r"(?:/Users|/home|C:\\Users)[/\\](?!runner\b|claude\b|user\b|you\b)[A-Za-z][\w.-]+")),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
]


@dataclass
class Hit:
    path: str
    line: int
    code: str
    match: str

    def render(self, mask: bool) -> str:
        shown = _mask(self.match) if mask else self.match
        return f"{self.path}:{self.line} | {self.code} | {shown}"


def _mask(s: str) -> str:
    return " ".join(w[:1] + "*" * max(3, len(w) - 1) for w in s.split()) or "***"


def _squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _words(s: str) -> str:
    return " " + re.sub(r"[^a-z0-9]+", " ", s.lower()).strip() + " "


def load_denylist(file: str | Path | None = ".denylist") -> list[str]:
    terms: list[str] = []
    env = os.environ.get("PINCITE_DENYLIST", "")
    terms += re.split(r"[\n,]", env)
    if file and Path(file).is_file():
        terms += Path(file).read_text(encoding="utf-8").splitlines()
    out, seen = [], set()
    for t in terms:
        t = t.split("#", 1)[0].strip()
        if t and _squash(t) not in seen:
            seen.add(_squash(t))
            out.append(t)
    return out


def scan_text(text: str, path: str, denylist: list[str]) -> list[Hit]:
    hits: list[Hit] = []
    dense = [(t, _words(t), _squash(t)) for t in denylist]
    for n, line in enumerate(text.splitlines(), 1):
        if ALLOW_MARK in line:
            continue
        w, sq = _words(line), _squash(line)
        for term, tw, tsq in dense:
            # word-boundary match on normalized words; squashed match catches
            # CamelCase and underscore_joined forms of multi-letter terms
            if tw in w or (len(tsq) >= 5 and tsq in sq):
                hits.append(Hit(path, n, "DENYLIST", term))
        for code, pat in PATTERNS:  # one finding per pattern per line is enough to act on
            m = next((m for m in pat.finditer(line) if not (code == "EMAIL" and EMAIL_ALLOW.search(m.group(0)))), None)
            if m:
                hits.append(Hit(path, n, code, m.group(0).strip()))
    return hits


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def _tracked() -> list[str]:
    return [p for p in _git("ls-files", "-z").split("\0") if p]


def _history_blobs():
    seen = set()
    for commit in _git("rev-list", "--all").split():
        for line in _git("ls-tree", "-r", commit).splitlines():
            meta, path = line.split("\t", 1)
            sha = meta.split()[2]
            if sha in seen or Path(path).suffix.lower() in BINARY_EXT:
                continue
            seen.add(sha)
            data = subprocess.run(["git", "cat-file", "-p", sha], capture_output=True).stdout
            yield f"{path}@{commit[:7]}", data.decode("utf-8", "replace")


def _files(paths: list[str]):
    for p in paths:
        pp = Path(p)
        targets = [pp] if pp.is_file() else [q for q in pp.rglob("*") if q.is_file() and ".git" not in q.parts]
        for q in targets:
            if q.suffix.lower() in BINARY_EXT or q.name == ".denylist":
                continue
            try:
                yield str(q), q.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="files or directories (default: git-tracked files)")
    ap.add_argument("--denylist", default=".denylist", help="untracked file of private terms")
    ap.add_argument("--history", action="store_true", help="scan every blob in every commit")
    ap.add_argument("--mask", action="store_true", help="mask matches in output (automatic in CI)")
    ap.add_argument(
        "--require-denylist",
        action="store_true",
        help="fail if no private terms were loaded (use in CI on the default branch)",
    )
    a = ap.parse_args(argv)
    mask = a.mask or bool(os.environ.get("CI"))
    denylist = load_denylist(a.denylist)

    if a.history:
        sources = _history_blobs()
    elif a.paths:
        sources = _files(a.paths)
    else:
        sources = ((p, t) for p, t in _files(_tracked()))

    hits: list[Hit] = []
    nfiles = 0
    for path, text in sources:
        nfiles += 1
        hits += scan_text(text, path, denylist)
    for h in hits:
        print(h.render(mask))
    note = f"{len(denylist)} private term(s)" if denylist else "no private denylist loaded"
    print(f"-- {len(hits)} potential leak(s) in {nfiles} file(s); {note}")
    if a.require_denylist and not denylist:
        print("error: --require-denylist set but PINCITE_DENYLIST / .denylist is empty", file=sys.stderr)
        return 2
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
